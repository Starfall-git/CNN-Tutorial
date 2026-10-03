"""Execute the tutorial in real Jupyter kernels, saving outputs only on success.

Usage: python scripts/execute_notebooks.py [00_environment.ipynb ...]
Running chapter 02 starts a full new training run; it does not overwrite old runs.
"""
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
names = sys.argv[1:] or [p.name for p in sorted((root / "notebooks").glob("*.ipynb"))]
for name in names:
    path = (root / "notebooks" / name).resolve()
    if path.parent != (root / "notebooks").resolve() or path.suffix != ".ipynb":
        raise ValueError("Choose a notebook directly inside notebooks/")
    notebook = nbformat.read(path, as_version=4)
    print(f"Executing {name}", flush=True)
    client = NotebookClient(notebook, timeout=1800, kernel_name="CNN-Tutorial",
                            resources={"metadata": {"path": str(root)}})
    client.execute()
    nbformat.write(notebook, path)
    print(f"PASS {name}", flush=True)
