# JavaScript Sample Data

This folder is organized so JavaScript mining stays separate from the Java and Python examples.

## Layout

- `sample_input_js/`: editable JavaScript source examples.
- `sample_input_xml/`: XML AST files consumed by FREQTALS.
- `output/`: FREQTALS output files.

FREQTALS does not parse `.js` files directly. Convert JavaScript source to XML AST first, then mine the XML directory.

## Quick Test

From the repository root:

```bash
java -jar freqtals.jar conf/javascript/config.properties 2 sample_input_xml
```

Expected outputs are written to `sample-data/JavaScript/output/`, for example:

```text
sample_input_xml_2_patterns.xml
sample_input_xml_2_matches.xml
sample_input_xml_2_patterns.xml_report.txt
```

## Convert JavaScript To XML

The converter lives in `tools/javascript-ast/`.

```bash
cd tools/javascript-ast
npm install
npm run convert -- ../../sample-data/JavaScript/sample_input_js ../../sample-data/JavaScript/sample_input_xml
```

Then run FREQTALS again from the repository root.
