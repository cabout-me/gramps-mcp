#!/usr/bin/env python3
"""
Pre-commit hook to check for emojis in files.
Prevents emojis from being committed to maintain clean, professional code.
"""

import re
import sys
from pathlib import Path


def has_emojis(text: str) -> bool:
    """
    Check if text contains emoji characters.

    Args:
        text: Text content to check

    Returns:
        True if emojis are found, False otherwise
    """
    # Comprehensive emoji pattern covering most Unicode emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U00002702-\U000027b0"  # dingbats
        "\U000024c2-\U0001f251"  # enclosed characters
        "\U0001f900-\U0001f9ff"  # supplemental symbols
        "\U0001fa70-\U0001faff"  # symbols and pictographs extended-A
        "\U00002600-\U000026ff"  # miscellaneous symbols
        "\U00002700-\U000027bf"  # dingbats
        "]+",
        flags=re.UNICODE,
    )
    return bool(emoji_pattern.search(text))


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
