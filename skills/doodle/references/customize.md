# Customizing Doodle

Everything is optional. With no settings, Doodle writes for beginners, in the user's language, with the `paper` theme.

## Where settings live

Doodle merges up to two JSON files, later ones winning:

1. `~/.config/doodle/config.json` (or `$XDG_CONFIG_HOME/doodle/config.json`): your defaults everywhere.
2. `doodle.json`: the nearest one found from the document's folder upward, stopping at the repository root.

Command-line flags (`--theme`, `--sketch`, `--scheme`) win over both, and `@theme` / `@sketch` inside a block win
over everything for that one diagram. `--config PATH` uses one specific file instead of searching.

```bash
doodle.py --init        # write a starter doodle.json in the current folder
doodle.py --settings    # print the merged settings and which files they came from
doodle.py --themes      # list the themes
```

## All settings

| key | values | default | used by |
|---|---|---|---|
| `theme` | `paper`, `clean`, `candy`, `blueprint`, `chalk` | `paper` | renderer |
| `sketch` | `true` / `false` (unset: the theme decides; `chalk` is hand-drawn) | unset | renderer |
| `scheme` | `auto` (follow the viewer), `light`, `dark` | `auto` | renderer |
| `frame` | `false` drops the background card, for pasting into slides | `true` | renderer |
| `font` | a CSS `font-family` list | the theme's | renderer |
| `colors` | `{"info": "#7c3aed", "bg": "#ffffff", ...}` | `{}` | renderer |
| `darkColors` | same keys, for the dark palette only | `{}` | renderer |
| `imageDir` | folder for SVGs, relative to the document | `img` | renderer |
| `audience` | `kid`, `beginner`, `developer`, `expert` | `beginner` | agent |
| `depth` | `quick`, `standard`, `deep` | `standard` | agent |
| `language` | `auto` (the user's language) or a language name such as `pt-BR` | `auto` | agent |
| `docsDir` | folder for new explanations, relative to the project root | current folder | agent |
| `notes` | free-text house rules for the writer | `""` | agent |

Unknown keys produce a warning with a suggestion, so typos don't fail silently.

## Themes

| theme | look | good for |
|---|---|---|
| `paper` | warm off-white, soft shadows, rounded font | the default; READMEs and docs |
| `clean` | white, thin lines, no shadows, neutral sans font | product docs, slides, print |
| `candy` | pastel colors, very round shapes | kids, workshops, friendly onboarding |
| `blueprint` | white lines on blue with a grid, monospace | architecture and infrastructure |
| `chalk` | chalk on a green board, hand-drawn | classes and talks |

`paper`, `clean` and `candy` have light and dark palettes and follow the viewer's mode. `blueprint` and `chalk`
look the same everywhere.

## Colors

`colors` takes the five tones (`neutral`, `info`, `ok`, `bad`, `warn`; aliases like `red` or `error` also work) and
the base colors `bg` (background), `line` (guides), `ink` (text), `mut` (notes), `edge` (arrows) and `on` (text on a
filled badge). Give each tone one strong color; Doodle derives the light card fill from it and a lighter version for
dark mode. Use `darkColors` only to pick the dark versions yourself.

## Examples

A team of senior engineers that wants plain, brand-colored diagrams in `docs/explain`:

```json
{
  "theme": "clean",
  "colors": {"info": "#6d28d9"},
  "audience": "developer",
  "docsDir": "docs/explain",
  "notes": "Link to files as path:line. Mention the related runbook when there is one."
}
```

A teacher preparing a class for 10-year-olds, in Portuguese:

```json
{
  "theme": "candy",
  "audience": "kid",
  "depth": "quick",
  "language": "pt-BR",
  "notes": "Use school and soccer metaphors."
}
```

Diagrams for dark slides, without the background card:

```json
{"theme": "clean", "scheme": "dark", "frame": false}
```
