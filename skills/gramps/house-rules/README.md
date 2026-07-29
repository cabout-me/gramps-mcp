# House rules

Each tree has conventions that live only in its data: how notes are worded, how
media are named, which fields stay empty, whether repositories are used. Records
that ignore them are valid and visibly wrong, and nothing errors.

This folder holds them.

## Using it

**Read the rules file for the connected tree before your first write in a
session.** If none exists, derive one and offer to save it.

One file per tree. With a single tree, `rules.md` is enough. With several, name
the file after the tree and match on `GRAMPS_API_URL`.

## Deriving rules

Rules are observations, so derive them by counting and record the count. A
convention followed 141 times out of 143 is a rule; one followed twice is a
coincidence.

Pull a collection with `keys` to keep it small, then count the shapes.

```bash
# naming conventions
api.py GET sources/ -p page=1 -p pagesize=400 -p keys=gramps_id,title
api.py GET media/   -p page=1 -p pagesize=900 -p keys=gramps_id,desc,path,mime

# whether an object type is used at all
api.py GET repositories/ -p page=1 -p pagesize=50

# date conventions: count modifier/quality combinations
api.py GET events/ -p page=1 -p pagesize=9000 -p keys=gramps_id,type,date

# how a kind of record is documented: read siblings
api.py GET citations/ -p "gql=source_handle = <handle>" -p page=1 -p pagesize=10
# then fetch their notes and media
```

Ask what appears in every one, what appears in none, and what varies. The first
two are rules. The third belongs to the user.

## Writing a rules file

Each entry gives **the rule, the evidence, the query**. The evidence makes it
trustworthy; the query makes it refreshable as the tree grows.

```markdown
## Media naming

`<CODE> <Surname> <Surname>` -- document-type code, then the people involved.

Evidence: 143 of 143 `HA ` items follow it; codes HA/OA/GA/BP/RB/DP/DA.
Query:    api.py GET media/ -p page=1 -p pagesize=900 -p keys=desc,path
```

The data is the authority and this folder caches it. Re-run the query when a
rule fights what you are seeing.

## Ambiguous rules

Show the user two existing records that differ and ask which to follow, then add
the answer here with the date and the reason. A rule you were told outranks one
you inferred, and should say so.
