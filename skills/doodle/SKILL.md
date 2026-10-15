---
name: doodle
description: Explains anything (a bug, a codebase flow, a protocol, a concept) to a beginner as a Markdown document with clean, friendly diagrams, using very few tokens. Use when the user asks to "explain with pictures/diagrams/drawings", "explain like I'm 5", "draw it", "make an illustrated explanation", "me explica com desenhos/imagens", or says they did not understand a text-only explanation.
---

# Doodle: Diagrams Over Overly Dense Long Explanations

You write **one Markdown file** where each drawing is a tiny ` ```doodle ` text block. Then one command turns every
block into an SVG under `img/` and swaps the block for an image link. Never write SVG by hand, and never open the
generated SVGs: that is where the token savings come from.

## Workflow

1. **Understand first.** If the topic is about this project, read the real code, logs and data. Explanations must be
   true; never invent evidence.
2. **Write `<topic-slug>.md`** in the current directory (or where the user asks), in **the user's language**, using
   the structure below.
3. **Render:** `python3 <this-skill-dir>/scripts/doodle.py <topic-slug>.md`.
   It prints the SVG paths. On `error: ... line N`, fix that block and run again. Re-running is safe: rendered
   blocks are kept as `<!-- doodle ... -->` comments and re-rendered in place.
4. **Reply briefly:** the file path plus 2–3 lines of summary. Don't paste the document into the chat.

No Python? Use ` ```mermaid ` blocks instead (GitHub renders them) and skip step 3.

## Document structure (the teaching method)

```
# <Question the reader actually has, e.g. "Why does the app log me out every morning?">
## In three sentences        -> 3 numbered sentences: what happens, why, what fixes it
## Pieces you need to know   -> table | Piece | What it is | (only if there are 3+ unfamiliar terms)
## Step 1: <one claim>       -> one doodle + 2–5 bullets; end with the "why"
## Step 2: ...               -> 2–5 steps total
## When it happens / Why it matters
## Evidence                  -> only real logs, numbers, file paths (omit if none)
```

Writing rules: short sentences; plain words; define each jargon term the first time; **bold** the key fact in each
step; one idea per drawing; prefer everyday metaphors (a phone book, a mailbox, a queue at a bakery) in
titles and notes.

## Doodle blocks (cheat sheet)

```doodle
timeline: A pizza order
> optional subtitle
Order placed | the app sends it to the shop | info
Oven is full | waits 20 minutes | warn
Delivered | still hot | ok
```

- Line 1 is `kind: Title`. Each row is `label | note | tone`; note and tone are optional.
- Tones: `neutral` (default), `info`, `ok`, `bad`, `warn`. Options: `@sketch` (hand-drawn), `@vertical`,
  `@horizontal`, `@arrow` (for `compare` and `stack`). `\n` breaks a line; `//` starts a comment.
- Keep labels ≤ 4 words and notes ≤ 12 words. Use 3–6 rows; split bigger ideas into two drawings.

| kind | use it for | extra syntax |
|---|---|---|
| `timeline` | what happens in what order | rows only (numbered automatically) |
| `flow` | steps, decisions, branches | `[id] Label \| note \| tone` rows, then `a -> b: label`; `~>` = dashed. No edges = a chain of the rows |
| `cycle` | loops, things that keep repeating | rows only, in loop order |
| `compare` | before/after, A vs B, wrong vs right | `## Column \| tone` then rows (items inherit the column tone); `@arrow` puts → between columns |
| `tree` | folders, hierarchies, parts of a whole | indent children by 2 spaces |
| `stack` | layers (architecture, network, call stack) | rows top to bottom; `@arrow` links them |
| `sequence` | who talks to whom (requests, protocols) | `A -> B: message \| tone`; `~>` = reply (dashed); `A -> A` = self |

Full syntax and examples: [references/dsl.md](references/dsl.md). Read it only if the cheat sheet isn't enough.
