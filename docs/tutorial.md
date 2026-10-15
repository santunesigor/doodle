# Doodle tutorial

> [Leia em português](tutorial.pt-BR.md)

This tutorial takes about 10 minutes. You will install Doodle, ask for your first illustrated explanation, change a
drawing, and learn to write diagrams yourself.

## 1. Install

You need **Python 3.8 or newer**. Check with `python3 --version`.
The `npx` installer also needs Node.js 22.20+ and Git; the native plugin and manual options below don't need Node.js.
Terminal examples use Bash syntax (Linux, macOS, WSL, or Git Bash).

Pick one of the following.

**Claude Code** (plugin marketplace), inside a Claude Code session:

```
/plugin marketplace add santunesigor/doodle
/plugin install doodle@doodle
```

**Codex, Cursor, Claude Code and other agents with skills support:**

```bash
npx skills add santunesigor/doodle --skill doodle
```

The CLI installs into the current project by default. To install globally for one agent, use:

```bash
npx skills add santunesigor/doodle --skill doodle --agent codex --global
```

Replace `codex` with `claude-code` or `cursor` for those agents.

**Manual (Codex):**

```bash
git clone https://github.com/santunesigor/doodle
mkdir -p ~/.agents/skills
cp -R doodle/skills/doodle ~/.agents/skills/
```

For Claude Code, use `~/.claude/skills` as the destination instead. Install into a new `doodle` folder to avoid merging
with an existing copy.

**Testing a local copy before publishing (Codex):** from the repository root, link the folder instead of copying it,
so your edits show up right away. Choose either the copy above or this link:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/doodle" ~/.agents/skills/doodle
```

If your agent doesn't discover the skill after installation, open a **new** session. To check, ask "which skills do
you have?". You should see `doodle` in the list. In Codex, you can invoke it with `$doodle`.

## 2. Your first explanation

Ask for it in plain words, in any language:

> Explain how DNS works with drawings. I'm a beginner.

The agent will:

1. read the relevant code, logs or docs, if the topic is about your project;
2. write `how-dns-works.md` (the name comes from the topic) with the drawings as tiny text blocks;
3. run the renderer, which creates the pictures in `img/`;
4. reply with the file path and a short summary.

To read it, open the `.md` file:

- **VS Code:** `Ctrl+Shift+V` (`Cmd+Shift+V` on Mac) opens the preview.
- **GitHub:** commit the `.md` file **and** the `img/` folder. The pictures follow your light or dark theme.
- **Obsidian:** open the folder as a vault.

See finished results in [examples/dns](../examples/dns/how-dns-works.md) and
[examples/git-rebase](../examples/git-rebase/git-rebase-pt-br.md).

### Asking well

| You want | Ask like this |
|---|---|
| An explanation of a bug in your code | "I don't get why `checkout()` fails twice. Explain with drawings, using the logs in `logs/today.txt`." |
| A concept | "Explain OAuth with pictures, like I'm 5." |
| A specific language | "Me explica com desenhos, em português." (the reply follows your language anyway) |
| A specific file name or place | "…and save it in `docs/explanations/`." |
| A hand-drawn look | "…use the sketch style." |

## 3. Every document has the same shape

Doodle writes in a fixed order, built to make things click:

1. **In three sentences:** the main idea, how it works, and why it matters (or what fixes the problem).
2. **Pieces you need to know:** a short table when there are at least three unfamiliar terms.
3. **Steps:** each one makes one claim, with one drawing and a few bullets that end with the "why".
4. **When it happens / Why it matters.**
5. **Evidence:** real logs, numbers and file paths. This section only appears when there is real proof.

## 4. Change a drawing

After rendering, each drawing stays in the file as a comment right above its image:

```
<!-- doodle
cycle: The cache cycle
Full lookup | walks the tree (slow) | info
Answer cached | kept for TTL seconds | ok
-->
![The cache cycle](img/how-dns-works-the-cache-cycle.svg)
```

You have two ways to change it:

- **Ask the agent:** "In drawing 2, mark the cache step as a problem and add a step for TTL expiring."
- **Edit it yourself:** change the text inside the comment, then run the renderer again:

```bash
python3 ~/.agents/skills/doodle/scripts/doodle.py how-dns-works.md
```

This path is for a manual Codex installation; for a manual Claude Code copy, use `~/.claude/skills` instead.
If you installed through the plugin marketplace, ask the agent to rerender the document; its plugin folder may differ.
The command redraws the pictures and preserves the surrounding text. Invalid diagram specs or output paths leave the
document and existing images unchanged. If you chose a custom image directory with `-o`, pass it again on every run.

## 5. Write your own diagrams

You can use Doodle without an agent. Write a ` ```doodle ` block in any Markdown file and run the renderer on it.

