import os
from xml.sax.saxutils import escape
from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjs

JS_DIR = "js_files"
AST_DIR = "js_ast_xml"

os.makedirs(AST_DIR, exist_ok=True)

# Initialisation du langage
JS_LANGUAGE = Language(tsjs.language())
parser = Parser(JS_LANGUAGE)

def sanitize_xml_tag(label):
    """
    Convertit un label Tree-sitter en balise XML compatible FREQTALS.
    FREQTALS ignore les racines qui ne commencent pas par une majuscule,
    donc on transforme les labels comme call_expression en CallExpression.
    """
    pascal_label = "".join(part.capitalize() for part in label.split("_") if part)
    sanitized = "".join(char if char.isalnum() or char in "._-" else "_" for char in pascal_label)
    if not sanitized or not (sanitized[0].isalpha() or sanitized[0] == "_"):
        sanitized = f"_{sanitized}"
    return sanitized


def line_number(node):
    """
    Tree-sitter utilise des lignes indexées à partir de 0.
    FREQTALS attend un attribut LineNr quand il veut retrouver les matches.
    """
    return node.start_point[0] + 1


def next_id(counter):
    current = counter["value"]
    counter["value"] += 1
    return current


def node_to_xml(node, source_code_bytes, id_counter, indent=1):
    """
    Convertit un noeud Tree-sitter en XML compatible avec FREQTALS.
    On garde uniquement les named_children pour éviter la ponctuation pure
    comme ;, (, ), {, }.
    """
    tag = sanitize_xml_tag(node.type)
    spaces = "  " * indent
    line = line_number(node)
    node_id = next_id(id_counter)

    if not node.named_children:
        text = source_code_bytes[node.start_byte:node.end_byte].decode("utf8", errors="ignore").strip()
        if not text:
            return f'{spaces}<{tag} ID="{node_id}" LineNr="{line}"/>'
        return f'{spaces}<{tag} ID="{node_id}" LineNr="{line}">{escape(text)}</{tag}>'

    children_xml = [node_to_xml(child, source_code_bytes, id_counter, indent + 1) for child in node.named_children]
    return "\n".join([
        f'{spaces}<{tag} ID="{node_id}" LineNr="{line}">',
        *children_xml,
        f"{spaces}</{tag}>"
    ])


def tree_to_freqtals_xml(root, source_path, source_code_bytes):
    id_counter = {"value": 1}
    source_file_id = next_id(id_counter)

    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<SourceFile FullName="{escape(source_path)}" ID="{source_file_id}" Language="JavaScript" LineNr="1">',
        node_to_xml(root, source_code_bytes, id_counter, indent=1),
        "</SourceFile>",
        ""
    ])

count = 0

for file in os.listdir(JS_DIR):
    if not file.endswith(".js"):
        continue

    js_path = os.path.join(JS_DIR, file)
    ast_path = os.path.join(AST_DIR, file.replace(".js", ".xml"))

    try:
        with open(js_path, "r", encoding="utf8") as f:
            code_str = f.read()

        # Tree-sitter travaille de manière optimale avec des bytes
        code_bytes = bytes(code_str, "utf8")
        tree = parser.parse(code_bytes)
        root = tree.root_node

        ast_xml = tree_to_freqtals_xml(root, js_path, code_bytes)

        with open(ast_path, "w", encoding="utf8") as f:
            f.write(ast_xml)

        count += 1

    except Exception as e:
        print(f"Error parsing {file}: {e}")

print(f"XML AST generated: {count}")
