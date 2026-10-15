# Contributing to Doodle

Contributions in English or Portuguese are welcome: bug reports, teaching examples, diagram layout fixes, and clearer docs.

## Local setup

Python 3.8+ is enough. There are no packages to install.

```bash
git clone https://github.com/santunesigor/doodle.git
cd doodle
python3 -m unittest discover -s tests -v
```

To try the skill in your agent without copying it, follow the local installation instructions in the
[English](docs/tutorial.md#1-install) or [Portuguese](docs/tutorial.pt-BR.md#1-instalar) tutorial.

## What lives where

| Change | Location |
| --- | --- |
| Agent workflow and activation cues | `skills/doodle/SKILL.md` |
| Codex display metadata | `skills/doodle/agents/openai.yaml` |
| Parser, layout, SVG output, Markdown handling | `skills/doodle/scripts/doodle.py` |
| Syntax and options | `skills/doodle/references/dsl.md` |
| Themes and `doodle.json` settings | `THEMES` and `DEFAULTS` in `doodle.py`, documented in `skills/doodle/references/customize.md` |
| Regression tests | `tests/test_doodle.py` |
| Finished explanations | `examples/<topic>/` with images in `img/` |
| User documentation | `README*.md` and `docs/tutorial*.md` |

## Reporting a bug

Include the smallest diagram spec or Markdown file that reproduces it, the command you ran, your Python version, and
what you expected. For a layout issue, include a screenshot and the editor or browser you used. Remove private project
information before sharing examples.

## Sending a pull request

Keep changes focused. Preserve the renderer's Python 3.8 compatibility and standard-library-only runtime.
Add a regression test for a parser or rendering bug; for visual changes, include a before/after preview.
A new theme needs light and dark palettes (or `dark=None` for a fixed look), a row in `customize.md`, and a section in
`examples/themes/themes.md`; the tests check that the docs list every theme, kind and setting.
Keep English and Portuguese user docs aligned when changing installation or usage.

Before submitting:

```bash
python3 -m unittest discover -s tests -v
python3 skills/doodle/scripts/doodle.py --check examples/dns/how-dns-works.md
git diff --check
```

When changing examples, render a temporary copy first, then include the Markdown source comments and the resulting SVGs.
The renderer updates Markdown in place. If you use a custom image directory, pass the same `-o` option on subsequent runs.

Use a descriptive commit message, such as `fix: preserve unfinished diagram blocks` or `docs: clarify Codex installation`.
Describe the resulting behavior and how you checked it in the pull request.
