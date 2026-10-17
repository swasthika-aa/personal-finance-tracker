"""Execute the source notebook in a fresh kernel and export a static HTML report."""

from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "outputs"
    output.mkdir(exist_ok=True)
    notebook = nbformat.read(root / "notebooks" / "finance_demo.ipynb", as_version=4)
    nbformat.validate(notebook)
    client = NotebookClient(notebook, timeout=180, kernel_name="python3",
                            resources={"metadata": {"path": str(root)}})
    client.execute()
    nbformat.write(notebook, output / "finance_demo.executed.ipynb")
    html, _ = HTMLExporter().from_notebook_node(notebook)
    (output / "finance_demo.html").write_text(html, encoding="utf-8")
    errors = [item for cell in notebook.cells if cell.cell_type == "code"
              for item in cell.get("outputs", []) if item.output_type == "error"]
    if errors:
        raise RuntimeError(errors)
    code_cells = sum(cell.cell_type == "code" for cell in notebook.cells)
    print(f"Executed {code_cells} code cells without errors. Report: {output / 'finance_demo.html'}")


if __name__ == "__main__":
    main()