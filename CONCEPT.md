# Concept: one tool, scripts, and a skill

> **Superseded.** What was built is in `skills/gramps/` -- a skill and scripts,
> with **no MCP server at all**. The scripts hold the credential and call the
> API directly, which works because this runs in a harness that already has it.
>
> The reasoning below still holds; only the last layer went. Two findings
> removed the argument for keeping a server: Gramps Web ships its own read-only
> assistant (v3.6.0+), so the chat-interface case that justified an MCP is
> covered upstream, and every instance publishes `/api/openapi.json`
> unauthenticated, so "point at the live spec" needs no server either.
>
> Kept as the record of how the design got there.

## The principle

**This repo only contains what the Gramps Web API can't do for itself.**

The API validates its own input, selects its own fields, describes its own endpoints, filters its own queries and reports its own errors. None of that belongs here. What it can't do is authenticate on your behalf, and know how genealogy research works. That's the whole remaining surface.

## Why the current design fails it

Three complaints, one mistake:

- **Too strict** — validating what the API validates. `models/parameters/base_params.py:81-105` rejects `extend`/`profile` values outside a hardcoded list, so a call Gramps would accept fails here instead.
- **Drifts** — describing what the API describes. 81 endpoints in `ApiCalls`, 41 never called, all hand-transcribed from a spec the server already publishes.
- **Six edits per endpoint** — `api_calls.py`, `api_mapping.py`, a params file, a handler, a tool, `TOOL_REGISTRY`.

The root cause is that **this is a mirror of someone else's API living outside their repo**, and mirrors rot silently — nothing tells you when upstream moves. The durable fixes are to upstream it into `gramps-project/web-api`, or to stop mirroring. This is the second.

The mirror was the right call when it was made. Skills didn't exist, 1:1 endpoint→tool was the universal pattern, and transcribing the spec was how you found out which tools were worth having. The experiment ran — 81 endpoints in, 42 used, 16 tools out — and this is what the result implies.

## The shape

**One MCP tool. Everything else is a script. Knowledge lives in the skill.**

```
MCP server                        skills/gramps/
└── gramps_api(method,            ├── SKILL.md            genealogy workflow
               endpoint,          ├── scripts/            credential-free clients
               params, body)      │   ├── show.py         person + timeline + refs, trimmed
   holds the credentials          │   ├── report.py       POST → poll → fetch → summarize
   full access, no gating         │   └── update.py       GET → edit → PUT
                                  └── references/gql.md
```

`endpoint` is a free-form path relative to `/api` — `people/`, `people/{handle}/timeline`, `search/`. No enum, no allowlist. An endpoint Gramps ships tomorrow works tomorrow.

**The MCP server is the only thing that holds a credential.** Scripts don't read `.env`; they call the tool. So the skill directory contains no secret, is safe to share and audit, and there is exactly one place a token is ever minted. `server.py:215` is already configured for this — `stateless_http=True, json_response=True` means a script's call is one `httpx.post` with a plain JSON reply, no session handshake, no SSE to parse.

The consequence: this commits to HTTP transport. A stdio server has no socket to POST to, so `run_stdio_server()` and the dual-transport split at `server.py:312-358` go away, and the server runs on localhost or wherever you put it. Docker isn't scaffolding you don't need — it's just how it starts.

**Scripts are conveniences over calls that already work without them.** Every one of them decomposes into passthrough calls the model can make directly. That matters because scripts don't run everywhere (below), and the fallback is more round trips, never a lost capability.

The reason to have them at all is one asymmetry: **a tool's result flows through the model's context; a script's doesn't — only what it prints.** So a script earns its place when it fetches a lot and returns a little. `show.py` pulls a person plus timeline plus five referenced objects and prints the readable slice. `report.py` polls a wait loop and summarizes a large file. `update.py` saves two round trips on an edit.

A script decides **what calls to make**, never **what's valid**. The moment a script declares a field, the mirror starts again.

## The partition

The principle sorts every line in the repo, exactly:

| The API can't… | keep |
|---|---|
| authenticate on your behalf | the MCP tool |
| know genealogy practice | `SKILL.md` |

| The API can… | delete |
|---|---|
| validate input | `models/parameters/` — 1,681 lines, 51 classes |
| select fields (`keys`, `skipkeys`, `profile`) | `handlers/` — 2,181 lines |
| describe itself (live spec on your instance) | `api_calls.py`, `api_mapping.py`, vendored `apispec.yaml` |
| filter and query (GQL) | `tools/search_*.py` |
| report its own errors | `_format_http_error`, `client.py:140-155` |

~7,200 lines of source → one tool, three scripts, and a skill.

**No merge tool.** `client.py:248-319` does a GET-then-merge before every PUT, deduping `*_list` fields on `ref`. That encodes Gramps' data model in the server — a mirror wearing different clothes, drifting the same way when a differently-shaped field arrives. It's also 70 lines guessing at intent the model already has: it has the GET response on screen and knows it's adding one event to one person. GET, edit, PUT. Two calls, works anywhere, `update.py` wraps it for convenience only.

## Rules that fall out

**Read-side coupling is fine; write-side coupling is what burned you.** Trimming output references field names too, but if Gramps renames one, a trimmer prints nothing for it — soft failure, visible. A validator that doesn't recognise a new value blocks the call entirely.

