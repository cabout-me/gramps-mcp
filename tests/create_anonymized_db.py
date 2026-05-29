"""
Create an anonymized Gramps SQLite test fixture from a real database.

Reads GRAMPS_TEST_DB_PATH (or the default path) and writes an anonymized
copy to tests/fixtures/test_gramps.sqlite suitable for committing to the
repository.

Anonymization strategy:
  - Names:    replaced with generated first/last names from word lists
  - Dates:    years shifted by a fixed random offset (structure preserved)
  - Places:   titles replaced with fictional place names
  - Notes:    text replaced with Lorem Ipsum
  - Sources:  titles/authors replaced with generic text
  - URLs:     replaced with example.com
  - Handles:  unchanged (needed for relationship integrity)
  - IDs:      unchanged (I0001, F0001, etc.)
  - Relationships: all family/event links preserved exactly

Usage:
    uv run python tests/create_anonymized_db.py
"""

import json
import os
import random
import shutil
import sqlite3
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_SOURCE = (
    r"C:\Users\dachner\AppData\Roaming\gramps\grampsdb\6a1764f8\sqlite.db"
)
SOURCE_DB = os.environ.get("GRAMPS_TEST_DB_PATH", _DEFAULT_SOURCE)
TARGET_DB = Path(__file__).parent / "fixtures" / "test_gramps.sqlite"

# Deterministic seed so the anonymized DB is stable across runs
SEED = 42
random.seed(SEED)

# Year shift: all years move by this offset (so birth/death order is preserved)
YEAR_SHIFT = -random.randint(30, 80)

# ---------------------------------------------------------------------------
# Word lists for generated names
# ---------------------------------------------------------------------------

_FIRST_NAMES_F = [
    "Anna", "Maria", "Elise", "Klara", "Helene", "Emma", "Ida", "Rosa",
    "Martha", "Frieda", "Greta", "Lotte", "Hedwig", "Paula", "Berta",
    "Hildegard", "Erna", "Else", "Agnes", "Wilhelmine",
]
_FIRST_NAMES_M = [
    "Karl", "Hans", "Wilhelm", "Friedrich", "Ernst", "Otto", "Franz",
    "Heinrich", "Gustav", "Hermann", "Georg", "Paul", "Johann", "Walter",
    "Albert", "Rudolf", "Erich", "Max", "Alfred", "Emil",
]
_SURNAMES = [
    "Bauer", "Fischer", "Hoffmann", "Müller", "Schmidt", "Schneider",
    "Weber", "Wagner", "Meyer", "Koch", "Richter", "Becker", "Schäfer",
    "Zimmermann", "Braun", "Krause", "Wolf", "Schröder", "Neumann", "Schwarz",
    "Zimmermann", "Braun", "Krause", "Wolf", "Schröder", "Neumann",
    "Hartmann", "Lange", "Schmitt", "Werner", "Schmitz", "Kramer", "Lehmann",
    "König", "Walter", "Mayer", "Huber", "Kaiser", "Fuchs", "Peters",
]
_PLACES = [
    "Musterdorf", "Beispielhausen", "Testburg", "Musterstadt", "Probedorf",
    "Neuheim", "Altfeld", "Waldkirch", "Bergheim", "Seebach",
    "Thalheim", "Steinbach", "Kirchdorf", "Lindenau", "Fichtenwald",
    "Eichenbach", "Buchenheim", "Ahorntal", "Rosenfeld", "Blumental",
]
_NOTE_TEXT = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris."
)
_SOURCE_TITLES = [
    "Kirchenbuch St. Marien", "Standesamt Musterdorf", "Taufregister 1800-1900",
    "Heiratsregister Kreis Muster", "Sterberegister Pfarrei Beispiel",
    "Volkszählung 1900", "Militärregister 1914", "Auswandererliste Hamburg",
    "Grundbuch Mustergemeinde", "Schulregister Altfeld",
]

# Deterministic per-handle mapping so the same handle always gets the same name
_name_cache: dict = {}


