# Changelog

## Unreleased

- New explanations go to a `doodle/` folder at the repository root by default (`docsDir`), and rendering one adds
  `/doodle/` to the repository's `.gitignore`. Set `"gitignore": false` to commit them, or `"docsDir": ""` for the
  old behavior (the current folder). `--settings` now prints the repository `root`.

## 0.2.0

### Make it yours

- **Themes:** `paper` (default), `clean`, `candy`, `blueprint` and `chalk`. Choose one per project, per run
  (`--theme`) or per diagram (`@theme`).
- **`doodle.json` settings**, merged from `~/.config/doodle/config.json` and every project file from the repository
  root down (subfolders override only what they name): theme, sketch, light/dark scheme, frame, font, brand colors
  (dark versions derived automatically) and image folder. A JSON schema gives editors autocomplete.
- **The writing adapts too:** `audience` (`kid`, `beginner`, `developer`, `expert`), `depth` (`quick`, `standard`,
  `deep`), `language`, `docsDir` and free-text `notes`. The agent saves lasting preferences for you.
- New commands: `--init`, `--settings`, `--themes`, `--scheme`, `--sketch`, `--config`.

### Better diagrams

- Two new kinds: `bars` for numbers and `hub` for "what is it made of?".
- `@sketch` is now really hand-drawn: double-traced wobbly outlines, fills that miss the line, bowed arrows.
  The wobble is deterministic, so re-rendering doesn't churn git diffs.
- Flow edge labels sit beside the curve instead of on it.
- Badge numbers keep their contrast in dark mode.
- Every SVG has a `<desc>` with its content, for screen readers.

### Better feedback

- Lint warnings with document line numbers: unknown options, misspelled tones, flow edges that match no node,
  probable actor typos, text that is too long, diagrams that are too big.
- `--check` validates without writing; errors in Markdown files point at the document line.
- Unchanged SVG and Markdown files are no longer rewritten.

## 0.1.0

- First release: seven diagram kinds, Markdown mode, light and dark palettes, `@sketch`.
