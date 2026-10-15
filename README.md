# Doodle 🖍️

**D**iagrams **O**ver **O**verly **D**ense **L**ong **E**xplanations.

A skill for AI coding agents (Claude Code, Codex, Cursor…) that explains anything (a bug, a code flow,
a protocol, a concept) as **a Markdown file with clean, friendly diagrams**, written for beginners.

> [Leia em português](README.pt-BR.md)

![The cache cycle](examples/dns/img/how-dns-works-the-cache-cycle.svg)

## Why

Asking an AI to "draw it" usually means one of two things:

- **Hand-written SVG** looks nice, but costs about 1,000 tokens per picture, and the arrows and text often misalign.
- **Mermaid** is cheap, but it looks generic and only covers some kinds of diagrams.

Doodle has the agent write a **tiny text spec**. A dependency-free Python script turns it into a polished SVG,
with dark mode, automatic text wrapping and consistent colors.

```doodle
cycle: The cache cycle
Full lookup | walks the tree (slow) | info
Answer cached | kept for TTL seconds | ok
Instant answers | everyone near reuses it | ok
TTL expires | the answer is thrown away | warn
```

Those 5 lines produce the image above. In our tests, the same 4 diagrams took **1.4 KB of specs against 15.3 KB of
hand-written SVG: about 11× fewer tokens**. The agent also never has to read the SVGs back.

## What you get

- **A teaching structure that works:** three-sentence summary → "pieces you need to know" → one drawing per step →
  why it matters → evidence.
- **7 diagram kinds:** `timeline`, `flow`, `cycle`, `compare`, `tree`, `stack` and `sequence`.
- **Looks good everywhere:** GitHub, VS Code and Obsidian, in **light and dark mode**. There is also a `@sketch`
  hand-drawn style.
- **Written in your language:** you ask in Portuguese, you get the explanation in Portuguese.
- **No dependencies:** only Python 3.8+. Without Python, the agent falls back to Mermaid.

## Install

**Claude Code** (plugin marketplace):

```
/plugin marketplace add santunesigor/doodle
/plugin install doodle@doodle
```

**Any agent with skills support** (Codex, Cursor, Claude Code…), via [skills](https://skills.sh):

```bash
npx skills add santunesigor/doodle
```

**Manual:**

```bash
git clone https://github.com/santunesigor/doodle
cp -r doodle/skills/doodle ~/.claude/skills/
```

## Use

**New here? Follow the [10-minute tutorial](docs/tutorial.md).**

Just ask:

> explain how DNS works with drawings
>
> I didn't get this bug, show me with pictures
>
> me explica o git rebase com desenhos

The agent writes `<topic>.md`, runs the renderer, and gives you the path.

You can also run the renderer yourself:

```bash
python3 skills/doodle/scripts/doodle.py notes.md   # renders every ```doodle block in place
python3 skills/doodle/scripts/doodle.py spec.txt   # one spec -> spec.svg
```

Rendered blocks stay in the file as `<!-- doodle ... -->` comments, so you can edit them and run the command again.

## Examples

- [How does my browser find a website?](examples/dns/how-dns-works.md) (English: tree, sequence, stack, cycle)
- [Por que o `git rebase` "reescreve a história"?](examples/git-rebase/git-rebase-pt-br.md) (Portuguese: timeline, compare, flow)

The full syntax is in [skills/doodle/references/dsl.md](skills/doodle/references/dsl.md).

## Development

```bash
python3 -m unittest discover -s tests
```

## License

MIT
