#!/usr/bin/env python3
""" Helper functions for installing this multifile add-on in Blender """
import argparse
import os
import shutil
from pathlib import Path
from zipfile import ZipFile


def build(output_path: str = ""):
    """
    Pack add-on into a zip file suitable for a Blender install

    Returns:
        addon_name, zip_path: Name of the addon, path to the zip file
    """
    # It is assumed that this script is located in the same folder as the add-on
    addon_name = (Path(__file__).resolve()).parent.name
    source_path = (Path(__file__).resolve()).parent

    if output_path.strip() == "":
        # Remove previous build output
        build_path = source_path.joinpath("build")
        if build_path.is_dir():
            shutil.rmtree(build_path, ignore_errors=True)
        os.makedirs(build_path)

    # This is to get relative paths when creating the zip, makes it easier
    os.chdir(source_path)

    # Find relevant files
    all_but_hidden_files = [path for path in Path("").rglob('*.*') if not str(path).startswith('.')]

    # Write to zip
    zip_path = build_path.joinpath(f'{addon_name}.zip')
    print(f"Writing output to '{zip_path}'")
    with ZipFile(zip_path, 'w') as zip_file:
        for path in all_but_hidden_files:
            zip_file.write(filename=path, arcname=Path(addon_name).joinpath(path))

    print("\nDone")

    return addon_name, zip_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pack addon into a zip file")
    parser.add_argument('--output-path', '-p', type=str, default="", required=False, help="Output path of zip."
                        " Output will be in a subfolder of this script if this argument is not provided.")
    args = parser.parse_args()

    addon_name, zip_path = build(args.output_path)
