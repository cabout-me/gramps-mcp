#!/usr/bin/env python3
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
        if category == 'So' and ('EMOJI' in name or 'FACE' in name or 'HAND' in name):
            return True
            
        # Check for common emoji ranges by code point
        code_point = ord(char)
        if (0x1F600 <= code_point <= 0x1F64F or  # Emoticons
            0x1F300 <= code_point <= 0x1F5FF or  # Misc symbols and pictographs
            0x1F680 <= code_point <= 0x1F6FF or  # Transport and map symbols
            0x1F1E0 <= code_point <= 0x1F1FF or  # Flags
            0x2600 <= code_point <= 0x26FF or   # Misc symbols
            0x2700 <= code_point <= 0x27BF or   # Dingbats
            0x1F900 <= code_point <= 0x1F9FF or  # Supplemental symbols
            0x1FA70 <= code_point <= 0x1FAFF):   # Extended pictographs
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
