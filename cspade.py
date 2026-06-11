from __future__ import annotations

import json
import time
from pathlib import Path


INPUT_FILE = Path("js_spade_input/sequences.cspade.txt")
MAPPING_FILE = Path("js_spade_input/mapping.json")
OUTPUT_DIR = Path("js_spade_output")
OUTPUT_FILE = OUTPUT_DIR / "spade_output.txt"
MIN_SUPPORT = 0.5

def remove_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text
def load_mapping(mapping_file: Path) -> dict[str, str]:
    with mapping_file.open("r", encoding="utf-8") as file:
        return json.load(file)


def decode_item(item: str, mapping: dict[str, str]) -> str:
    label = mapping.get(item, f"unknown={item}")
    return remove_prefix(label, "tag=")


def decode_pattern(pattern: str, mapping: dict[str, str]) -> str:
    events = []
    for raw_event in pattern.split("->"):
        item_ids = raw_event.strip().split()
        event_labels = [decode_item(item_id, mapping) for item_id in item_ids]
        events.append("{" + ", ".join(event_labels) + "}")
    return " -> ".join(events)


def parse_seqstrm(seqstrm: str, mapping: dict[str, str]) -> list[dict[str, object]]:
    patterns = []

    for line_number, line in enumerate(seqstrm.splitlines(), start=1):
        line = line.strip()
        if not line or "--" not in line:
            continue

        raw_pattern, raw_support = line.split("--", maxsplit=1)
        support_parts = raw_support.strip().split()
        support = int(support_parts[0]) if support_parts else 0
        support_sequences = int(support_parts[1]) if len(support_parts) > 1 else support

        patterns.append(
            {
                "index": len(patterns) + 1,
                "line": line_number,
                "raw": raw_pattern.strip(),
                "decoded": decode_pattern(raw_pattern.strip(), mapping),
                "support": support,
                "support_sequences": support_sequences,
            }
        )

    return patterns


def write_output(
    result: dict[str, object],
    patterns: list[dict[str, object]],
    execution_time: float,
    output_file: Path,
) -> None:
    nsequences = int(result.get("nsequences", 0))

    with output_file.open("w", encoding="utf-8") as file:
        file.write("cSPADE frequent sequential patterns\n")
        file.write("===================================\n\n")
        file.write(f"Input file: {INPUT_FILE}\n")
        file.write(f"Minimum support: {MIN_SUPPORT:.2%}\n")
        file.write(f"Number of input sequences: {nsequences}\n")
        file.write(f"Number of frequent patterns: {len(patterns)}\n")
        file.write(f"Execution time: {execution_time:.2f} seconds\n\n")

        for pattern in patterns:
            support = int(pattern["support"])
            support_ratio = support / nsequences if nsequences else 0.0

            file.write(f"Pattern #{pattern['index']}\n")
            file.write(f"Support: {support}/{nsequences} ({support_ratio:.2%})\n")
            file.write(f"Raw: {pattern['raw']}\n")
            file.write(f"Decoded: {pattern['decoded']}\n")
            file.write("\n")


def main() -> None:
    from pycspade.helpers import spade

    start = time.time()
    result = spade(
        filename=str(INPUT_FILE),
        support=MIN_SUPPORT,
    )
    execution_time = time.time() - start

    OUTPUT_DIR.mkdir(exist_ok=True)
    mapping = load_mapping(MAPPING_FILE)
    patterns = parse_seqstrm(str(result.get("seqstrm", "")), mapping)
    write_output(result, patterns, execution_time, OUTPUT_FILE)

    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Wrote {len(patterns)} patterns to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
