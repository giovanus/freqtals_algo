#!/usr/bin/env python3
"""
XML Tree Visualizer

Usage:
    python xml_tree_visualizer.py input.xml output.html

Example:
    python xml_tree_visualizer.py results.xml tree.html
"""

import sys
import html
import xml.etree.ElementTree as ET
from pathlib import Path


def format_attributes(element: ET.Element) -> str:
    """
    Format XML attributes as HTML.
    Example:
        id="1" support="29"
    """
    if not element.attrib:
        return ""

    attrs = []
    for key, value in element.attrib.items():
        attrs.append(
            f'<span class="attr">{html.escape(key)}</span>='
            f'<span class="value">"{html.escape(value)}"</span>'
        )

    return " " + " ".join(attrs)


def xml_to_html_tree(element: ET.Element) -> str:
    """
    Recursively convert an XML element into nested HTML.
    """
    tag = html.escape(element.tag)
    attrs = format_attributes(element)

    children = list(element)

    text = (element.text or "").strip()

    # Leaf node
    if not children:
        text_html = ""
        if text:
            text_html = f'<span class="text"> {html.escape(text)}</span>'

        return f"""
        <li>
          <div class="node leaf">
            <span class="tag">&lt;{tag}</span>{attrs}<span class="tag">&gt;</span>{text_html}
          </div>
        </li>
        """

    # Non-leaf node
    children_html = "\n".join(xml_to_html_tree(child) for child in children)

    return f"""
    <li>
      <div class="node expandable">
        <span class="toggle">▾</span>
        <span class="tag">&lt;{tag}</span>{attrs}<span class="tag">&gt;</span>
      </div>
      <ul>
        {children_html}
      </ul>
    </li>
    """


def generate_html(root: ET.Element, source_name: str) -> str:
    """
    Generate the final HTML document.
    """
    tree_html = xml_to_html_tree(root)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>XML Tree Visualization</title>

  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f7f8fa;
      color: #222;
      margin: 0;
      padding: 2rem;
    }}

    h1 {{
      margin-bottom: 0.25rem;
      font-size: 1.7rem;
    }}

    .subtitle {{
      color: #666;
      margin-bottom: 1.5rem;
    }}

    .container {{
      background: white;
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
      overflow-x: auto;
    }}

    ul {{
      list-style-type: none;
      margin-left: 1.2rem;
      padding-left: 1rem;
      border-left: 1px solid #ddd;
    }}

    li {{
      margin: 0.35rem 0;
      position: relative;
    }}

    .node {{
      display: inline-block;
      padding: 0.35rem 0.6rem;
      border-radius: 8px;
      background: #f1f5f9;
      border: 1px solid #d8e0ea;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 0.9rem;
      cursor: default;
      white-space: nowrap;
    }}

    .node.expandable {{
      cursor: pointer;
      background: #eef6ff;
      border-color: #b8d8f8;
    }}

    .node.expandable:hover {{
      background: #dfefff;
    }}

    .node.leaf {{
      background: #f8fafc;
    }}

    .toggle {{
      display: inline-block;
      width: 1rem;
      color: #2563eb;
      font-weight: bold;
    }}

    .tag {{
      color: #1d4ed8;
      font-weight: 600;
    }}

    .attr {{
      color: #9333ea;
    }}

    .value {{
      color: #15803d;
    }}

    .text {{
      color: #b45309;
    }}

    .collapsed > ul {{
      display: none;
    }}

    .collapsed > .node .toggle {{
      transform: rotate(-90deg);
    }}

    .toolbar {{
      margin-bottom: 1rem;
    }}

    button {{
      border: none;
      background: #2563eb;
      color: white;
      padding: 0.45rem 0.8rem;
      border-radius: 8px;
      cursor: pointer;
      margin-right: 0.5rem;
      font-size: 0.9rem;
    }}

    button:hover {{
      background: #1d4ed8;
    }}
  </style>
</head>

<body>
  <h1>XML Tree Visualization</h1>
  <div class="subtitle">Source file: <strong>{html.escape(source_name)}</strong></div>

  <div class="toolbar">
    <button onclick="expandAll()">Expand all</button>
    <button onclick="collapseAll()">Collapse all</button>
  </div>

  <div class="container">
    <ul class="tree">
      {tree_html}
    </ul>
  </div>

  <script>
    document.querySelectorAll(".node.expandable").forEach(node => {{
      node.addEventListener("click", event => {{
        const li = node.parentElement;
        li.classList.toggle("collapsed");

        const toggle = node.querySelector(".toggle");
        if (li.classList.contains("collapsed")) {{
          toggle.textContent = "▸";
        }} else {{
          toggle.textContent = "▾";
        }}

        event.stopPropagation();
      }});
    }});

    function expandAll() {{
      document.querySelectorAll("li.collapsed").forEach(li => {{
        li.classList.remove("collapsed");
        const toggle = li.querySelector(".toggle");
        if (toggle) toggle.textContent = "▾";
      }});
    }}

    function collapseAll() {{
      document.querySelectorAll(".tree li").forEach(li => {{
        if (li.querySelector("ul")) {{
          li.classList.add("collapsed");
          const toggle = li.querySelector(".toggle");
          if (toggle) toggle.textContent = "▸";
        }}
      }});
    }}
  </script>
</body>
</html>
"""


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python xml_tree_visualizer.py input.xml output.html")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)

    try:
        tree = ET.parse(input_path)
        root = tree.getroot()
    except ET.ParseError as error:
        print(f"Error: invalid XML file: {error}")
        sys.exit(1)

    html_content = generate_html(root, input_path.name)

    output_path.write_text(html_content, encoding="utf-8")

    print(f"HTML tree visualization generated: {output_path}")


if __name__ == "__main__":
    main()