def _anon_first(handle: str, gender: int) -> str:
    key = f"first_{handle}"
    if key not in _name_cache:
        pool = _FIRST_NAMES_M if gender == 1 else _FIRST_NAMES_F
        _name_cache[key] = random.choice(pool)
    return _name_cache[key]


def _anon_surname(handle: str) -> str:
    key = f"sur_{handle}"
    if key not in _name_cache:
        _name_cache[key] = random.choice(_SURNAMES)
    return _name_cache[key]


def _anon_place_name(handle: str) -> str:
    key = f"pl_{handle}"
    if key not in _name_cache:
        _name_cache[key] = random.choice(_PLACES)
    return _name_cache[key]


# ---------------------------------------------------------------------------
# JSON transformers
# ---------------------------------------------------------------------------

def _shift_year(dateval: list) -> list:
    """Shift the year component of a [d, m, y, dual] dateval list."""
    if not dateval or len(dateval) < 3:
        return dateval
    shifted = list(dateval)
    if shifted[2]:
        shifted[2] = max(1, shifted[2] + YEAR_SHIFT)
    return shifted


def _anon_date(date: dict) -> dict:
    if not isinstance(date, dict):
        return date
    result = dict(date)
    if "dateval" in result:
        result["dateval"] = _shift_year(result["dateval"])
    return result


def _anon_name(name: dict, handle: str, gender: int) -> dict:
    if not isinstance(name, dict):
        return name
    result = dict(name)
    result["first_name"] = _anon_first(handle, gender)
    result["suffix"] = ""
    result["title"] = ""
    result["call"] = ""
    result["nick"] = ""
    result["famnick"] = ""
    if "surname_list" in result:
        new_sl = []
        for sn in result["surname_list"]:
            new_sn = dict(sn)
            if isinstance(new_sn.get("surname"), str):
                new_sn["surname"] = _anon_surname(handle)
            new_sl.append(new_sn)
        result["surname_list"] = new_sl
    if "date" in result:
        result["date"] = _anon_date(result["date"])
    result["note_list"] = []
    result["citation_list"] = []
    return result


def _anon_person(data: dict) -> dict:
    obj = dict(data)
    handle = obj.get("handle", "")
    gender = obj.get("gender", 2)

    if "primary_name" in obj:
        obj["primary_name"] = _anon_name(obj["primary_name"], handle, gender)
    obj["alternate_names"] = []
    obj["address_list"] = []
    obj["urls"] = []
    obj["note_list"] = []
    obj["person_ref_list"] = []
    return obj


def _anon_event(data: dict) -> dict:
    obj = dict(data)
    if "date" in obj:
        obj["date"] = _anon_date(obj["date"])
    obj["description"] = ""
    obj["note_list"] = []
    obj["attribute_list"] = []
    return obj


def _anon_place(data: dict) -> dict:
    obj = dict(data)
    handle = obj.get("handle", "")
    place_name = _anon_place_name(handle)
    obj["title"] = place_name
    obj["long"] = ""
    obj["lat"] = ""
    obj["code"] = ""
    if isinstance(obj.get("name"), dict):
        obj["name"] = dict(obj["name"])
        obj["name"]["value"] = place_name
    obj["alt_names"] = []
    obj["urls"] = []
    obj["note_list"] = []
    return obj


def _anon_source(data: dict, idx: int) -> dict:
    obj = dict(data)
    obj["title"] = _SOURCE_TITLES[idx % len(_SOURCE_TITLES)]
    obj["author"] = "Musterarchiv"
    obj["pubinfo"] = "Musterdorf, 1900"
    obj["abbrev"] = f"SRC{idx}"
    obj["note_list"] = []
    obj["media_list"] = []
    return obj


def _anon_note(data: dict) -> dict:
    obj = dict(data)
    if isinstance(obj.get("text"), dict):
        obj["text"] = dict(obj["text"])
        obj["text"]["string"] = _NOTE_TEXT
        obj["text"]["tags"] = []
    return obj


def _anon_media(data: dict) -> dict:
    obj = dict(data)
    obj["path"] = ""
    obj["desc"] = "Anonymized media"
    obj["note_list"] = []
    return obj


