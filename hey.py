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
<results>
  <subtree id="1" support="20" wsupport="46" size="11">
    <ExpressionStatement>
      <__directives>
        <match-sequence/>
      </__directives>
      <CallExpression>
        <__directives>
          <match-sequence/>
        </__directives>
        <MemberExpression>
          <__directives>
            <match-sequence/>
          </__directives>
          <Identifier>
            <Dummy>
              <__directives>
                <optional/>
                <meta-variable>
                  <parameter key="name" value="?Identifier"/>
                </meta-variable>
              </__directives>
            </Dummy>
          </Identifier>
          <PropertyIdentifier>
            <Dummy>
              <__directives>
                <optional/>
                <meta-variable>
                  <parameter key="name" value="?PropertyIdentifier"/>
                </meta-variable>
              </__directives>
            </Dummy>
          </PropertyIdentifier>
        </MemberExpression>
        <Arguments>
          <String>
            <StringFragment>
              <Dummy>
                <__directives>
                  <optional/>
                  <meta-variable>
                    <parameter key="name" value="?StringFragment"/>
                  </meta-variable>
                </__directives>
              </Dummy>
            </StringFragment>
          </String>
        </Arguments>
      </CallExpression>
    </ExpressionStatement>
  </subtree>
  <subtree id="2" support="23" wsupport="43" size="9">
    <LexicalDeclaration>
      <__directives>
        <match-sequence/>
      </__directives>
      <VariableDeclarator>
        <__directives>
          <match-sequence/>
        </__directives>
        <Identifier>
          <Dummy>
            <__directives>
              <optional/>
              <meta-variable>
                <parameter key="name" value="?Identifier"/>
              </meta-variable>
            </__directives>
          </Dummy>
        </Identifier>
        <CallExpression>
          <__directives>
            <match-sequence/>
          </__directives>
          <Arguments>
            <String>
              <StringFragment>
                <Dummy>
                  <__directives>
                    <optional/>
                    <meta-variable>
                      <parameter key="name" value="?StringFragment"/>
                    </meta-variable>
                  </__directives>
                </Dummy>
              </StringFragment>
            </String>
          </Arguments>
        </CallExpression>
      </VariableDeclarator>
    </LexicalDeclaration>
  </subtree>
</results>
"""

xml_to_tree(xml_data)