Every block has the same shape:

```doodle
timeline: A pizza order
> a subtitle is optional
Order placed | the app sends it to the shop | info
Oven is full | waits 20 minutes | warn
Delivered | still hot | ok
```

- **The first line** is `kind: Title`.
- **Each row** is `label | note | tone`. Only the label is required.
- **Tones** color the story: `ok` is green (the healthy path or the fix), `bad` is red (the broken part), `warn` is
  amber (the risky step), `info` is blue (an actor or an input), and `neutral` is gray (the default).

### Which kind to use

| The question you're answering | Kind |
|---|---|
| In what order do things happen? | `timeline` |
| What decides what? Where does it branch? | `flow` |
| Why does it keep happening? | `cycle` |
| What changed? Which option is better? | `compare` |
| Where is it? What is inside what? | `tree` |
| What sits on top of what? | `stack` |
| Who talks to whom? | `sequence` |

### One small example of each

```doodle
flow: Can I deploy?
[a] Tests pass? | warn
[b] Deploy | ok
[c] Fix first | bad
a -> b: yes
a -> c: no
c -> a: try again
```

```doodle
compare: Password vs passkey
@arrow
## Password | bad
Can be guessed
Can be phished
## Passkey | ok
Nothing to guess
Bound to the real site
```

```doodle
tree: Where the config lives
app/
  config/
    default.json | base values
    prod.json | overrides default | warn
  main.py
```

```doodle
stack: A web app
@arrow
Browser | what the user sees | info
API server
Database | where the data lives | ok
```

```doodle
sequence: Logging in
User | info
User -> App: email + password
App -> Database: check the password
Database ~> App: matches | ok
App ~> User: welcome! | ok
```

```doodle
cycle: The code review loop
Write code | info
Open a pull request
Review asks for changes | warn
Fix and push | ok
```

The full syntax, with every option, is in [skills/doodle/references/dsl.md](../skills/doodle/references/dsl.md).

### Options

Add them on their own line, right after the title:

- `@sketch` gives a hand-drawn look.
- `@vertical` or `@horizontal` forces the direction of a `timeline` or `flow`.
- `@arrow` draws arrows between `compare` columns or `stack` layers.

### Rendering a single diagram

In a local clone of this repository, save the pizza example above (without the fences) as `pizza.txt` in the repository root.
If you don't have a clone yet, run `git clone https://github.com/santunesigor/doodle.git`, then `cd doodle`.
From that root folder:

```bash
python3 skills/doodle/scripts/doodle.py pizza.txt
python3 skills/doodle/scripts/doodle.py pizza.txt -o out.svg
printf '%s\n' 'stack: Hi' 'A' 'B' | python3 skills/doodle/scripts/doodle.py - > hi.svg
```

These create `pizza.svg`, `out.svg`, and `hi.svg`. Open an SVG in your browser to view it.
To render a Markdown file, use the same command with its `.md` path; the command updates that file in place.

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `error: line 3: unknown kind 'pie'` | The first line must start with one of the 7 kinds. |
| `error: cycle needs at least 2 rows` | Add rows, or pick another kind. |
| A note became a tone | A last cell that is exactly a tone word (`ok`, `bad`…) becomes the tone. Rephrase it, e.g. `status \| all good`. |
| A box is too tall | Keep labels to 4 words or fewer and notes to 12 words or fewer, or split the idea into two drawings. |
| Pictures don't show up on GitHub | Commit the `img/` folder together with the `.md` file. |
| No Python on the machine | The agent writes ` ```mermaid ` blocks instead. GitHub renders them too, with a plainer look. |
| `npx: command not found` | Install Node.js, or choose the native plugin/manual installation option. |
| `SVG output must stay inside 'img'` | If you previously used `-o assets/diagrams`, pass that same option again. Keep image links inside the selected directory. |
| The skill isn't used | Start a new session after installing, or ask explicitly: "use the doodle skill". |
