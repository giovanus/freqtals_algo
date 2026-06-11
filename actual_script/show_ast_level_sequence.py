#!/usr/bin/env python3
"""
Display an XML AST as a sequence of itemsets grouped by tree level.

Example:
    python actual_script/show_ast_level_sequence.py js_ast_xml/file_2.xml
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


IGNORED_TAGS = {
    "__directives",
    "match-sequence",
    "optional",
    "meta-variable",
    "parameter",
    "Dummy",
}


def visible_children(element: ET.Element) -> list[ET.Element]:
    return [child for child in list(element) if child.tag not in IGNORED_TAGS]


def add_levels(element: ET.Element, levels: dict[int, list[str]], depth: int = 0) -> None:
    if element.tag in IGNORED_TAGS:
        for child in visible_children(element):
            add_levels(child, levels, depth)
        return

    levels[depth].append(element.tag)

    for child in visible_children(element):
        add_levels(child, levels, depth + 1)


def ast_level_sequence(xml_path: Path) -> str:
    root = ET.parse(xml_path).getroot()
    levels: dict[int, list[str]] = defaultdict(list)
    add_levels(root, levels)

    itemsets = []
    for depth in sorted(levels):
        itemsets.append("{" + " ".join(levels[depth]) + "}")

    return " -> ".join(itemsets)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print an XML AST as a sequence of itemsets grouped by level."
    )
    parser.add_argument("xml_path", type=Path, help="XML AST file to display")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(ast_level_sequence(args.xml_path))


if __name__ == "__main__":
    main()
