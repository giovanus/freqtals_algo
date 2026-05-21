# JavaScript AST Converter

This tool converts JavaScript source files into XML AST files that FREQTALS can mine.

## Install

```bash
cd tools/javascript-ast
npm install
```

## Convert A Directory

```bash
npm run convert -- ../../sample-data/JavaScript/sample_input_js ../../sample-data/JavaScript/sample_input_xml
```

The first argument is a `.js` file or a directory containing `.js`, `.jsx`, `.mjs`, `.cjs`, `.ts`, or `.tsx` files.
The second argument is the output directory for generated `.xml` files.

## Mine The Generated XML

From the repository root:

```bash
java -jar freqtals.jar conf/javascript/config.properties 2 sample_input_xml
```

Tune the mining shape in `conf/javascript/listRootLabel.txt` and `conf/javascript/listWhiteLabel.txt`.
