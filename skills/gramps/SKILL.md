---
name: gramps
description: Read and write a family tree hosted on Gramps Web. Use when the user asks to look up, add, correct, or source people, families, events, places, sources, citations, notes or media in their genealogy database, or to research their own tree.
---

# Gramps Web

## Setup

Three environment variables, or a `.env` file at the repo root:

```
GRAMPS_API_URL=https://your-instance.example.com
GRAMPS_USERNAME=you
GRAMPS_PASSWORD=...
```

## Read the spec first

Every instance publishes its OpenAPI spec at `/api/openapi.json`,
unauthenticated and generated from the running code. It covers 183 operations
with every parameter and what each one does. **Read it before experimenting**:
it gives the rule, a probe gives one case.

```bash
SPEC=$(scripts/spec.py --file)          # downloads, caches, prints the path

jq -r '.paths | keys[]' $SPEC                                    # operations
jq -r '.paths | keys[] | select(contains("citation"))' $SPEC     # filtered
jq -r '.paths."/api/people/{handle}" | keys[]' $SPEC             # methods allowed
jq -r '.paths."/api/people/".get.parameters[]
       | "\(.name): \(.description)"' $SPEC                      # what a param does
```

Object shapes need `scripts/spec.py`, since Gramps schemas are mutually
recursive and jq loops on them:

```bash
scripts/spec.py Person                 # fields, one line each
scripts/spec.py Person.primary_name    # drill into a field
scripts/spec.py Event.date --full      # raw JSON for a fragment
```

Request bodies for POST and PUT live in the schemas rather than the operations:
use `spec.py Person`, or `GET` an existing record and mirror it. Valid type
strings live in the database: `scripts/api.py GET types/`.

## Calling the API

```bash
scripts/api.py GET  people/ -p page=1 -p pagesize=10
scripts/api.py GET  people/{handle} -p profile=self,events -p keys=profile
scripts/api.py POST notes/ -b '{"text": {"string": "..."}, "type": "Transcript"}'
scripts/api.py PUT  people/{handle} -b @person.json
scripts/api.py POST media/ -f scan.pdf
```

`-p` repeats for query parameters. `-b` takes a JSON string, `@file`, or `@-`
for stdin. `-f` sends a file's bytes. `X-Total-Count` goes to stderr.

**Check for an `error` key before using a response.** Success returns an array;
failure returns an object naming the field, and both have a length:

```
{"error": {"code": 422, "message": "query: keys: Unknown field."}}
```

## Keeping responses small

**Always send `page` together with `pagesize`.** The spec is explicit: *"page:
If omitted, all results are returned"*, and pagesize applies only *"when
pagination is active"*.

```
-p pagesize=5 -p page=1    -> 5 records
-p page=1                  -> 20 records (default page size)
-p pagesize=5              -> the entire collection
```

**Let the API trim.** It resolves handles into names, ISO dates and full place
names server-side:

```bash
scripts/api.py GET people/{handle} -p profile=self,events -p keys=profile
```

Name the sections you need -- `self`, `events`, `families`, `age`, `span`,
`ratings`, `references`, `participants`. `profile=all` recursively embeds
relatives' full profiles: 41.6 KB on a person with 14 events, against 4.4 KB for
`self,events` with the same readable content.

`keys=handle,gramps_id` whitelists fields, `skipkeys=` drops them, `extend=`
inlines referenced objects at a cost -- reach for `profile` first.

## Searching

**`gql=` filters on structure.** Use it when you know the field. A query is
`field operator value` tests joined by `and` / `or`, with parentheses where
needed. Operators: `=`, `!=`, `~` (contains), `!~`, `>`, `<`.

Reaching into a list takes `any` or `all` at the point of indexing; following a
handle to another object takes a `get_*` step:

```bash
scripts/api.py GET people/ -p 'gql=primary_name.surname_list.any.surname ~ Dobrzy' \
                           -p page=1 -p pagesize=10
scripts/api.py GET events/ -p 'gql=place.get_place.name.value ~ Vrasene' \
                           -p page=1 -p pagesize=10
```

Quote values containing spaces or punctuation; the parser stops at the first odd
character and returns a 422 naming the column.

Property names differ from the field names in a response, and a wrong path
errors rather than degrading. The full list is at
<https://www.grampsweb.org/user-guide/gql/>.

**`GET search/ -p query=...` matches text anywhere**, notes included. Use it
when you know a phrase. Results are wrapped as
`{"object_type": "person", "object": {...}}`.

`notes/` answers every `gql` query with a 500, through 3.19.0. Reach a note by
searching its text, or from the object that references it.

**`GET relations/{h1}/{h2}` names how two people are related**, computed
server-side with the tree's kinship rules:

```bash
scripts/api.py GET relations/{h1}/{h2}
# {"relationship_string": "father", "distance_common_origin": 1, ...}
```

`/all` returns every path between them; `-p depth=` bounds the search for a
common ancestor, 15 generations by default.

## Writing

### Always find first

**Search before creating anything** -- repository, source, citation, place,
event, person, family. Duplicates are the most common damage an assistant does
to a tree and the most tedious to undo.

| Search result | Do this |
|---|---|
| Found, already has the new information | Use it as-is. Write nothing. |
| Found, missing some of the information | `PUT` the existing handle |
| Not found | `POST` a new one |

The middle row is what keeps one "St. Mary's Church" record gaining an address
instead of two records existing.

