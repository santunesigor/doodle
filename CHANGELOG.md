# Changelog

## 0.2.0

### Make it yours

- **Themes:** `paper` (default), `clean`, `candy`, `blueprint` and `chalk`. Choose one per project, per run
  (`--theme`) or per diagram (`@theme`).
- **`doodle.json` settings**, merged from `~/.config/doodle/config.json` and the nearest project file: theme, sketch,
  light/dark scheme, frame, font, brand colors (dark versions derived automatically) and image folder.
- **The writing adapts too:** `audience` (`kid`, `beginner`, `developer`, `expert`), `depth` (`quick`, `standard`,
  `deep`), `language`, `docsDir` and free-text `notes`. The agent saves lasting preferences for you.
- New commands: `--init`, `--settings`, `--themes`, `--scheme`, `--sketch`, `--config`.

### Better diagrams

- Two new kinds: `bars` for numbers and `hub` for "what is it made of?".
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