**Errors get better.** Today a 422 becomes `"Invalid data provided."`, discarding which field and why. Deleting the layer restores the real message.

**Trim, don't narrate.** `person_detail_handler.py` is 348 lines assembling English for a reader that parses JSON fine. Selection was the value; prose never was. And `keys`/`skipkeys`/`profile` do the selection server-side, so scripts only trim what the API can't.

**Always leave `--raw`.** Any trimmed view eventually hides the field you need, and if the only escape is editing the script, you'll be editing it at the worst moment.

**Point at the live spec, not a copy.** Your instance serves its OpenAPI spec for the version you actually run. A generated `endpoints.md` goes stale exactly as fast as the enum did.

**Full access, no method gating.** The tree is the user's responsibility. Gramps keeps `transactions/history/` upstream anyway, so an undo trail exists without building one.

## What SKILL.md holds

The test for every line: *does this go stale when Gramps Web ships a release?*

**Doesn't drift, and is yours** — Repository → Source → Citation → Event → People ordering; "always find before you create"; read-modify-write on PUT; Gramps date conventions; the marriage-record walkthrough. That's most of `resources/gramps-usage-guide.md` (318 lines), and it's the part the 16 tools were least able to express.

**Does drift, so don't write it down** — endpoint paths, methods, params, field names, valid `extend`/`profile` values.

The guide also gets shorter by losing a job. Today it translates between your vocabulary (`create_person`, `PersonData`) and what Gramps stores. Remove the tool layer and there's one vocabulary — a person *is* the JSON with `event_ref_list`, `primary_name` — and half the explanation stops being necessary.

GQL is the honest exception. `gql-documentation.md` (413 lines) describes their query language, so by the test it's theirs — but it isn't in the OpenAPI spec and there's nothing live to point at. It stays as a checked-in snapshot, labelled as one. One acknowledged mirror instead of twenty-two.

**"Always find first" was the one rule the old design enforced structurally** — no tool existed to create without searching. Now it's a sentence in a file. The fix isn't a guard, it's making search the easiest thing to reach for.

## Where each layer runs

| Surface | Code execution | Scripts | MCP tool |
|---|---|---|---|
| Claude Code | your machine, OS sandbox | yes | yes |
| Claude Desktop / Cowork | local VM, attached folders | yes | yes |
| claude.ai in a browser | Anthropic cloud container, no local files | no | yes (remote) |

The one tool works everywhere; scripts are the optimization where they run. Note that **network egress is denied by default in all three sandboxes** and needs allowlisting — Anthropic found domain allowlists are themselves a weak point, since a malicious file exfiltrated workspace data through an allowlisted endpoint. Scripts hit that boundary; a local stdio MCP server wouldn't, but HTTP transport is the trade for scripts being able to call it.

One risk worth knowing, separate from the delete question: **tree data is fetched content entering context.** A note field is text an agent reads. Near-zero for your own tree; not zero the day you import someone else's GEDCOM.

## The old repo

v1.1.0 is the final release of the current design. Docker and the HTTP server survive — they're how the one tool runs. What goes is the 7,000 lines of mirror inside them, the stdio path, and the AGPL header hook. Forks pulling `:latest` will break, which after a year unmaintained is a reasonable prompt to look at what changed.

## Why this is the current pattern

Anthropic's answer to tool-count bloat is progressive disclosure and code execution: load definitions on demand, let scripts filter data locally so intermediate results never enter context. Their benchmark went 150,000 tokens → 2,000 for equivalent work ([Anthropic Engineering](https://www.anthropic.com/engineering/code-execution-with-mcp)). Skills implement that in three tiers — ~100 tokens of frontmatter at rest, the body only when triggered, bundled files only when read, and *"the script's code never loads into the context window; only its output consumes tokens"* ([Agent Skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)).

The 1:1 endpoint→tool mapping this repo used is the documented anti-pattern: context cost before the agent does anything, and tool-selection accuracy that degrades as the count grows ([Hackteam](https://hackteam.io/blog/stop-converting-openapi-specs-mcp-servers/), [Zuplo](https://zuplo.com/learning-center/mapping-rest-apis-to-mcp-tools)).

Portability is no longer an argument for keeping tools in the server. Agent Skills became an open specification in December 2025; within 48 hours OpenAI added it to ChatGPT and Codex, Microsoft to VS Code, and by March 2026 some 32 tools including Gemini CLI, JetBrains Junie, AWS Kiro and Block's Goose read the same `SKILL.md`. Both MCP and Skills now sit under the Linux Foundation's Agentic AI Foundation ([Linux Foundation](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation), [paperclipped](https://www.paperclipped.de/en/blog/agent-skills-open-standard-interoperability/)).

The fair counterargument: Speakeasy recommends curated typed tools over generic access, and Hackteam recommends workflow-shaped tools because agents fumble multi-step sequences ([Speakeasy](https://www.speakeasy.com/blog/skills-vs-mcp/)). Both mostly dissolve here. Curated typed tools are *what this repo already is* — the curation went stale and the typing became a gate against valid calls. And the multi-step-fragility argument assumes nothing supplies the workflow, which is what the scripts and the skill are for. They're workflow-shaped tools. They're just not in a tool list.
