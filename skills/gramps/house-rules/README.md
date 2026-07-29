# House rules

Every tree has conventions that exist nowhere in Gramps, the API, or the
OpenAPI spec. They live only in the data: how notes are worded, how media are
named, which fields are deliberately left empty, whether repositories are used
at all.

An agent that does not know them writes records that are technically valid and
visibly wrong -- a prose citation in a tree whose citations are bare URLs, a
descriptive media title in a tree that uses document-type codes. Neither errors.
Both need cleaning up by hand.

This folder is where those rules are written down.

## How to use it

**Read the rules file for the connected tree before your first write in a
session.** If none exists, derive one (below) and offer to save it.

One file per tree. With a single tree, `rules.md` is enough. With several, name
the file after the tree and match on `GRAMPS_API_URL`.

## Deriving rules from the data

Rules are observations, not preferences -- so derive them by counting, and
record the count. A convention followed 141 times out of 143 is a rule; one
followed twice is a coincidence.

The general move: pull a collection with `keys` to keep it small, then count
the shapes.

```bash
# naming conventions
api.py GET sources/ -p page=1 -p pagesize=400 -p keys=gramps_id,title
api.py GET media/   -p page=1 -p pagesize=900 -p keys=gramps_id,desc,path,mime

# is a whole object type unused?
api.py GET repositories/ -p page=1 -p pagesize=50

# date conventions: count modifier/quality combinations
api.py GET events/ -p page=1 -p pagesize=9000 -p keys=gramps_id,type,date

# how a specific kind of record is documented: read siblings
api.py GET citations/ -p "gql=source_handle = <handle>" -p page=1 -p pagesize=10
# then fetch their notes and media and read them
```

Then ask: what is in every one of these, what is in none of them, and what
varies? The first two are rules. The third is a real choice, and belongs to the
user, not to you.

## Writing a rules file

Keep each entry to: **the rule, the evidence, the query.** The evidence is what
makes it trustworthy; the query is what makes it refreshable when the tree
grows.

```markdown
## Media naming

`<CODE> <Surname> <Surname>` -- document-type code, then the people involved.

Evidence: 143 of 143 `HA ` items follow it; codes HA/OA/GA/BP/RB/DP/DA.
Query:    api.py GET media/ -p page=1 -p pagesize=900 -p keys=desc,path
```

Rules go stale. Re-run the query when a rule seems to fight the data rather
than assuming the file is right -- **the data is the authority, this folder is
a cache of it.**

## When a rule is ambiguous

Do not pick. Show the user two existing records that differ and ask which to
follow -- then add the answer here, with the date and the reason. A rule you
were told is worth more than one you inferred, and it should say so.
