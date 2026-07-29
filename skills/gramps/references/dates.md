# Gramps date structure

Dates are objects, not strings. The OpenAPI spec names the fields but not the
integer codes, because they come from Gramps core rather than the web API.
Values below are from
[`gramps/gen/lib/date.py`](https://github.com/gramps-project/gramps/blob/master/gramps/gen/lib/date.py).

## Fields

| Field | Meaning |
|---|---|
| `dateval` | `[day, month, year, slash]`, `0` for unknown parts, `slash` is a boolean for dual dating (1731/32). Ranges and spans use eight entries: start then end. |
| `modifier` | How to read the value -- exact, before, after, about, range, span. |
| `quality` | Confidence. |
| `calendar` | Which calendar the value is expressed in. |
| `text` | Free-text form. The only thing that carries meaning when `modifier` is 6. |
| `sortval` | Server-computed sort key. Do not set it by hand. |
| `year` | Server-computed convenience field. Do not set it by hand. |

## modifier

| Code | Meaning |
|---|---|
| 0 | exact date |
| 1 | before |
| 2 | after |
| 3 | about (circa) |
| 4 | range -- between two dates |
| 5 | span -- from one date to another |
| 6 | text only, `dateval` ignored |
| 7 | from |
| 8 | to |

## quality

| Code | Meaning |
|---|---|
| 0 | normal |
| 1 | estimated |
| 2 | calculated |

## calendar

| Code | Calendar |
|---|---|
| 0 | Gregorian |
| 1 | Julian |
| 2 | Hebrew |
| 3 | French Republican |
| 4 | Persian |
| 5 | Islamic |
| 6 | Swedish |

## Examples

15 June 1878:

```json
{"dateval": [15, 6, 1878, false], "modifier": 0, "quality": 0, "calendar": 0}
```

Around 1850, only the year known:

```json
{"dateval": [0, 0, 1850, false], "modifier": 3, "quality": 0, "calendar": 0}
```

Estimated 1850, derived from other records:

```json
{"dateval": [0, 0, 1850, false], "modifier": 0, "quality": 1, "calendar": 0}
```

Between 1875 and 1880:

```json
{"dateval": [0, 0, 1875, false, 0, 0, 1880, false], "modifier": 4, "quality": 0, "calendar": 0}
```

Unparseable, keep the original wording:

```json
{"dateval": [0, 0, 0, false], "modifier": 6, "quality": 0, "text": "the winter after the flood"}
```

## Note

Day and month come before year in `dateval`, which is the opposite of how the
date reads. Getting this backwards silently produces a date in year 15.
