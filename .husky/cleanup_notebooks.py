#!/usr/bin/env python3

import json
import sys
import subprocess


def get_staged_notebooks():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )
    return [file for file in result.stdout.split("\n") if file.endswith(".ipynb")]


def clean_notebook(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    # Clear outputs
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    # Re-stage the file
    subprocess.run(["git", "add", file_path])


def main():
    notebooks = get_staged_notebooks()

    if not notebooks:
        print("No Jupyter notebooks staged for commit. Exiting.")
        sys.exit(0)

    print("Cleaning notebook outputs...")

    for notebook in notebooks:
        print(f"Processing {notebook}")
        clean_notebook(notebook)

    print("Notebook cleaning completed.")


if __name__ == "__main__":
    main()
