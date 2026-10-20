<h1 align="center">Doodle</h1>

<p align="center"><sub><strong>D</strong>iagrams <strong>O</strong>ver <strong>O</strong>verly <strong>D</strong>ense <strong>L</strong>ong <strong>E</strong>xplanations</sub></p>

<p align="center"><strong>Turn “I don't get it” into a picture.</strong></p>
<p align="center">Illustrated explanations for AI coding agents. Small text specs. Friendly SVG diagrams.</p>

<p align="center">
  <a href="https://github.com/santunesigor/doodle/actions/workflows/test.yml"><img src="https://github.com/santunesigor/doodle/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white" alt="Python 3.8 or newer"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT license"></a>
</p>

<p align="center">
  <a href="#install">Install</a> · <a href="#use">Use</a> · <a href="#make-it-yours">Customize</a> ·
  <a href="#examples">Examples</a> ·
  <a href="docs/tutorial.md">Tutorial</a> · <a href="CONTRIBUTING.md">Contribute</a> ·
  <a href="README.pt-BR.md">Português</a>
</p>

Doodle is an [Agent Skill](https://agentskills.io/) for **Claude Code, Codex, Cursor, and other compatible agents**.
It explains bugs, code flows, protocols, and concepts in a Markdown document written for your level, in your language.

<p align="center">
  <img src="docs/demo.svg" alt="Doodle demo: a request becomes a five-line spec, then a diagram of the DNS cache cycle">
</p>

## Install

The renderer needs **Python 3.8+** and uses only the standard library. No API keys or Python packages are needed.
If Python is unavailable, the skill falls back to Mermaid.

The [skills CLI](https://github.com/vercel-labs/skills) installer also needs Node.js 22.20+ with `npx` and Git.
If you don't use Node.js, choose the native Codex/Claude Code option below or the manual installation in the tutorial.
To use the CLI, run this in your project folder and choose your agent:

```bash
npx skills add santunesigor/doodle --skill doodle
```

This installs into the current project. Add `--global` to use Doodle across projects.

<details>
<summary><strong>Codex</strong></summary>

Install globally from your terminal:

```bash
npx skills add santunesigor/doodle --skill doodle --agent codex --global
```

Or ask Codex to use its built-in installer:

```text
$skill-installer install https://github.com/santunesigor/doodle/tree/main/skills/doodle
```

</details>

<details>
<summary><strong>Claude Code</strong></summary>

Run inside Claude Code:

```text
/plugin marketplace add santunesigor/doodle
/plugin install doodle@doodle
```

Or use the skills CLI:

```bash
npx skills add santunesigor/doodle --skill doodle --agent claude-code --global
```

</details>

For manual installation and local development, see the [tutorial](docs/tutorial.md#1-install).
If your agent doesn't discover the skill after installation, start a new session.

## Use

Ask in plain language:

```text
Explain how DNS works with drawings. I'm a beginner.
```

```text
I don't understand this bug. Show the flow with diagrams, using the code in this repo.
```

```text
Me explica o git rebase com desenhos, em português.
```

```text
Explain our checkout flow for the new senior engineers, in depth, with the blueprint theme.
```

In Codex, you can also invoke it explicitly: `$doodle explain how DNS works with diagrams`.

The agent reads relevant evidence, writes `<topic>.md`, renders diagrams into `img/`, and replies with the document path.
Open the Markdown preview in your editor, or commit the document and its images to view them on GitHub.

## How it works

The agent writes a small diagram spec instead of SVG markup:

```doodle
cycle: The cache cycle
Full lookup | walks the tree (slow) | info
Answer cached | kept for TTL seconds | ok
Instant answers | everyone near reuses it | ok
TTL expires | the answer is thrown away | warn
```

Those five lines generate the preview above. The renderer handles layout, text wrapping, colors, light and dark modes,
five themes, and an optional `@sketch` style. It also lints the specs: a misspelled tone or an arrow pointing to a
box that doesn't exist becomes a warning with its line number, so the agent can fix it before you see it. Writing compact specs keeps SVG markup out of the agent's context;
actual token savings depend on the diagram and tokenizer.

Each explanation starts with three sentences, introduces unfamiliar terms, and builds the idea one diagram at a time.
When the topic concerns your project, it uses real code, logs, and file paths as evidence.

### Nine diagram types

| Type | Best for |
| --- | --- |
| `timeline` | Events and their order |
| `flow` | Decisions, branches, and paths |
| `cycle` | Repeating processes |
| `compare` | Alternatives and before/after |
| `tree` | Folders and hierarchies |
| `stack` | Layers and architecture |
| `sequence` | Requests, replies, and protocols |
| `bars` | Numbers: time, size, count, cost |
| `hub` | What something is made of; key vocabulary |

See the [syntax reference](skills/doodle/references/dsl.md) for options and examples of every type.

## Make it yours

Doodle adapts both **how it writes** and **how it draws**. Tell the agent once, for example "always explain for
senior developers and use the clean theme with our purple", and it saves that in a `doodle.json`:

```json
{
  "theme": "clean",
  "colors": {"info": "#6d28d9"},
  "audience": "developer",
  "depth": "deep",
  "docsDir": "docs/explain",
  "gitignore": false,
  "notes": "Link to files as path:line."
}
```

| Setting | Choices |
| --- | --- |
| `audience` | `kid`, `beginner` (default), `developer`, `expert` |
| `depth` | `quick` (two drawings), `standard`, `deep` (adds common mistakes and a self-check quiz) |
| `theme` | `paper` (default), `clean`, `candy`, `blueprint`, `chalk` |
| `colors` | one `#hex` per tone; dark-mode versions are derived for you |
| `scheme` | `auto` (follows light/dark mode), `light`, `dark` |

Put it at your project root (`doodle.json`; files in subfolders override only what they name) or in
`~/.config/doodle/config.json` for every project. A single diagram can switch with `@theme chalk`.
See [customize.md](skills/doodle/references/customize.md) for every setting.

<p align="center">
  <img src="examples/themes/img/themes-can-i-deploy-paper.svg" width="49%" alt="Theme paper">
  <img src="examples/themes/img/themes-can-i-deploy-clean.svg" width="49%" alt="Theme clean">
  <img src="examples/themes/img/themes-can-i-deploy-candy.svg" width="32%" alt="Theme candy">
  <img src="examples/themes/img/themes-can-i-deploy-blueprint.svg" width="32%" alt="Theme blueprint">
  <img src="examples/themes/img/themes-can-i-deploy-chalk.svg" width="32%" alt="Theme chalk">
</p>

## Examples

| Explanation | Language | Diagrams |
| --- | --- | --- |
| [How does my browser find a website?](examples/dns/how-dns-works.md) | English | Tree, sequence, stack, cycle |
| [Por que o git rebase “reescreve a história”?](examples/git-rebase/git-rebase-pt-br.md) | Português | Timeline, compare, flow |
| [Doodle themes](examples/themes/themes.md) | English | The same flow in all five themes |

<p align="center">
  <img src="examples/git-rebase/img/git-rebase-pt-br-merge-ou-rebase.svg" alt="Merge and rebase compared side by side">
</p>

## Run without an agent

From a Bash-compatible terminal, clone the repository and render a small example:

```bash
git clone https://github.com/santunesigor/doodle.git
cd doodle
printf '%s\n' 'stack: Hello' 'Browser | info' 'Server | ok' > demo.txt
python3 skills/doodle/scripts/doodle.py demo.txt
```

Open the generated `demo.svg` in your browser. Add `--theme chalk` to try another look, or see the
[tutorial](docs/tutorial.md#5-write-your-own-diagrams) for all nine types.

For a Markdown file containing `doodle` blocks, run `python3 skills/doodle/scripts/doodle.py notes.md` from the repository root.
This **updates `notes.md` in place**. The original specs remain in HTML comments, so you can edit and render again.
To keep images somewhere else, set `"imageDir": "assets/diagrams"` in `doodle.json` (or pass `-o assets/diagrams` on every run).
In Markdown mode, diagram specs and SVG output paths are checked before writing files; `--check` validates and lints
without writing anything.

## Repository layout

```text
skills/doodle/
  SKILL.md           Agent instructions and activation cues
  agents/            Codex display metadata
  scripts/           Dependency-free Python renderer
  references/        Diagram syntax and customization
examples/            Illustrated explanations and their SVGs
docs/                English and Portuguese tutorials
tests/               Parser, renderer, and Markdown regression tests
```

## Contributing

Bug reports, clearer examples, and focused improvements are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup
and what to include in a pull request. You can contribute in English or Portuguese.

```bash
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE).
