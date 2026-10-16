# Doodle DSL reference

Every block has the same shape:

```
kind: Title                  <- required first line
> Subtitle line               <- optional, any number
@option @option              <- optional
row                          <- the content, one per line
// comment                   <- ignored
```

A **row** is `label | note | tone`.

- `label` is bold and required.
- `note` is optional, muted, and wraps automatically.
- `tone` is optional and must be the **last** cell. It accepts `neutral`, `info`, `ok`, `bad` or `warn`.
  Aliases also work: `good`/`success`/`green` → ok; `error`/`fail`/`red` → bad; `warning`/`yellow` → warn; `blue` → info.
  So a last cell that is literally a tone word, like `Status | ok`, becomes the tone and not the note.
- Write `\n` inside a label or note to force a line break.

**Options:**

| option | effect |
|---|---|
| `@sketch` | hand-drawn look: wobbly shapes, handwriting font when available |
| `@vertical` / `@horizontal` | force the direction of `timeline` and `flow` (the default is automatic) |
| `@arrow` | arrows between `compare` columns, between `stack` layers, and from a `hub` center outward |
| `@theme NAME` | draw this one diagram in another theme: `paper`, `clean`, `candy`, `blueprint`, `chalk` |

The theme, colors and light/dark behavior of a whole document come from `doodle.json`; see
[customize.md](customize.md).

The renderer warns (it doesn't fail) about unknown options, misspelled tones, flow edges that match no node,
and text that is too long. Run `doodle.py --check FILE.md` to see those warnings without writing anything.

SVGs include a dark palette through `prefers-color-scheme`. It activates in viewers that support this media query;
other viewers may show the light palette.

---

## timeline

The rows are events, in order. They get numbers 1, 2, 3… on an axis. With more than 5 rows the timeline turns vertical.

```doodle
timeline: A request's life
DNS lookup | find the server's address | info
TCP + TLS | open a safe connection
Request | GET /index.html
Response | 200 OK + HTML | ok
```

## flow

There are two ways to write a flow.

**A chain**, where you write only rows and they connect in that order. Short flows are horizontal by default;
add `@vertical` to draw them from top to bottom:

```doodle
flow: Build pipeline
Commit
Tests | 2 min | info
Deploy | ok
```

**A graph**, where you write rows and then edges:

```doodle
flow: Login
[a] Open app
[b] Has token? | warn
[c] Home | ok
[d] Login screen
a -> b
b -> c: yes
b -> d: no
d -> b: after login | info
```

- An edge looks like `from -> to: label | tone`. Use `~>` for a dashed edge.
- An endpoint can be a bare ID (`a` for a node declared as `[a] Label`), a 1-based row number, or the exact label
  (case-insensitive). Use brackets only in node declarations, not in edges.
  An endpoint that matches nothing creates a new node, so `A -> B` works with no rows at all.
- An edge that goes back (a loop) is drawn as a curve around the diagram.
- With more than 4 levels the flow turns vertical.

## cycle

Use at least two rows. With three or more, rows go clockwise around a circle, starting at the top, and the last row
connects back to the first. A two-row cycle is drawn side by side with a return arrow.

```doodle
cycle: The code review loop
Write code | info
Open a pull request
Review asks for changes | warn
Fix and push | ok
```

## compare

`## Header | note | tone` starts a column. The rows below it are its items, each with a ✓ ✗ ! i • icon from its tone.
An item with no tone, or with `neutral`, takes the column's tone.
The layout works best with 2–3 columns.

```doodle
compare: Merge vs rebase
@arrow
## Merge | keeps history as it happened | info
May add merge commit | warn
Safe on shared branches | ok
## Rebase | rewrites history in a line | info
Linear history | ok
Avoid rewriting shared commits | bad
```

## tree

Each 2-space indent is one level. Nodes that have children get a folder icon, and the others get a file icon.
The note appears to the right of the node.

```doodle
tree: Project layout
src/
  main.py | entry point | info
  utils/
    dates.py | the bug lives here | bad
tests/
```

## stack

The rows are drawn as horizontal layers, from top to bottom. Add `@arrow` to link them.

```doodle
stack: Where a DNS answer can come from
@arrow
Browser cache | seconds to minutes | ok
OS cache
Router
ISP resolver | asks the root servers if needed | info
```

## sequence

`A -> B: message | tone` draws a solid arrow, `~>` draws a dashed reply, and `A -> A` draws a message to itself.
Actors appear in the order of first use, and you can declare them first as plain rows to set the order or a tone.
The messages are numbered automatically.

```doodle
sequence: TLS handshake (simplified)
Browser | info
Server
Browser -> Server: hello, here are my ciphers
Server ~> Browser: certificate + chosen cipher
Browser -> Browser: check certificate | warn
Browser -> Server: key exchange
Server ~> Browser: encrypted from now on | ok
```

## bars

Use it when the point is a **quantity**: time, size, count, cost. Each row's note holds the number, plus any unit you
want to show. Bars are scaled against the largest one. `1,200`, `2.5` and `1,5` are all read as numbers.

```doodle
bars: Where a page load spends its time
> one visit, in milliseconds
DNS lookup | 120 ms | warn
TLS handshake | 80 ms
Server work | 410 ms | bad
Render | 60 ms | ok
```

## hub

The first row is the center; every other row is drawn around it. Use it for "what is this made of?" or for the
pieces of a concept. A neutral center is drawn as `info`. Add `@arrow` for arrows that point outward.

```doodle
hub: What a URL is made of
URL | the full address | info
Scheme | https://
Host | www.example.com | ok
Path | /docs/page
Query | ?lang=pt | warn
```

---

## Tips

- Pick the kind by the question: "in what order?" → `timeline`; "what decides what?" → `flow`;
  "why does it keep happening?" → `cycle`; "what changed?" → `compare`; "where is it?" → `tree`;
  "what sits on top of what?" → `stack`; "who talks to whom?" → `sequence`; "how much?" → `bars`;
  "what is it made of?" → `hub`.
- Use tones to tell the story: `bad` is the broken part, `ok` is the fix or the healthy path, `warn` is the risky
  step, and `info` is the actor or the input.
- Don't use `-->` anywhere; use `~>` for dashed arrows.
