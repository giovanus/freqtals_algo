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
    Convertit un label Tree-sitter en nom de balise XML valide.
    Les noeuds nommés de Tree-sitter JS sont généralement déjà propres
    (function_declaration, call_expression, etc.), mais cette garde évite
    de casser le XML si un label inattendu apparaît.
    """
    sanitized = "".join(char if char.isalnum() or char in "._-" else "_" for char in label)
    if not sanitized or not (sanitized[0].isalpha() or sanitized[0] == "_"):
        sanitized = f"_{sanitized}"
    return sanitized


def line_number(node):
    """
    Tree-sitter utilise des lignes indexées à partir de 0.
    FREQTALS attend un attribut LineNr quand il veut retrouver les matches.
    """
    return node.start_point[0] + 1


def node_to_xml(node, indent=1):
    """
    Convertit un noeud Tree-sitter en XML compatible avec FREQTALS.
    On garde uniquement les named_children pour éviter la ponctuation pure
    comme ;, (, ), {, }.
    """
    tag = sanitize_xml_tag(node.type)
    spaces = "  " * indent
    line = line_number(node)

    if not node.named_children:
        return f'{spaces}<{tag} LineNr="{line}"/>'

    children_xml = [node_to_xml(child, indent + 1) for child in node.named_children]
    return "\n".join([
        f'{spaces}<{tag} LineNr="{line}">',
        *children_xml,
        f"{spaces}</{tag}>"
    ])


def tree_to_freqtals_xml(root, source_path):
    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<SourceFile FullName="{escape(source_path)}" Language="JavaScript" LineNr="1">',
        node_to_xml(root, indent=1),
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

        ast_xml = tree_to_freqtals_xml(root, js_path)

        with open(ast_path, "w", encoding="utf8") as f:
            f.write(ast_xml)

        count += 1

    except Exception as e:
        print(f"Error parsing {file}: {e}")

print(f"XML AST generated: {count}")
