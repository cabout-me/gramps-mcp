#!/usr/bin/env python3
# gramps-mcp - AI-Powered Genealogy Research & Management
# Copyright (C) 2025 cabout.me
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
Pre-commit hook to check that Python files don't exceed 500 lines.

This enforces the project's code modularity standards by preventing
files from becoming too large and encouraging proper separation of concerns.
"""

import sys
from pathlib import Path


def check_file_length(file_path: Path, max_lines: int = 500) -> bool:
    """
    Check if a file exceeds the maximum line count.

    Args:
        file_path: Path to the file to check.
        max_lines: Maximum allowed lines (default 500).

    Returns:
        bool: True if file is within limits, False otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            line_count = len(lines)

        if line_count > max_lines:
            print(f"ERROR: {file_path} has {line_count} lines (max: {max_lines})")
            print("Consider refactoring into smaller modules.")
            return False

        return True
    except Exception as e:
        print(f"ERROR: Could not read {file_path}: {e}")
        return False


def main():
    """
    Main function to check all provided files.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    if len(sys.argv) < 2:
        print("Usage: python check_file_length.py <file1> [file2] ...")
        return 1

    all_passed = True

    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)

        # Skip non-Python files (shouldn't happen with pre-commit config)
        if not file_path.suffix == ".py":
            continue

        if not check_file_length(file_path):
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
