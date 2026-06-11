#!/usr/bin/env python3
"""
Convert AST/FreqTALS XML trees to the sequence/itemset format expected by pycspade.

Each XML tree becomes one sequence. Each tree level becomes one event/itemset.
Items inside a level are written in their left-to-right XML order. Items are
integer-encoded node labels, because cSPADE works with numeric item identifiers.
example:
    python _6_freqtals_patterns_to_cspade.py --input-path patterns.xml --output-dir js_spade_input
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


IGNORED_TAGS = {
    "results",
    "subtree",
    "__directives",
    "match-sequence",
    "optional",
    "meta-variable",
    "parameter",
    "Dummy",
}


def is_ignored(element: ET.Element) -> bool:
    return element.tag in IGNORED_TAGS


def visible_children(element: ET.Element) -> list[ET.Element]:
    return [child for child in list(element) if not is_ignored(child)]


def feature_id(feature: str, mapping: dict[str, int], allow_new_items: bool) -> int:
    if feature not in mapping:
        if not allow_new_items:
            raise ValueError(
                f"Unknown feature {feature!r}. The global mapping already exists, "
                "so it will not be regenerated. Delete the mapping file if you want "
                "to rebuild it for a changed corpus."
            )
        mapping[feature] = len(mapping) + 1
    return mapping[feature]


def add_levels(
    element: ET.Element,
    mapping: dict[str, int],
    allow_new_items: bool,
    depth: int = 0,
    levels: dict[int, list[int]] | None = None,
) -> dict[int, list[int]]:
    """
    Group one XML tree by depth.

    The recursion visits children in document order, so the list stored for each
    level preserves the left-to-right order of nodes at that depth.
    """
    if levels is None:
        levels = defaultdict(list)

    if is_ignored(element):
        for child in visible_children(element):
            add_levels(child, mapping, allow_new_items, depth, levels)
        return levels

    levels[depth].append(feature_id(f"tag={element.tag}", mapping, allow_new_items))

    for child in visible_children(element):
        add_levels(child, mapping, allow_new_items, depth + 1, levels)

    return levels


def sequence_id_from_path(xml_path: Path, fallback: int) -> int:
    match = re.fullmatch(r"file_(\d+)\.xml", xml_path.name)
    if match:
        return int(match.group(1))
    return fallback


def xml_inputs(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(
            input_path.glob("*.xml"),
            key=lambda path: (sequence_id_from_path(path, 10**12), path.name),
        )
    return [input_path]


def roots_to_convert(root: ET.Element, default_sequence_id: int) -> list[tuple[int, ET.Element]]:
    """
    FreqTALS pattern files contain several <subtree> elements.
    A normal AST XML file contains one source tree rooted at the document root.
    """
    subtrees = root.findall("subtree")
    if subtrees:
        return [
            (int(subtree.get("id", index)), subtree)
            for index, subtree in enumerate(subtrees, start=1)
        ]

    return [(default_sequence_id, root)]


def convert_trees_by_level(
    input_path: Path,
    mapping: dict[str, int],
    allow_new_items: bool,
) -> list[tuple[int, int, list[int]]]:
    rows: list[tuple[int, int, list[int]]] = []

    for fallback_sequence_id, xml_path in enumerate(xml_inputs(input_path)):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        default_sequence_id = sequence_id_from_path(xml_path, fallback_sequence_id)

        for sequence_id, tree_root in roots_to_convert(root, default_sequence_id):
            levels = add_levels(tree_root, mapping, allow_new_items)
            for event_id, depth in enumerate(sorted(levels), start=1):
                items = levels[depth]
                rows.append((sequence_id, event_id, items))

    return rows


def write_cspade_file(rows: list[tuple[int, int, list[int]]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as output:
        for sequence_id, event_id, items in rows:
            item_text = " ".join(str(item) for item in items)
            output.write(f"{sequence_id} {event_id} {len(items)} {item_text}\n")


def write_mapping(mapping: dict[str, int], mapping_path: Path) -> None:
    reverse_mapping = {str(item_id): feature for feature, item_id in mapping.items()}
    with mapping_path.open("w", encoding="utf-8") as output:
        json.dump(reverse_mapping, output, indent=2, sort_keys=True)
        output.write("\n")


def load_mapping(mapping_path: Path) -> dict[str, int]:
    with mapping_path.open("r", encoding="utf-8") as mapping_file:
        reverse_mapping = json.load(mapping_file)

    mapping: dict[str, int] = {}
    for item_id, feature in reverse_mapping.items():
        mapping[str(feature)] = int(item_id)
    return mapping


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert AST/FreqTALS XML trees to pycspade sequence/itemset rows."
    )
    parser.add_argument("input_path", type=Path, help="AST XML file or directory of AST XML files")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("js_spade_input"),
        help="Directory for generated cSPADE input files. Default: js_spade_input",
    )
    parser.add_argument(
        "--sequences-name",
        default="sequences.cspade.txt",
        help="Generated cSPADE sequence filename. Default: sequences.cspade.txt",
    )
    parser.add_argument(
        "--mapping-name",
        default="mapping.json",
        help="Global mapping filename. Default: mapping.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    output_path = args.output_dir / args.sequences_name
    mapping_path = args.output_dir / args.mapping_name

    if mapping_path.exists():
        mapping = load_mapping(mapping_path)
        allow_new_items = False
        print(f"Using existing global mapping from {mapping_path}")
    else:
        mapping = {}
        allow_new_items = True

    rows = convert_trees_by_level(args.input_path, mapping, allow_new_items)
    write_cspade_file(rows, output_path)
    if allow_new_items:
        write_mapping(mapping, mapping_path)

    sequence_count = len({sequence_id for sequence_id, _, _ in rows})
    print(f"Wrote {len(rows)} events from {sequence_count} sequences to {output_path}")
    if allow_new_items:
        print(f"Wrote {len(mapping)} item mappings to {mapping_path}")
    else:
        print(f"Kept existing {len(mapping)} item mappings")


if __name__ == "__main__":
    main()