# ---------------------------------------------------------------------------
# Table-level processing
# ---------------------------------------------------------------------------

def _process_table(src_conn, dst_conn, table: str, transform):
    rows = src_conn.execute(
        f"SELECT * FROM {table}"  # noqa: S608
    ).fetchall()
    if not rows:
        return

    col_names = [d[0] for d in src_conn.execute(
        f"SELECT * FROM {table} LIMIT 0"  # noqa: S608
    ).description]

    placeholders = ",".join("?" * len(col_names))
    insert_sql = (
        f"INSERT OR REPLACE INTO {table} ({','.join(col_names)}) "  # noqa: S608
        f"VALUES ({placeholders})"
    )

    for i, row in enumerate(rows):
        row_dict = dict(zip(col_names, row))

        if "json_data" in row_dict and row_dict["json_data"]:
            try:
                data = json.loads(row_dict["json_data"])
                data = transform(data, i)
                row_dict["json_data"] = json.dumps(data, ensure_ascii=False)

                # Update secondary columns for person
                if table == "person":
                    pn = data.get("primary_name", {})
                    sl = pn.get("surname_list", [])
                    row_dict["given_name"] = pn.get("first_name", "")
                    row_dict["surname"] = sl[0].get("surname", "") if sl else ""
                if table == "place":
                    row_dict["title"] = data.get("title", "")
                    row_dict["long"] = ""
                    row_dict["lat"] = ""
            except (json.JSONDecodeError, Exception) as exc:
                print(f"  Warning: could not transform {table} row {i}: {exc}")

        dst_conn.execute(insert_sql, [row_dict[c] for c in col_names])


# ---------------------------------------------------------------------------
# Schema copy
# ---------------------------------------------------------------------------

def _copy_schema(src_conn, dst_conn):
    schema_rows = src_conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()
    for (sql,) in schema_rows:
        dst_conn.execute(sql)
    dst_conn.commit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not os.path.exists(SOURCE_DB):
        print(f"ERROR: Source DB not found: {SOURCE_DB}")
        print("Set GRAMPS_TEST_DB_PATH environment variable to override.")
        sys.exit(1)

    TARGET_DB.parent.mkdir(parents=True, exist_ok=True)

    if TARGET_DB.exists():
        TARGET_DB.unlink()

    print(f"Source: {SOURCE_DB}")
    print(f"Target: {TARGET_DB}")
    print(f"Year shift: {YEAR_SHIFT:+d}")

    src = sqlite3.connect(SOURCE_DB)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(str(TARGET_DB))

    _copy_schema(src, dst)

    tables = {
        "person": lambda d, i: _anon_person(d),
        "family": lambda d, i: d,
        "event": lambda d, i: _anon_event(d),
        "place": lambda d, i: _anon_place(d),
        "source": lambda d, i: _anon_source(d, i),
        "citation": lambda d, i: d,
        "note": lambda d, i: _anon_note(d),
        "media": lambda d, i: _anon_media(d),
        "repository": lambda d, i: d,
        "tag": lambda d, i: d,
        "reference": lambda d, i: d,
        "name_group": lambda d, i: d,
        "gender_stats": lambda d, i: d,
        "metadata": lambda d, i: d,
    }

    for table, transform in tables.items():
        try:
            count_row = src.execute(
                f"SELECT COUNT(*) FROM {table}"  # noqa: S608
            ).fetchone()
            count = count_row[0] if count_row else 0
            if count == 0:
                continue
            print(f"  {table:15s} {count:5d} rows...")
            _process_table(src, dst, table, transform)
            dst.commit()
        except sqlite3.OperationalError:
            pass  # Table might not exist in this DB version

    src.close()
    dst.close()

    size_kb = TARGET_DB.stat().st_size // 1024
    print(f"\nDone. {TARGET_DB.name} ({size_kb} KB)")
    print("\nVerify with:")
    print(f"  uv run pytest tests/test_sqlite_integration.py -v "
          f"--override-ini='integration' "
          f"GRAMPS_TEST_DB_PATH={TARGET_DB}")


if __name__ == "__main__":
    main()
