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
Pre-commit hook to check for emojis in files.
Prevents emojis from being committed to maintain clean, professional code.
"""

import sys
import unicodedata
from pathlib import Path


def has_emojis(text: str) -> bool:
    """
    Check if text contains emoji characters using Unicode categories.

    Args:
        text: Text content to check

    Returns:
        True if emojis are found, False otherwise
    """
    for char in text:
        # Check for emoji using Unicode categories and properties
        category = unicodedata.category(char)
        name = unicodedata.name(char, "")

        # Emoji symbols are typically in category 'So' (Other symbols)
        # or have 'EMOJI' in their Unicode name
        if category == "So" and ("EMOJI" in name or "FACE" in name or "HAND" in name):
            return True

        # Check for common emoji ranges by code point
        code_point = ord(char)
        if (
            0x1F600 <= code_point <= 0x1F64F  # Emoticons
            or 0x1F300 <= code_point <= 0x1F5FF  # Misc symbols and pictographs
            or 0x1F680 <= code_point <= 0x1F6FF  # Transport and map symbols
            or 0x1F1E0 <= code_point <= 0x1F1FF  # Flags
            or 0x2600 <= code_point <= 0x26FF  # Misc symbols
            or 0x2700 <= code_point <= 0x27BF  # Dingbats
            or 0x1F900 <= code_point <= 0x1F9FF  # Supplemental symbols
            or 0x1FA70 <= code_point <= 0x1FAFF
        ):  # Extended pictographs
            return True

    return False


def check_file_for_emojis(file_path: Path) -> tuple[bool, list[tuple[int, str]]]:
    """
    Check a single file for emoji characters.

    Args:
        file_path: Path to file to check

    Returns:
        Tuple of (has_emojis, list of (line_number, line_content) with emojis)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, PermissionError):
        # Skip binary files or files we can't read
        return False, []

    emoji_lines = []
    for line_num, line in enumerate(lines, 1):
        if has_emojis(line):
            emoji_lines.append((line_num, line.rstrip()))

    return bool(emoji_lines), emoji_lines


def main() -> int:
    """
    Main function to check all provided files for emojis.

    Returns:
        0 if no emojis found, 1 if emojis found
    """
    if len(sys.argv) < 2:
        print("Usage: check_no_emojis.py <file1> [file2] ...")
        return 1

    files_with_emojis = []

    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)

        if not file_path.exists():
            continue

        if file_path.is_file():
            has_emoji, emoji_lines = check_file_for_emojis(file_path)
            if has_emoji:
                files_with_emojis.append((file_path, emoji_lines))

    if files_with_emojis:
        print("ERROR: Emojis found in the following files:")
        print("Emojis are not allowed to maintain clean, professional code.")
        print()

        for file_path, emoji_lines in files_with_emojis:
            print(f"File: {file_path}")
            for line_num, line_content in emoji_lines:
                print(f"  Line {line_num}: {line_content}")
            print()

        print("Please remove all emojis from the above files before committing.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
