"""Validate notebook format and the tutorial's prose-before-code convention."""
from pathlib import Path
import nbformat

for path in (Path(__file__).resolve().parents[1] / "notebooks").rglob("*.ipynb"):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            if index == 0 or notebook.cells[index - 1].cell_type != "markdown":
                raise AssertionError(f"Missing explanation: {path}, cell {index}")
            if any(output.output_type == "error" for output in cell.outputs):
                raise AssertionError(f"Execution error stored in {path}, cell {index}")
    print(f"OK {path.name}")
