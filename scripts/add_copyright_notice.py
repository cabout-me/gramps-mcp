#!/usr/bin/env python3
"""
Add copyright and license notices to Python source files.

This script ensures all Python files have the appropriate copyright
and license header as required by the GNU Affero General Public License v3.
"""

import argparse
import datetime
import sys
from pathlib import Path
from typing import List

# Copyright notice template (as comments, not docstring)
COPYRIGHT_TEMPLATE = """# gramps-mcp - AI-Powered Genealogy Research & Management
# Copyright (C) {year} cabout.me
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""


def has_copyright_notice(content: str) -> bool:
    """
    Check if file already has a copyright notice.

    Args:
        content: File content to check.

    Returns:
        bool: True if copyright notice exists.
    """
    # Check for various indicators of existing copyright (in comments)
    indicators = [
        "# Copyright (C)",
        "# gramps-mcp - AI-Powered Genealogy Research",
    ]
    return any(indicator in content for indicator in indicators)


def add_copyright_to_file(filepath: Path, check_only: bool = False) -> bool:
    """
    Add copyright notice to a Python file if missing.

    Args:
        filepath: Path to the Python file.
        check_only: If True, only check without modifying.

    Returns:
        bool: True if file was modified or needs modification.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Skip if already has copyright
        if has_copyright_notice(content):
            return False

        if check_only:
            return True

        # Add copyright notice at the beginning
        year = datetime.datetime.now().year
        copyright_notice = COPYRIGHT_TEMPLATE.format(year=year)

        # Handle shebang line if present
        if content.startswith("#!"):
            # Find the end of the shebang line
            shebang_end = content.find("\n") + 1
            shebang = content[:shebang_end]
            rest = content[shebang_end:]
            new_content = shebang + copyright_notice + rest
        else:
            new_content = copyright_notice + content

        # Write the modified content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return False


def find_python_files(paths: List[str], exclude_dirs: List[str]) -> List[Path]:
    """
    Find all Python files in given paths.

    Args:
        paths: List of file or directory paths.
        exclude_dirs: List of directory names to exclude.

    Returns:
        List[Path]: List of Python file paths.
    """
    python_files = []

    for path_str in paths:
        path = Path(path_str)

        if path.is_file() and path.suffix == ".py":
            python_files.append(path)
        elif path.is_dir():
            for py_file in path.rglob("*.py"):
                # Check if file is in excluded directory
                if not any(
                    exclude_dir in py_file.parts for exclude_dir in exclude_dirs
                ):
                    python_files.append(py_file)

    return python_files


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Add copyright notices to Python files"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["src", "scripts"],
        help="Files or directories to process (default: src scripts)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check only, don't modify files",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=["__pycache__", "venv", ".venv", "tests", "examples"],
        help="Directories to exclude",
    )

    args = parser.parse_args()

    # Find all Python files
    python_files = find_python_files(args.paths, args.exclude)

    if not python_files:
        print("No Python files found to process")
        return 0

    # Process files
    modified_count = 0
    for filepath in python_files:
        if add_copyright_to_file(filepath, check_only=args.check):
            if args.check:
                print(f"Missing copyright: {filepath}")
            else:
                print(f"Added copyright: {filepath}")
            modified_count += 1

    # Summary
    if args.check:
        if modified_count > 0:
            print(f"\n{modified_count} file(s) missing copyright notices")
            return 1
        else:
            print("All files have copyright notices")
            return 0
    else:
        if modified_count > 0:
            print(f"\nAdded copyright to {modified_count} file(s)")
        else:
            print("No files needed copyright notices")
        return 0


if __name__ == "__main__":
    sys.exit(main())
