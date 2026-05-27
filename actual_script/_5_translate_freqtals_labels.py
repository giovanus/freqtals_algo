from pathlib import Path

CONFIG_FILES = [
    Path("conf/javascript/listRootLabel.txt"),
    Path("conf/javascript/listWhiteLabel.txt"),
]


def to_pascal_case(label):
    return "".join(part.capitalize() for part in label.split("_") if part)


def translate_line(line):
    stripped = line.strip()

    if not stripped or stripped.startswith("#"):
        return line

    line_without_newline = line.rstrip("\n")
    newline = "\n" if line.endswith("\n") else ""
    tokens = line_without_newline.split()
    translated_tokens = [to_pascal_case(token) for token in tokens]

    return " ".join(translated_tokens) + newline


for config_file in CONFIG_FILES:
    content = config_file.read_text(encoding="utf8").splitlines(keepends=True)
    translated = [translate_line(line) for line in content]
    config_file.write_text("".join(translated), encoding="utf8")
    print(f"Translated labels in {config_file}")
