---
name: codebase-visualizer
description: >
  Generates an interactive, collapsible HTML tree visualisation of a codebase.
  Use when exploring a new repository, understanding project structure, or
  identifying large files and hotspots. Opens the result in the default browser.
allowed-tools: Bash(python *)
---

# Codebase Visualizer

Generates a self-contained `codebase-map.html` file with an interactive tree
view of the project, including file sizes, type colour-coding, and collapsible
directories.

## Usage

Run the bundled script from the project root:

```bash
python registry/shared/codebase-visualizer/scripts/visualize.py .
```

The script creates `codebase-map.html` in the current directory and opens it
in the default browser. No external packages required — uses only the Python
standard library.

## What the visualisation shows

- **Collapsible directories** — click to expand or collapse
- **File sizes** — displayed next to each file and as directory totals
- **Type colour-coding** — different colours for `.py`, `.ts`, `.yml`, etc.
- **Summary sidebar** — file count, directory count, total size, top file types
  with a proportional bar chart

## Ignored paths

`.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `dist`, `build`
