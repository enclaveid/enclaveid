#!/usr/bin/env python3

import json
import sys
import subprocess
import os


def read_cleanignore(notebook_path):
    directory = os.path.dirname(notebook_path)
    cleanignore_path = os.path.join(directory, ".cleanignore")
    try:
        with open(cleanignore_path, "r") as f:
            # Read lines and remove whitespace, empty lines, and comments
            return {
                line.strip() for line in f if line.strip() and not line.startswith("#")
            }
    except FileNotFoundError:
        return set()


def get_staged_notebooks():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )
    staged_files = result.stdout.split("\n")
    notebooks = []
    for file in staged_files:
        if file.endswith(".ipynb"):
            ignored_files = read_cleanignore(file)
            if file not in ignored_files:
                notebooks.append(file)
    return notebooks


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
