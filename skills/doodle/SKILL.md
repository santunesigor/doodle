---
name: doodle
description: Explains bugs, code flows, protocols, and concepts in a Markdown document with SVG diagrams generated from small text specs, adapted to the reader's level. Use when the user asks for an explanation with diagrams or drawings, says "explain like I'm 5" or "me explica com desenhos", wants an illustrated explanation after not understanding text alone, or wants to change how Doodle explanations look or read (theme, colors, audience, depth).
---

# Doodle: Diagrams Over Overly Dense Long Explanations

You write **one Markdown file** where each drawing is a tiny ` ```doodle ` text block. Then one command turns every
block into an SVG under `img/` and swaps the block for an image link. Use the renderer instead of writing SVG by hand.
Keep generated SVG markup out of context unless debugging the renderer; inspect a visual preview when needed.

`<doodle>` below means `python3 <this-skill-dir>/scripts/doodle.py`.

## Workflow

1. **Read the preferences.** Run `<doodle> --settings` from the folder where the document will go. It prints the
   merged `doodle.json` settings as JSON. Use `audience`, `depth`, `language`, `docsDir` and `notes` (house rules
   written by the user; follow them). The current request wins over the file: "like I'm 5" means `kid`,
   "quick"/"rápido" means `quick`, "in depth"/"a fundo" means `deep`.
2. **Understand first.** If the topic is about this project, read the real code, logs and data. Explanations must be
   true; never invent evidence.
3. **Write `<topic-slug>.md`** in `docsDir` (`doodle/` by default), relative to the `root` that `--settings`
   prints (the current directory when `root` is null), or where the user asks. Use the user's language unless
   `language` says otherwise, and the structure below. Rendering adds `docsDir` to the repository's `.gitignore`
   unless `gitignore` is false; if the user wants to commit the explanations, set `"gitignore": false`.
4. **Render:** `<doodle> <topic-slug>.md`. It prints the SVG paths, then `warning: file:line: ...` lines. Fix warnings
   that reveal a mistake (a misspelled tone, an edge to a node that doesn't exist); the rest are judgment calls.
   On `error: file:line: ...`, fix that line and run again. Re-running is safe: rendered blocks are kept as
   `<!-- doodle ... -->` comments and re-rendered in place. Theme, colors and image folder come from `doodle.json`;
   don't pass `--theme` or `-o` unless the user asked for this one document.
5. **Reply briefly:** the file path plus 2–3 lines of summary. Don't paste the document into the chat.

No Python? Use ` ```mermaid ` blocks instead (GitHub renders them) and skip step 4.

## Adapt to the reader

| `audience` | Write like this |
|---|---|
| `kid` | No jargon at all. Everyday metaphors in every step and title. Sentences under 12 words. |
| `beginner` (default) | Define each technical term the first time. A metaphor where it helps. |
| `developer` | Assume programming basics. Real names, file paths and short code snippets; metaphors only for the hard part. |
| `expert` | Dense and precise. Skip the basics, focus on the mechanism, edge cases and trade-offs. |

| `depth` | Shape |
|---|---|
| `quick` | Title question, "In three sentences", 1–2 drawings, one-line takeaway. Nothing else. |
| `standard` (default) | The full structure below with 2–4 steps. |
| `deep` | 3–6 steps, plus the two sections marked *deep* below. |

## Document structure (the teaching method)

```
# <Question the reader actually has, e.g. "Why does the app log me out every morning?">
## In three sentences        -> 3 numbered sentences: what happens, why, what fixes it
## Pieces you need to know   -> table | Piece | What it is | or a `hub` drawing (only if 3+ unfamiliar terms)
## Step 1: <one claim>       -> one doodle + 2–5 bullets; end with the "why"
## Step 2: ...               -> 2–5 steps total
## When it happens / Why it matters
## Common mistakes           -> deep only: 2–4 bullets, each a mistake and how to avoid it
## Evidence                  -> only real logs, numbers, file paths; a `bars` drawing for numbers (omit if none)
## Check yourself            -> deep only: 2–3 questions, each answer in <details><summary>Answer</summary>…</details>
```

Numbers that only illustrate (not measured) can go in a step's `bars` drawing; say so in its subtitle, e.g.
`> illustrative numbers`. The Evidence section holds only real data.

Writing rules: short sentences; plain words; **bold** the key fact in each step; one idea per drawing; the drawing's
title states the step's claim; tones tell the story (`bad` = the broken part, `ok` = the fix or healthy path,
`warn` = the risky step, `info` = the actor or input).

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
  `@horizontal`, `@arrow` (for `compare`, `stack`, `hub`), `@theme NAME`. `\n` breaks a line; `//` starts a comment.
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
| `bars` | how much: time, size, count, cost | `Label \| 120 ms \| tone`; the note holds the number |
| `hub` | what something is made of; key vocabulary | first row is the center, the others go around it |

Full syntax and examples: [references/dsl.md](references/dsl.md). Read it only if the cheat sheet isn't enough.

## Personalize

When the user states a **lasting** preference ("always use the chalk theme", "my team are senior devs", "save these
in docs/explain", "use our brand purple"), save it instead of just applying it once:

- For this project: edit the `doodle.json` that `--settings` lists last in `sources` (the nearest one), or create
  one at the repository root with `<doodle> --init`. Files cascade: one in a subfolder overrides only the keys it
  names, for documents in that subfolder.
- For every project: edit `~/.config/doodle/config.json`.
- For one document only: add `@theme NAME` to its blocks, so re-renders keep the look.

Then re-render any document they are looking at. Settings: `theme` (`paper`, `clean`, `candy`, `blueprint`,
`chalk`), `sketch`, `scheme` (`auto`/`light`/`dark`), `colors` (per tone, `#hex`), `imageDir`, `audience`, `depth`,
`language`, `docsDir`, `gitignore`, `notes`. Details and examples: [references/customize.md](references/customize.md).
