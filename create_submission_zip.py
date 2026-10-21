"""Packaging script to create the clean submission ZIP.

Creates 'team_name_voiceops.zip' matching the exact submission structure from the Capstone Brief:
team_name_voiceops.zip
|-- README.md
|-- .env.example
|-- requirements.txt
|-- run.py
|-- src/
|-- report.pdf
`-- sample_outputs/

Excludes virtual environments, .git, .env secrets, and duplicate datasets.
"""

import os
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
ZIP_NAME = os.path.join(_HERE, "team_name_voiceops.zip")

FILES_TO_INCLUDE = [
    "README.md",
    ".env.example",
    "requirements.txt",
    "run.py",
    "evaluate.py",
    "report.pdf",
    "report_template.md"
]

FOLDERS_TO_INCLUDE = [
    "src",
    "sample_outputs"
]

def make_zip():
    print(f"Creating submission package: {ZIP_NAME}...")
    with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add root files
        for fname in FILES_TO_INCLUDE:
            fpath = os.path.join(_HERE, fname)
            if os.path.exists(fpath):
                zipf.write(fpath, arcname=fname)
                print(f"  + Added file: {fname}")

        # Add folders recursively
        for folder in FOLDERS_TO_INCLUDE:
            dir_path = os.path.join(_HERE, folder)
            if os.path.exists(dir_path):
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith((".pyc", ".pyo")) or "__pycache__" in root:
                            continue
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, _HERE)
                        zipf.write(full_p, arcname=rel_p)
                        print(f"  + Added folder item: {rel_p}")

    print(f"\n[Success] Created clean submission ZIP at: {ZIP_NAME}")

if __name__ == "__main__":
    make_zip()
