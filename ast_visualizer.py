import xml.etree.ElementTree as ET


def should_ignore(element):
    """
    Ignore:
    - <results>
    - anything inside <Dummy>
    - directive/meta tags
    """
    ignored_tags = {
        "results",
        "__directives",
        "match-sequence",
        "optional",
        "meta-variable",
        "parameter",
    }

    return element.tag in ignored_tags


def build_tree(element, prefix="", is_last=True, inside_dummy=False):
    """
    Recursively print XML as a visual tree.
    """

    # Ignore everything inside Dummy
    if inside_dummy:
        return

    # Skip ignored tags
    if should_ignore(element):
        for child in element:
            build_tree(child, prefix, True, inside_dummy)
        return

    # Detect Dummy section
    if element.tag == "Dummy":
        return

    connector = "└── " if is_last else "├── "
    print(prefix + connector + element.tag)

    children = [
        child
        for child in element
        if not should_ignore(child) and child.tag != "Dummy"
    ]

    new_prefix = prefix + ("    " if is_last else "│   ")

    for i, child in enumerate(children):
        last = i == len(children) - 1
        build_tree(child, new_prefix, last)


def xml_to_tree(xml_content):
    root = ET.fromstring(xml_content)

    # Find all subtree nodes
    subtrees = root.findall("subtree")

    for idx, subtree in enumerate(subtrees, 1):
        print(f"\nSubtree {idx}")

        children = [
            child
            for child in subtree
            if not should_ignore(child) and child.tag != "Dummy"
        ]

        for i, child in enumerate(children):
            build_tree(child, "", i == len(children) - 1)


# Example usage
xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<SourceFile FullName="js_files/file_7.js" ID="1" Language="JavaScript" LineNr="1">
  <Program ID="2" LineNr="1">
    <LexicalDeclaration ID="3" LineNr="1">
      <VariableDeclarator ID="4" LineNr="1">
        <Identifier ID="5" LineNr="1">MarsDB</Identifier>
        <CallExpression ID="6" LineNr="1">
          <Identifier ID="7" LineNr="1">require</Identifier>
          <Arguments ID="8" LineNr="1">
            <String ID="9" LineNr="1">
              <StringFragment ID="10" LineNr="1">marsdb</StringFragment>
            </String>
          </Arguments>
        </CallExpression>
      </VariableDeclarator>
    </LexicalDeclaration>
    <LexicalDeclaration ID="11" LineNr="3">
      <VariableDeclarator ID="12" LineNr="3">
        <Identifier ID="13" LineNr="3">myDoc</Identifier>
        <NewExpression ID="14" LineNr="3">
          <MemberExpression ID="15" LineNr="3">
            <Identifier ID="16" LineNr="3">MarsDB</Identifier>
            <PropertyIdentifier ID="17" LineNr="3">Collection</PropertyIdentifier>
          </MemberExpression>
          <Arguments ID="18" LineNr="3">
            <String ID="19" LineNr="3">
              <StringFragment ID="20" LineNr="3">myDoc</StringFragment>
            </String>
          </Arguments>
        </NewExpression>
      </VariableDeclarator>
    </LexicalDeclaration>
    <LexicalDeclaration ID="21" LineNr="5">
      <VariableDeclarator ID="22" LineNr="5">
        <Identifier ID="23" LineNr="5">db</Identifier>
        <Object ID="24" LineNr="5">
          <ShorthandPropertyIdentifier ID="25" LineNr="6">myDoc</ShorthandPropertyIdentifier>
        </Object>
      </VariableDeclarator>
    </LexicalDeclaration>
    <ExpressionStatement ID="26" LineNr="9">
      <AssignmentExpression ID="27" LineNr="9">
        <MemberExpression ID="28" LineNr="9">
          <Identifier ID="29" LineNr="9">module</Identifier>
          <PropertyIdentifier ID="30" LineNr="9">exports</PropertyIdentifier>
        </MemberExpression>
        <Identifier ID="31" LineNr="9">db</Identifier>
      </AssignmentExpression>
    </ExpressionStatement>
  </Program>
</SourceFile>
"""

xml_to_tree(xml_data)