**When a search returns a plausible match, show it to the user and ask.**
"Same Jan Kowalski or a different one?" is a research judgement. Present what
you found, say what matches and what does not, and wait.

### Read the house rules first

Each tree has its own conventions: how notes are worded, how media are named,
which fields stay empty, whether repositories are used. **Read `house-rules/`
before your first write in a session.** If no rules file exists for this tree,
derive one -- `house-rules/README.md` has the queries -- and offer to save it.

Where the rules are silent, read siblings of the thing you are about to create:
another citation on the same source, another media item of the same type. Where
siblings disagree, show the user two examples, ask which to follow, and record
the answer.

The data is the authority and `house-rules/` caches it. Re-derive a rule that
fights what you are seeing.

### The chain

Gramps is source-focused and event-focused. Facts hang off events, events are
backed by citations, citations point at sources, sources sit in repositories.
Build in that order -- each step needs a handle from the one before:

```
Repository -> Source -> Citation -> Event <- Person / Family
```

Birth, death, baptism and burial are events, cited to a document, referenced by
the person.

### Creating

A person needs `primary_name` and `gender` (0 female, 1 male, 2 unknown,
3 other). `_class` is optional; the endpoint determines the type.

POST returns a transaction list:

```json
[{"type": "add", "_class": "Note", "handle": "103cd...", "old": null,
  "new": {"gramps_id": "N1692", "handle": "103cd...", ...}}]
```

Take the handle from `[0]["handle"]`. Creating a family returns several entries
-- the family plus every person it touched -- so match on
`entry["_class"] == "Family"`.

### Use exact type strings

Type fields accept a string, and **an unrecognised string becomes a custom
type**. `"Transcript"` gives `{"value": 3}`; `"transcript"` gives
`{"value": 0, "string": "transcript"}`, a new custom type, silently. They are
case-sensitive.

Take them verbatim from the database:

```bash
scripts/api.py GET types/          # {"default": {...}, "custom": {...}}
```

### Handle lists come in two shapes

`citation_list`, `note_list` and `tag_list` hold bare handles. `media_list`,
`event_ref_list`, `child_ref_list` and `person_ref_list` hold objects carrying
`ref` plus fields of their own -- a role, a crop rectangle, a relationship.

```bash
scripts/spec.py Event    # array[string] against array[object], per field
```

Check the field before you build it, or mirror the same field on a record that
already has one.

### Events attach to people

Each person carries an `event_ref_list` entry pointing at the event, with that
person's role:

```json
{"ref": "<event handle>", "role": "Primary"}
```

Linking a person to an event is an update to the person. Roles like "Groom",
"Bride", "Witness" live in the same place. Individual events (birth, death,
baptism, burial) attach to the person; family events (marriage, divorce,
engagement) attach to the family.

`birth_ref_index` and `death_ref_index` are **positions within
`event_ref_list`**. Append a birth event and set `birth_ref_index` to its index
in the same write, or it reads as an ordinary event. `-1` means none.

### Updating is read, edit, write

`PUT` replaces the whole object, and any field you leave out is dropped
silently. Fetch the raw record -- no `profile`, no `keys` -- change what you
mean to change, send it all back:

```bash
scripts/api.py GET people/{handle} > /tmp/person.json
# edit: append to event_ref_list, keep every other field
scripts/api.py PUT people/{handle} -b @/tmp/person.json
```

### Media uploads in two passes

`POST media/` sends the file bytes with their own Content-Type. The server
checksums them, stores the file as `<checksum><ext>`, and creates the object
pointing there with an empty `desc`.

Naming it takes three calls:

```bash
scripts/api.py POST media/ -f scan.pdf                    # 1. creates the object
# 2. GET it, set desc and path, PUT it back (leave checksum alone)
scripts/api.py PUT media/{handle}/file -p uploadmissing=true -f scan.pdf   # 3.
```

Step 3 moves the file: a matching checksum with no file at the object's path
makes the server write the bytes there. Files are served through `path`, so
changing `path` alone leaves the object pointing at nothing.

Confirm by fetching the file, not just the record -- `GET media/{handle}/file`
should return 200 and the original byte count.

### Places nest

A place carries a `placeref_list` pointing at whatever encloses it: church in
city in county in state in country. Build upward until you reach an existing
place, and reuse -- one "Boston" per tree.

### Dates

`dateval` is `[day, month, year, slash]`, day first, `0` for unknown parts.
`modifier`, `quality` and `calendar` are integer codes: see
`references/dates.md`.

## Link what you report

**Whenever you name a record, link it**, so the user can check it. The web UI
takes the Gramps ID, on the same host as the API without `/api`:

```
https://<your-instance>/person/I3342
https://<your-instance>/family/F1287
https://<your-instance>/event/E6770
https://<your-instance>/citation/C1434
```

Routes: `person`, `family`, `event`, `place`, `source`, `citation`,
`repository`, `media`, `note`.

Link before a write too, alongside what you intend to change, so the user can
look before agreeing.

## Checking your work

**Verify with a number the API computes.** Object counts are authoritative and
cheap:

```bash
scripts/api.py GET metadata/     # object_counts: people, events, notes, ...
```

The length of a search response misleads: an error object has a length, and a
slightly wrong filter returns a plausible number.

## Undo

Gramps keeps a server-side transaction log:

```bash
scripts/api.py GET transactions/history/ -p page=1 -p pagesize=5
```

Read a diff before sending it regardless.
