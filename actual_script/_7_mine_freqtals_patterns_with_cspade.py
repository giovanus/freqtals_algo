#!/usr/bin/env python3
"""
Convert FreqTALS frequent XML patterns to cSPADE sequences, then mine them.

Input:
    js_output_2/js_ast_xml_1_patterns.xml

Generated cSPADE input:
    freqt_to_sequence_input/sequences.cspade.txt
    freqt_to_sequence_input/mapping.json
    freqt_to_sequence_input/subtree_metadata.json

Generated mining output:
    freqt_to_sequence_output/spade_output.txt
"""

from __future__ import annotations

import argparse
import json
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


DEFAULT_PATTERNS_XML = Path("js_output_2/js_ast_xml_1_patterns.xml")
DEFAULT_INPUT_DIR = Path("freqt_to_sequence_input")
DEFAULT_OUTPUT_DIR = Path("freqt_to_sequence_output")
DEFAULT_SUPPORT = 0.1

IGNORED_TAGS = {
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


def item_id(label: str, mapping: dict[str, int]) -> int:
    if label not in mapping:
        mapping[label] = len(mapping) + 1
    return mapping[label]


def add_tree_levels(
    element: ET.Element,
    mapping: dict[str, int],
    levels: dict[int, list[int]],
    depth: int = 0,
) -> None:
    if is_ignored(element):
        for child in visible_children(element):
            add_tree_levels(child, mapping, levels, depth)
        return

    levels[depth].append(item_id(f"tag={element.tag}", mapping))

    for child in visible_children(element):
        add_tree_levels(child, mapping, levels, depth + 1)

def removeprefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text

def convert_freqtals_patterns(
    patterns_xml: Path,
) -> tuple[list[tuple[int, int, list[int]]], dict[str, int], list[dict[str, int]]]:
    tree = ET.parse(patterns_xml)
    root = tree.getroot()
    mapping: dict[str, int] = {}
    rows: list[tuple[int, int, list[int]]] = []
    metadata: list[dict[str, int]] = []

    for index, subtree in enumerate(root.findall("subtree"), start=1):
        sequence_id = int(subtree.get("id", index))
        levels: dict[int, list[int]] = defaultdict(list)

        for child in visible_children(subtree):
            add_tree_levels(child, mapping, levels)

        for event_id, depth in enumerate(sorted(levels), start=1):
            rows.append((sequence_id, event_id, levels[depth]))

        metadata.append(
            {
                "sequence_id": sequence_id,
                "freqtals_support": int(subtree.get("support", 0)),
                "freqtals_wsupport": int(subtree.get("wsupport", 0)),
                "freqtals_size": int(subtree.get("size", 0)),
                "sequence_length": len(levels),
            }
        )

    return rows, mapping, metadata


def write_cspade_sequences(rows: list[tuple[int, int, list[int]]], output_file: Path) -> None:
    with output_file.open("w", encoding="utf-8") as file:
        for sequence_id, event_id, items in rows:
            item_text = " ".join(str(item) for item in items)
            file.write(f"{sequence_id} {event_id} {len(items)} {item_text}\n")


def write_mapping(mapping: dict[str, int], output_file: Path) -> None:
    reverse_mapping = {str(value): key for key, value in mapping.items()}
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(reverse_mapping, file, indent=2, sort_keys=True)
        file.write("\n")


def write_metadata(metadata: list[dict[str, int]], output_file: Path) -> None:
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
        file.write("\n")


def load_mapping(mapping_file: Path) -> dict[str, str]:
    with mapping_file.open("r", encoding="utf-8") as file:
        return json.load(file)


def decode_item(item: str, mapping: dict[str, str]) -> str:
    return removeprefix(mapping.get(item, f"unknown={item}"),"tag=")


def decode_pattern(pattern: str, mapping: dict[str, str]) -> str:
    events = []
    for raw_event in pattern.split("->"):
        item_ids = raw_event.strip().split()
        labels = [decode_item(item_id, mapping) for item_id in item_ids]
        events.append("{" + ", ".join(labels) + "}")
    return " -> ".join(events)


def parse_seqstrm(seqstrm: str, mapping: dict[str, str]) -> list[dict[str, object]]:
    patterns: list[dict[str, object]] = []

    for line_number, line in enumerate(seqstrm.splitlines(), start=1):
        line = line.strip()
        if not line or "--" not in line:
            continue

        raw_pattern, raw_support = line.split("--", maxsplit=1)
        support_parts = raw_support.strip().split()
        support = int(support_parts[0]) if support_parts else 0

        patterns.append(
            {
                "index": len(patterns) + 1,
                "source_line": line_number,
                "support": support,
                "raw": raw_pattern.strip(),
                "decoded": decode_pattern(raw_pattern.strip(), mapping),
            }
        )

    return patterns


def write_mining_output(
    result: dict[str, object],
    mined_patterns: list[dict[str, object]],
    support: float,
    execution_time: float,
    input_file: Path,
    output_file: Path,
) -> None:
    nsequences = int(result.get("nsequences", 0))

    with output_file.open("w", encoding="utf-8") as file:
        file.write("cSPADE mining over FreqTALS frequent patterns\n")
        file.write("============================================\n\n")
        file.write(f"Input file: {input_file}\n")
        file.write(f"Minimum support: {support:.2%}\n")
        file.write(f"Number of FreqTALS pattern sequences: {nsequences}\n")
        file.write(f"Number of cSPADE frequent sequential patterns: {len(mined_patterns)}\n")
        file.write(f"Execution time: {execution_time:.2f} seconds\n\n")

        for pattern in mined_patterns:
            pattern_support = int(pattern["support"])
            support_ratio = pattern_support / nsequences if nsequences else 0.0
            file.write(f"Pattern #{pattern['index']}\n")
            file.write(f"Support: {pattern_support}/{nsequences} ({support_ratio:.2%})\n")
            file.write(f"Raw: {pattern['raw']}\n")
            file.write(f"Decoded: {pattern['decoded']}\n\n")


def generate_cspade_input(patterns_xml: Path, input_dir: Path) -> tuple[Path, Path, Path]:
    input_dir.mkdir(parents=True, exist_ok=True)
    sequences_file = input_dir / "sequences.cspade.txt"
    mapping_file = input_dir / "mapping.json"
    metadata_file = input_dir / "subtree_metadata.json"

    rows, mapping, metadata = convert_freqtals_patterns(patterns_xml)
    write_cspade_sequences(rows, sequences_file)
    write_mapping(mapping, mapping_file)
    write_metadata(metadata, metadata_file)

    print(f"Wrote {len(rows)} events from {len(metadata)} FreqTALS patterns to {sequences_file}")
    print(f"Wrote {len(mapping)} item mappings to {mapping_file}")
    print(f"Wrote subtree metadata to {metadata_file}")

    return sequences_file, mapping_file, metadata_file


def mine_sequences(
    sequences_file: Path,
    mapping_file: Path,
    output_dir: Path,
    support: float,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "spade_output.txt"

    try:
        from pycspade.helpers import spade
    except ModuleNotFoundError as error:
        if error.name != "pycspade":
            raise
        with output_file.open("w", encoding="utf-8") as file:
            file.write("cSPADE mining over FreqTALS frequent patterns\n")
            file.write("============================================\n\n")
            file.write(f"Input file: {sequences_file}\n")
            file.write(f"Mapping file: {mapping_file}\n")
            file.write(f"Minimum support: {support:.2%}\n\n")
            file.write("Mining was not executed because pycspade is not installed ")
            file.write("in the current Python environment.\n")
            file.write("Install it with:\n\n")
            file.write("    pip install Cython pycspade\n")
        print(f"pycspade is not installed; wrote diagnostic output to {output_file}")
        return output_file

    start = time.time()
    result = spade(filename=str(sequences_file), support=support)
    execution_time = time.time() - start

    mapping = load_mapping(mapping_file)
    mined_patterns = parse_seqstrm(str(result.get("seqstrm", "")), mapping)
    write_mining_output(result, mined_patterns, support, execution_time, sequences_file, output_file)

    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Wrote {len(mined_patterns)} mined patterns to {output_file}")
    return output_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert FreqTALS XML patterns to cSPADE input and mine them."
    )
    parser.add_argument(
        "--patterns-xml",
        type=Path,
        default=DEFAULT_PATTERNS_XML,
        help=f"FreqTALS *_patterns.xml file. Default: {DEFAULT_PATTERNS_XML}",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Directory for generated cSPADE input. Default: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for cSPADE mining output. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--support",
        type=float,
        default=DEFAULT_SUPPORT,
        help=f"Minimum support ratio for cSPADE. Default: {DEFAULT_SUPPORT}",
    )
    parser.add_argument(
        "--no-mine",
        action="store_true",
        help="Only generate cSPADE input files; skip pycspade mining.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    sequences_file, mapping_file, _ = generate_cspade_input(args.patterns_xml, args.input_dir)

    if args.no_mine:
        print("Skipped cSPADE mining because --no-mine was provided")
        return

    mine_sequences(sequences_file, mapping_file, args.output_dir, args.support)


if __name__ == "__main__":
    main()
