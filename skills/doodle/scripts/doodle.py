#!/usr/bin/env python3
"""doodle - turn tiny text specs into friendly SVG diagrams. Python 3.8+, stdlib only.

Usage:
  doodle.py FILE.md [-o IMG_DIR]   render every ```doodle block in FILE.md to an SVG
                                   and swap the block for an image link (re-runnable)
  doodle.py SPEC.txt [-o OUT.svg]  render a single spec file
  doodle.py -                      read one spec from stdin, write the SVG to stdout

Look and settings:
  --theme NAME                     paper | clean | candy | blueprint | chalk (see --themes)
  --sketch                         hand-drawn look for every diagram
  --scheme auto|light|dark         auto follows the viewer's light/dark mode
  --config PATH                    use this doodle.json instead of searching for one
  --settings                       print the effective settings (doodle.json files merged)
  --init                           create a starter doodle.json in the current folder
  --check                          validate and lint without writing any file

Spec format (see references/dsl.md):
  kind: Title                  kind = flow | cycle | timeline | compare | tree | stack | sequence
                                      | bars | hub
  > optional subtitle
  @sketch @vertical            options; @theme NAME changes the theme of one diagram
  label | note | tone          tone = neutral | info | ok | bad | warn
"""
import argparse
import json
import math
import os
import re
import sys
import unicodedata

KINDS = ("flow", "cycle", "timeline", "compare", "tree", "stack", "sequence", "bars", "hub")
TONES = ("neutral", "info", "ok", "bad", "warn")
ALIAS = {  # only words unlikely to be a real note
    "good": "ok", "success": "ok", "green": "ok",
    "error": "bad", "fail": "bad", "danger": "bad", "red": "bad",
    "warning": "warn", "caution": "warn", "yellow": "warn",
    "blue": "info", "gray": "neutral", "grey": "neutral",
}
ICON = {"ok": "✓", "bad": "✗", "warn": "!", "info": "i", "neutral": "•"}

PAD = 28          # canvas padding
TS, NS = 15, 13   # title / note font sizes
LT, LN = 20, 18   # title / note line heights
PX, PY = 14, 12   # card padding


class DoodleError(Exception):
    pass


# ---------------------------------------------------------------- parsing

class Spec:
    def __init__(self):
        self.kind = ""
        self.title = ""
        self.sub = []
        self.opts = set()
        self.theme = None  # set by '@theme NAME'
        self.rows = []  # (line number, raw line without trailing spaces)
        self.warnings = []  # (line number or None, message)
        self.opt_lines = {}  # option -> line where it was written


def tone_of(word):
    w = word.strip().lower()
    return w if w in TONES else ALIAS.get(w)


def parse(src):
    spec = Spec()
    for no, raw in enumerate(src.splitlines(), 1):
        line = raw.rstrip()
        st = line.strip()
        if not st or st.startswith("//"):
            continue
        if not spec.kind:
            kind, _, title = st.partition(":")
            kind = kind.strip().lower()
            if kind not in KINDS:
                raise DoodleError("line %d: unknown kind '%s' (use one of: %s)" % (no, kind, ", ".join(KINDS)))
            spec.kind, spec.title = kind, title.strip()
        elif st.startswith("@"):
            words = re.split(r"[\s=]+", st)
            for i, w in enumerate(words):
                w = w.lstrip("@").lower()
                if w == "theme" and i + 1 < len(words):
                    spec.theme = words[i + 1].lstrip("@").lower()
                elif w and not (i and words[i - 1].lower() == "@theme"):
                    spec.opts.add(w)
                    spec.opt_lines.setdefault(w, no)
        elif st == ">" or st.startswith("> "):
            spec.sub.append(st[1:].strip())
        else:
            spec.rows.append((no, line))
    if not spec.kind:
        raise DoodleError("empty spec: the first line must be 'kind: Title'")
    lint(spec)
    return spec


OPTIONS = {"sketch": KINDS, "vertical": ("timeline", "flow"), "horizontal": ("timeline", "flow"),
           "arrow": ("compare", "stack", "hub")}
MAX_ROWS = {"sequence": 12, "flow": 14, "compare": 12, "tree": 14, "bars": 12}  # others: 8


def lint(spec):
    """Warnings for things that render but probably aren't what the author meant."""
    warn = spec.warnings.append
    for opt, no in sorted(spec.opt_lines.items(), key=lambda kv: kv[1]):
        if opt not in OPTIONS:
            warn((no, "unknown option '@%s'%s; options: %s, @theme NAME"
                  % (opt, suggest(opt, OPTIONS), ", ".join("@" + o for o in OPTIONS))))
        elif spec.kind not in OPTIONS[opt]:
            warn((no, "'@%s' has no effect on %s" % (opt, spec.kind)))
    if not spec.title:
        warn((None, "no title; write 'kind: Title' so the image has alt text"))
    rows = [r for r in spec.rows if not r[1].strip().startswith("##")]
    if len(rows) > MAX_ROWS.get(spec.kind, 8):
        warn((rows[0][0], "%d rows is a lot for one %s; consider splitting it into two diagrams"
              % (len(rows), spec.kind)))
    vocabulary = list(TONES) + list(ALIAS)
    for no, line in spec.rows:
        text = line.strip().lstrip("#").strip()
        edge = split_edge(text) if spec.kind in ("flow", "sequence") else None
        cellsrc = EDGE.match(text).group(3).partition(":")[2] if edge else text
        parts = [p.strip() for p in cellsrc.split("|")]
        if len(parts) > 1:
            last = parts[-1].lower()
            if not tone_of(last) and re.fullmatch(r"[a-z]{2,9}", last) and suggest(last, vocabulary):
                warn((no, "'%s' is shown as a note; if it is a tone, write %s" % (
                    parts[-1], suggest(last, vocabulary).split("'")[1])))
        if edge:
            words = len(edge[3].split())
            if words > 10:
                warn((no, "message has %d words; aim for 8 or fewer" % words))
            continue
        label, note, _tone = cells(re.sub(r"^\[[^\]]+\]\s*", "", text))
        if len(label.split()) > 6:
            warn((no, "label has %d words; aim for 4 or fewer (put details in the note)" % len(label.split())))
        if len(note.split()) > 16:
            warn((no, "note has %d words; aim for 12 or fewer" % len(note.split())))


def cells(text):
    """'label | note | tone' -> (label, note, tone). Note and tone are optional."""
    parts = [p.strip() for p in text.split("|")]
    tone = "neutral"
    if len(parts) > 1 and tone_of(parts[-1]):
        tone = tone_of(parts.pop())
    label = parts[0].replace("\\n", "\n")
    note = " | ".join(parts[1:]).replace("\\n", "\n")
    return label, note, tone


EDGE = re.compile(r"^(.+?)\s*(->|~>)\s*(.+?)$")


def split_edge(text):
    """'A -> B: label | tone' -> (A, B, dashed, label, tone) or None."""
    m = EDGE.match(text.strip())
    if not m:
        return None
    a, arrow, rest = m.group(1).strip(), m.group(2), m.group(3)
    b, _, lab = rest.partition(":")
    label, _, tone = cells(lab) if lab.strip() else ("", "", "neutral")
    return a, b.strip(), arrow == "~>", label, tone


# ---------------------------------------------------------------- text metrics

NARROW = set("iljtfrI.,;:!|'`()[]{} ")
WIDE = set("MWmw@%&")


def tw(s, size, bold=False, sketch=False, mono=False):
    """Rough rendered width of s in px (no font metrics in the stdlib)."""
    if mono:
        return sum(1.2 if ord(ch) >= 0x2E80 else 0.61 for ch in s) * size
    w = 0.0
    for ch in s:
        if ch in NARROW:
            w += 0.31
        elif ch in WIDE:
            w += 0.86
        elif ord(ch) >= 0x2E80:
            w += 1.15
        elif ch.isupper() or ch.isdigit():
            w += 0.64
        else:
            w += 0.54
    return w * size * (1.06 if bold else 1.0) * (1.1 if sketch else 1.0)


def wrap(text, size, maxw, bold=False, sketch=False, mono=False):
    out = []
    for para in str(text).split("\n"):
        line = ""
        for word in para.split():
            while tw(word, size, bold, sketch, mono) > maxw and len(word) > 1:
                if line:
                    out.append(line)
                    line = ""
                cut = len(word) - 1
                while cut > 1 and tw(word[:cut], size, bold, sketch, mono) > maxw:
                    cut -= 1
                out.append(word[:cut])
                word = word[cut:]
            cand = line + " " + word if line else word
            if not line or tw(cand, size, bold, sketch, mono) <= maxw:
                line = cand
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def f(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


# ---------------------------------------------------------------- canvas & theme

FONT = ('ui-rounded,"SF Pro Rounded","Nunito","Segoe UI",system-ui,-apple-system,'
        'Roboto,"Helvetica Neue",Arial,sans-serif')
FONT_SANS = ('"Inter","Segoe UI",system-ui,-apple-system,Roboto,"Helvetica Neue",Arial,sans-serif')
FONT_MONO = ('ui-monospace,"SF Mono","JetBrains Mono","Cascadia Code",Menlo,Consolas,"DejaVu Sans Mono",'
             'monospace')
FONT_SKETCH = ('"Comic Neue","Comic Sans MS","Chalkboard SE","Segoe Print",'
               '"Bradley Hand",ui-rounded,sans-serif')

HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
BASE_KEYS = ("bg", "line", "ink", "mut", "edge", "on")  # on = text drawn on a filled badge


def rgb(c):
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]


def mix(a, b, t):
    """t of color a blended over color b."""
    return "#" + "".join("%02x" % round(x * t + y * (1 - t)) for x, y in zip(rgb(a), rgb(b)))


def pal(bg, line, ink, mut, edge, on, fill, **strokes):
    """A palette whose card fills are a light wash (fill) of each tone's stroke color over bg."""
    p = dict(bg=bg, line=line, ink=ink, mut=mut, edge=edge, on=on)
    for t in TONES:
        p[t] = (mix(strokes[t], bg, fill), strokes[t])
    return p


PAPER_LIGHT = dict(bg="#fffdf9", line="#ebe5da", ink="#1f2933", mut="#5f6b7a", edge="#7b8794", on="#ffffff",
                   neutral=("#f4f1ea", "#8a8174"), info=("#e8f1fc", "#3a78c2"), ok=("#e7f6eb", "#2f8a4b"),
                   bad=("#fdecea", "#c8423b"), warn=("#fff5df", "#c38410"))
PAPER_DARK = dict(bg="#14181d", line="#2a3038", ink="#e6e9ed", mut="#a2acb8", edge="#8d98a5", on="#14181d",
                  neutral=("#23272e", "#8b949e"), info=("#132a43", "#6aa8ec"), ok=("#12301d", "#5cc184"),
                  bad=("#3b1716", "#f07c74"), warn=("#3a2c0c", "#f0b543"))

THEMES = {
    "paper": dict(about="warm paper, soft shadows, rounded font (the default)",
                  light=PAPER_LIGHT, dark=PAPER_DARK, font=FONT, radius=12, shadow=True),
    "clean": dict(about="crisp white, thin lines, no shadows: good for docs and slides",
                  light=pal("#ffffff", "#e5e7eb", "#111827", "#6b7280", "#9ca3af", "#ffffff", .08,
                            neutral="#9ca3af", info="#2563eb", ok="#059669", bad="#dc2626", warn="#d97706"),
                  dark=pal("#0d1117", "#21262d", "#e6edf3", "#8b949e", "#6e7681", "#0d1117", .16,
                           neutral="#6e7681", info="#58a6ff", ok="#3fb950", bad="#f85149", warn="#d29922"),
                  font=FONT_SANS, radius=7, shadow=False),
    "candy": dict(about="playful pastels and round shapes: good for kids and workshops",
                  light=pal("#fff7fb", "#f7dcea", "#3b2a4a", "#7d6b8f", "#b49acb", "#ffffff", .13,
                            neutral="#a996c8", info="#3d8ef0", ok="#16a874", bad="#ef4b6c", warn="#ee9a12"),
                  dark=pal("#1d1724", "#33293f", "#f6eefc", "#b9a8cc", "#8f7aa8", "#1d1724", .2,
                           neutral="#a996c8", info="#7ab4ff", ok="#4fd6a0", bad="#ff7d96", warn="#ffc04d"),
                  font=FONT, radius=20, shadow=True),
    "blueprint": dict(about="white lines on blueprint blue with a grid, monospace (same in light and dark)",
                      light=pal("#1b4b85", "#2f65a3", "#f3f8ff", "#c0d6f2", "#dce9ff", "#1b4b85", .14,
                                neutral="#dce9ff", info="#8fd3ff", ok="#9ff0b8", bad="#ffa3a3", warn="#ffdb8a"),
                      dark=None, font=FONT_MONO, radius=3, shadow=False, grid=True),
    "chalk": dict(about="chalk on a green board, hand-drawn (same in light and dark)",
                  light=pal("#243329", "#3a4d40", "#f5f2e9", "#c7cec3", "#ece7da", "#243329", .1,
                            neutral="#ece7da", info="#a6d4ff", ok="#bdeba6", bad="#ffa59a", warn="#ffe38f"),
                  dark=None, font=FONT_SKETCH, radius=10, shadow=False, sketch=True),
}
SCHEMES = ("auto", "light", "dark")


def suggest(word, options, cutoff=0.6):
    import difflib
    close = difflib.get_close_matches(word, list(options), 1, cutoff)
    return " (did you mean '%s'?)" % close[0] if close else ""


def color_overrides(colors, where):
    out = {}
    for k, v in (colors or {}).items():
        key = tone_of(k) or k
        if key not in TONES and key not in BASE_KEYS:
            raise DoodleError("%s: unknown color '%s' (use %s)" % (where, k, ", ".join(BASE_KEYS + TONES)))
        if not isinstance(v, str) or not HEX.match(v):
            raise DoodleError("%s: color '%s' must look like #3a78c2, got %r" % (where, k, v))
        out[key] = v.lower()
    return out


class Style:
    """Everything about the look: theme palettes, font, shapes, and the user's color overrides."""

    def __init__(self, theme="paper", sketch=None, scheme="auto", frame=True, font="",
                 colors=None, dark_colors=None):
        theme = (theme or "paper").lower()
        if theme not in THEMES:
            raise DoodleError("unknown theme '%s'%s; themes: %s" % (theme, suggest(theme, THEMES), ", ".join(THEMES)))
        if scheme not in SCHEMES:
            raise DoodleError("unknown scheme '%s' (use auto, light or dark)" % scheme)
        self.args = dict(theme=theme, sketch=sketch, scheme=scheme, frame=frame, font=font,
                         colors=colors, dark_colors=dark_colors)
        t = THEMES[theme]
        self.theme, self.scheme, self.frame = theme, scheme, frame
        self.sketch = bool(t.get("sketch")) if sketch is None else bool(sketch)
        self.font = font or (FONT_SKETCH if self.sketch and t["font"] == FONT else t["font"])
        self.mono = "monospace" in self.font and not self.sketch
        self.radius, self.shadow, self.grid = t["radius"], t["shadow"], t.get("grid", False)
        light = dict(t["light"])
        dark = dict(t["dark"]) if t["dark"] else None
        lc = color_overrides(colors, "colors")
        dc = color_overrides(dark_colors, "darkColors")
        for k, v in lc.items():
            light[k] = (mix(v, light["bg"], .12), v) if k in TONES else v
            if dark and k in TONES and k not in dc:  # a brand color still needs to work at night
                s = mix(v, "#ffffff", .7)
                dark[k] = (mix(s, dark["bg"], .2), s)
        for k, v in dc.items():
            if dark:
                dark[k] = (mix(v, dark["bg"], .2), v) if k in TONES else v
        self.light, self.dark = light, dark

    def variant(self, **changes):
        args = dict(self.args)
        args.update({k: v for k, v in changes.items() if v is not None})
        return Style(**args)

    @staticmethod
    def palette_vars(p):
        v = ["--%s:%s" % (k, p[k]) for k in BASE_KEYS]
        for t in TONES:
            v.append("--%s1:%s;--%s2:%s" % (t, p[t][0], t, p[t][1]))
        return ";".join(v)

    def css(self):
        tones = "".join(
            ".c-{t}{{fill:var(--{t}1);stroke:var(--{t}2)}}.f-{t}{{fill:var(--{t}2)}}"
            ".s-{t}{{stroke:var(--{t}2)}}.x-{t}{{fill:var(--{t}2)}}".format(t=t) for t in TONES)
        if self.scheme == "dark" and self.dark:
            colors = "svg{%s}" % self.palette_vars(self.dark)
        elif self.scheme == "auto" and self.dark:
            colors = "svg{%s}@media (prefers-color-scheme:dark){svg{%s}}" % (
                self.palette_vars(self.light), self.palette_vars(self.dark))
        else:
            colors = "svg{%s}" % self.palette_vars(self.light)
        return (
            "%s"
            "text{font-family:%s;fill:var(--ink)}"
            ".bg{fill:var(--bg);stroke:var(--line)}.grid{fill:url(#grid)}"
            ".h{font-size:20px;font-weight:700}.sub{font-size:13px;fill:var(--mut)}"
            ".t{font-size:%dpx;font-weight:650}.n{font-size:%dpx;fill:var(--mut)}"
            ".card{stroke-width:1.6}.w{fill:var(--on);font-size:12px;font-weight:700}"
            ".e{fill:none;stroke:var(--edge);stroke-width:1.8;stroke-linecap:round}"
            ".d{stroke-dasharray:6 5}.ah{fill:var(--edge)}.ln{stroke:var(--line);stroke-width:2;fill:none}"
            ".el{font-size:12.5px;fill:var(--mut);paint-order:stroke;stroke:var(--bg);"
            "stroke-width:5px;stroke-linejoin:round}"
            ".big{font-size:64px;fill:var(--line)}%s"
        ) % (colors, self.font.replace('"', "'"), TS, NS, tones)


DEFAULT_STYLE = None


def default_style():
    global DEFAULT_STYLE
    if DEFAULT_STYLE is None:
        DEFAULT_STYLE = Style()
    return DEFAULT_STYLE


def css(sketch):
    """CSS of the default theme (kept for callers of older versions)."""
    return default_style().variant(sketch=sketch).css()


class Canvas:
    def __init__(self, spec, style=None):
        self.spec = spec
        style = style or default_style()
        if spec.theme or "sketch" in spec.opts:
            style = style.variant(theme=spec.theme, sketch=True if "sketch" in spec.opts else None)
        self.style = style
        self.sketch, self.mono = style.sketch, style.mono
        self.r = style.radius
        self.fx = ' filter="url(#sh)"' if style.shadow else ""
        self.parts = []
        self.top = PAD
        if spec.title:
            self.top += 26
        self.top += 19 * len(spec.sub)
        if spec.title or spec.sub:
            self.top += 18

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, cls, mid=False, end=False):
        anchor = ' text-anchor="middle"' if mid else ' text-anchor="end"' if end else ""
        self.add('<text x="%s" y="%s" class="%s"%s>%s</text>' % (f(x), f(y), cls, anchor, esc(s)))

    def box(self, x, y, w, h, tone, r=None, extra=""):
        """A tone-colored rounded rectangle (the shape behind every card)."""
        self.add('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" class="card c-%s"%s%s/>'
                 % (f(x), f(y), f(w), f(h), f(self.r if r is None else r), tone, self.fx, extra))

    def wrap(self, text, size, maxw, bold=False):
        return wrap(text, size, maxw, bold, self.sketch, self.mono)

    def tw(self, s, size, bold=False):
        return tw(s, size, bold, self.sketch, self.mono)

    def arrow(self, d, dashed=False, tone=None):
        cls = "e" + (" d" if dashed else "") + (" s-" + tone if tone and tone != "neutral" else "")
        self.add('<path d="%s" class="%s" marker-end="url(#ah)"/>' % (d, cls))

    def label(self, x, y, s, maxw=170, up=False):
        """Edge label centered on x; with up=True extra lines grow upward from y."""
        lines = self.wrap(s, 12.5, maxw)
        y -= (len(lines) - 1) * 16 if up else 0
        for i, line in enumerate(lines):
            self.text(x, y + i * 16, line, "el", mid=True)

    def badge(self, x, y, n, tone):
        self.add('<circle cx="%s" cy="%s" r="11" class="f-%s"/>' % (f(x), f(y), tone))
        self.text(x, y + 4, n, "w", mid=True)

    def render(self, w, h):
        spec, st, sk = self.spec, self.style, self.sketch
        head = []
        y = PAD + 8
        if spec.title:
            y += 12
            head.append('<text x="%d" y="%s" class="h">%s</text>' % (PAD, f(y), esc(spec.title)))
        for s in spec.sub:
            y += 19
            head.append('<text x="%d" y="%s" class="sub">%s</text>' % (PAD, f(y), esc(s)))
        w, h = math.ceil(w + PAD), math.ceil(h + PAD)
        defs = ""
        if sk:
            defs += ('<filter id="rough"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" '
                     'seed="7"/><feDisplacementMap in="SourceGraphic" scale="2.6"/></filter>')
        if st.shadow:
            defs += ('<filter id="sh" x="-10%" y="-10%" width="120%" height="140%"><feDropShadow dx="0" dy="1.5" '
                     'stdDeviation="1.6" flood-color="#000" flood-opacity=".10"/></filter>')
        frame = ""
        if st.frame:
            frame = '<rect x="1" y="1" width="%d" height="%d" rx="%s" class="bg"/>' % (w - 2, h - 2, f(st.radius + 4))
            if st.grid:
                defs += ('<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">'
                         '<path d="M20 0H0V20" fill="none" stroke="var(--line)" stroke-width=".7"/></pattern>')
                frame += '<rect x="1" y="1" width="%d" height="%d" rx="%s" class="grid"/>' % (
                    w - 2, h - 2, f(st.radius + 4))
        # shapes first, then all text on top, so the sketch filter never blurs letters
        shapes = "".join(p for p in self.parts if not p.startswith("<text"))
        texts = "".join(p for p in self.parts if p.startswith("<text"))
        body = ('<g filter="url(#rough)">%s</g>' % shapes if sk else shapes) + texts
        label = esc(spec.title or spec.kind)
        desc = esc(describe(spec))
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            'role="img" aria-label="{label}"><title>{label}</title><desc>{desc}</desc><style>{css}</style><defs>'
            '<marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ah"/></marker>'
            '{defs}</defs>{frame}{head}{body}</svg>\n'
        ).format(w=w, h=h, label=label, desc=desc, css=st.css(), defs=defs, frame=frame,
                 head="".join(head), body=body)


def describe(spec):
    """Plain-text summary of the rows for screen readers (the <desc> element)."""
    items = []
    for _, line in spec.rows:
        st = line.strip().lstrip("#-* ").replace("\\n", " ")
        st = re.sub(r"^\[[^\]]+\]\s*", "", st)
        parts = [p.strip() for p in st.split("|")]
        if len(parts) > 1 and tone_of(parts[-1]):
            parts.pop()
        items.append(" - ".join(p for p in parts if p).replace("~>", "->"))
    return "; ".join(items)


class Card:
    """A rounded box with a bold label and an optional muted note."""

    def __init__(self, cv, label, note, tone, w, mid=False):
        self.cv, self.tone, self.w, self.mid = cv, tone, w, mid
        inner = w - 2 * PX
        self.tl = cv.wrap(label, TS, inner, True) if label else []
        self.nl = cv.wrap(note, NS, inner) if note else []
        self.h = 2 * PY + len(self.tl) * LT + len(self.nl) * LN + (3 if self.tl and self.nl else 0) - 4
        self.x = self.y = 0.0

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    def place(self, x, y):
        self.x, self.y = x, y
        return self

    def draw(self):
        cv = self.cv
        cv.box(self.x, self.y, self.w, self.h, self.tone)
        tx = self.cx if self.mid else self.x + PX
        y = self.y + PY + TS - 2
        for line in self.tl:
            cv.text(tx, y, line, "t", self.mid)
            y += LT
        if self.tl:
            y += 3 - (LT - LN)
        for line in self.nl:
            cv.text(tx, y, line, "n", self.mid)
            y += LN

    def edge_point(self, tx, ty, gap=6):
        """Point on the card border toward (tx, ty)."""
        dx, dy = tx - self.cx, ty - self.cy
        if dx == 0 and dy == 0:
            return self.cx, self.cy
        sx = (self.w / 2 + gap) / abs(dx) if dx else float("inf")
        sy = (self.h / 2 + gap) / abs(dy) if dy else float("inf")
        s = min(sx, sy)
        return self.cx + dx * s, self.cy + dy * s


def rows_as_cards(cv, spec, w, mid=False):
    out = []
    for _, line in spec.rows:
        label, note, tone = cells(line.strip())
        out.append(Card(cv, label, note, tone, w, mid))
    if not out:
        raise DoodleError("'%s' needs at least one row" % spec.kind)
    return out


# ---------------------------------------------------------------- kinds

def draw_timeline(cv, spec):
    vertical = "vertical" in spec.opts or (len(spec.rows) > 5 and "horizontal" not in spec.opts)
    cards = rows_as_cards(cv, spec, 520 if vertical else 200)
    if vertical:
        x0, y = PAD + 20, cv.top + 6
        top = y
        for i, c in enumerate(cards):
            c.place(x0 + 34, y)
            y += c.h + 16
        cv.add('<path d="M%s %s V%s" class="ln"/>' % (f(x0), f(top + 6), f(y - 16)))
        for i, c in enumerate(cards):
            cv.add('<path d="M%s %s H%s" class="ln"/>' % (f(x0), f(c.y + 21), f(c.x)))
            c.draw()
            cv.badge(x0, c.y + 21, str(i + 1), c.tone)
        return x0 + 34 + 520, y - 16
    gap = 22
    axis = cv.top + 18
    x = PAD
    for c in cards:
        c.place(x, axis + 30)
        x += c.w + gap
    right = x - gap
    cv.add('<path d="M%s %s H%s" class="e" marker-end="url(#ah)"/>' % (f(PAD), f(axis), f(right + 14)))
    for i, c in enumerate(cards):
        cv.add('<path d="M%s %s V%s" class="ln"/>' % (f(c.cx), f(axis), f(c.y)))
        c.draw()
        cv.badge(c.cx, axis, str(i + 1), c.tone)
    return right + 16, max(c.y + c.h for c in cards)


def draw_stack(cv, spec):
    cards = rows_as_cards(cv, spec, 600)
    y = cv.top
    arrows = "arrow" in spec.opts
    for c in cards:
        c.place(PAD, y)
        c.draw()
        y += c.h + (26 if arrows else 8)
    if arrows:
        for a, b in zip(cards, cards[1:]):
            cv.arrow("M%s %s V%s" % (f(a.cx), f(a.y + a.h + 3), f(b.y - 3)))
    return PAD + 600, y - (26 if arrows else 8)


def draw_compare(cv, spec):
    cols = []
    for no, line in spec.rows:
        st = line.strip()
        if st.startswith("##"):
            label, note, tone = cells(st.lstrip("#").strip())
            cols.append({"label": label, "note": note, "tone": tone, "items": []})
        else:
            if not cols:
                cols.append({"label": "", "note": "", "tone": "neutral", "items": []})
            label, note, tone = cells(st.lstrip("-* ").strip())
            if tone == "neutral":  # items inherit the column's tone (and its icon)
                tone = cols[-1]["tone"]
            cols[-1]["items"].append((label, note, tone))
    if not cols:
        raise DoodleError("compare needs '## Column' headers followed by rows")
    n = len(cols)
    cw = {1: 560, 2: 330, 3: 250}.get(n, 210)
    arrow = "arrow" in spec.opts
    gap = 64 if arrow else 24
    iw = cw - 2 * PX - 26
    # measure
    for c in cols:
        hdr = cv.wrap(c["label"], 16, cw - 2 * PX, True) if c["label"] else []
        sub = cv.wrap(c["note"], NS, cw - 2 * PX) if c["note"] else []
        c["head"] = (hdr, sub)
        c["hh"] = (14 + len(hdr) * 21 + len(sub) * LN + 8) if (hdr or sub) else 6
        body = []
        for label, note, tone in c["items"]:
            tl = cv.wrap(label, 14, iw, True) if label else []
            nl = cv.wrap(note, NS, iw) if note else []
            body.append((tl, nl, tone, len(tl) * 19 + len(nl) * LN + 10))
        c["body"] = body
        c["h"] = c["hh"] + sum(b[3] for b in body) + 12
    H = max(c["h"] for c in cols)
    x = PAD
    for i, c in enumerate(cols):
        y0 = cv.top
        cv.box(x, y0, cw, H, c["tone"], cv.r + 2)
        y = y0 + 14
        hdr, sub = c["head"]
        for line in hdr:
            y += 16
            cv.add('<text x="%s" y="%s" class="t x-%s" style="font-size:16px">%s</text>'
                   % (f(x + PX), f(y), c["tone"], esc(line)))
            y += 5
        for line in sub:
            y += 14
            cv.text(x + PX, y, line, "n")
            y += 4
        if hdr or sub:
            y = y0 + c["hh"]
            cv.add('<path d="M%s %s H%s" class="ln s-%s" style="opacity:.35"/>'
                   % (f(x + PX), f(y - 4), f(x + cw - PX), c["tone"]))
        y += 6
        for tl, nl, tone, h in c["body"]:
            cv.add('<circle cx="%s" cy="%s" r="9" class="f-%s"/>' % (f(x + PX + 9), f(y + 10), tone))
            cv.text(x + PX + 9, y + 14, ICON[tone], "w", mid=True)
            ty = y + 15
            for line in tl:
                cv.add('<text x="%s" y="%s" class="t" style="font-size:14px">%s</text>'
                       % (f(x + PX + 26), f(ty), esc(line)))
                ty += 19
            for line in nl:
                cv.text(x + PX + 26, ty - 1, line, "n")
                ty += LN
            y += h
        if arrow and i < n - 1:
            ax = x + cw + 10
            cv.arrow("M%s %s H%s" % (f(ax), f(cv.top + H / 2), f(ax + gap - 20)))
        x += cw + gap
    return x - gap, cv.top + H


def draw_tree(cv, spec):
    nodes = []
    for no, line in spec.rows:
        raw = line.replace("\t", "  ")
        indent = len(raw) - len(raw.lstrip(" "))
        label, note, tone = cells(raw.strip().lstrip("-*").strip())
        nodes.append({"depth": indent // 2, "label": label, "note": note, "tone": tone})
    if not nodes:
        raise DoodleError("tree needs at least one row")
    base = min(n["depth"] for n in nodes)
    for n in nodes:
        n["depth"] -= base
    for i, n in enumerate(nodes):
        n["parent"] = None
        for j in range(i - 1, -1, -1):
            if nodes[j]["depth"] < n["depth"]:
                n["parent"] = j
                break
        n["kids"] = False
    for n in nodes:
        if n["parent"] is not None:
            nodes[n["parent"]]["kids"] = True
    IND, NOTEW = 30, 330
    y, right = cv.top, 0
    for n in nodes:
        x = PAD + n["depth"] * IND
        pw = cv.tw(n["label"], 14, True) + 46
        nl = cv.wrap(n["note"], NS, NOTEW) if n["note"] else []
        rh = max(34, 10 + len(nl) * LN)
        n.update(x=x, y=y, pw=pw, nl=nl, rh=rh)
        right = max(right, x + pw + (14 + max(cv.tw(s, NS) for s in nl) if nl else 0))
        y += rh + 8
    bottom = y - 8
    for i, n in enumerate(nodes):
        if n["parent"] is not None:
            p = nodes[n["parent"]]
            px, py = p["x"] + 17, p["y"] + 28
            cv.add('<path d="M%s %s V%s H%s" class="ln"/>' % (f(px), f(py), f(n["y"] + 15), f(n["x"])))
    for n in nodes:
        x, y, t = n["x"], n["y"], n["tone"]
        cv.box(x, y, n["pw"], 30, t, min(cv.r * .75, 15))
        ix, iy = x + 10, y + 8
        if n["kids"]:
            cv.add('<path d="M{a} {b} h6 l2 2.5 h8 a1.5 1.5 0 0 1 1.5 1.5 v9 a1.5 1.5 0 0 1 -1.5 1.5 h-16 '
                   'a1.5 1.5 0 0 1 -1.5 -1.5 v-11.5 a1.5 1.5 0 0 1 1.5 -1.5z" class="f-{t}"/>'
                   .format(a=f(ix + 1.5), b=f(iy), t=t))
        else:
            cv.add('<path d="M{a} {b} h8 l5 5 v10 a1.5 1.5 0 0 1 -1.5 1.5 h-11.5 a1.5 1.5 0 0 1 -1.5 -1.5 '
                   'v-13.5 a1.5 1.5 0 0 1 1.5 -1.5z" class="f-{t}" style="opacity:.75"/>'
                   .format(a=f(ix + 4), b=f(iy - 1), t=t))
        cv.add('<text x="%s" y="%s" class="t" style="font-size:14px">%s</text>' % (f(x + 34), f(y + 20), esc(n["label"])))
        ny = y + 20
        for line in n["nl"]:
            cv.text(x + n["pw"] + 12, ny, line, "n")
            ny += LN
    return right, bottom


def draw_cycle(cv, spec):
    cards = rows_as_cards(cv, spec, 210, mid=True)
    n = len(cards)
    if n < 2:
        raise DoodleError("cycle needs at least 2 rows")
    hmax = max(c.h for c in cards)
    s = math.sin(math.pi / n)
    rx = max(170.0, (210 + 56) / (2 * s))
    ry = max(110.0, (hmax + 46) / (2 * s))
    if n == 2:  # side by side, one arc above and one below
        rx, ry = 190.0, 46.0
    cx = PAD + 105 + rx
    cy = cv.top + hmax / 2 + ry
    for i, c in enumerate(cards):
        a = (math.pi if n == 2 else -math.pi / 2) + 2 * math.pi * i / n
        c.place(cx + rx * math.cos(a) - c.w / 2, cy + ry * math.sin(a) - c.h / 2)
    minx = min(c.x for c in cards)
    if minx < PAD:
        for c in cards:
            c.x += PAD - minx
        cx += PAD - minx
    if n > 2:
        cv.text(cx, cy + 22, "↻", "big", mid=True)
    for i, a in enumerate(cards):
        b = cards[(i + 1) % n]
        x1, y1 = a.edge_point(b.cx, b.cy)
        x2, y2 = b.edge_point(a.cx, a.cy)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ox, oy = mx - cx, my - cy
        d = math.hypot(ox, oy) or 1
        bend = 26 if n > 2 else 60
        qx, qy = mx + ox / d * bend, my + oy / d * bend
        if n == 2:
            qx, qy = mx, my + (-bend if i == 0 else bend)
            x1, y1 = a.cx + (40 if i == 0 else -40), a.y + (0 if i == 0 else a.h)
            x1, y1 = (a.x + a.w * (0.75 if i == 0 else 0.25), a.y + (0 if i == 0 else a.h))
            x2, y2 = (b.x + b.w * (0.25 if i == 0 else 0.75), b.y + (0 if i == 0 else b.h))
            y1 += -6 if i == 0 else 6
            y2 += -6 if i == 0 else 6
        cv.arrow("M%s %s Q%s %s %s %s" % (f(x1), f(y1), f(qx), f(qy), f(x2), f(y2)))
    for c in cards:
        c.draw()
    right = max(c.x + c.w for c in cards)
    bottom = max(c.y + c.h for c in cards) + (50 if n == 2 else 0)
    return right, bottom


def resolve(ref, nodes, ids, byname, created=None):
    """Edge endpoint -> node index: [id], 1-based row number, label, or a new node."""
    key = ref.strip()
    if key in ids:
        return ids[key]
    if key.isdigit() and 1 <= int(key) <= len(nodes):
        return int(key) - 1
    if key.lower() in byname:
        return byname[key.lower()]
    nodes.append(cells(key))
    byname[nodes[-1][0].lower()] = len(nodes) - 1
    if created is not None:
        created.append(key)
    return len(nodes) - 1


def draw_flow(cv, spec):
    raw_nodes, edges = [], []
    for no, line in spec.rows:
        e = split_edge(line)
        if e:
            edges.append((no,) + e)
        else:
            raw_nodes.append(line.strip())
    nodes, ids, byname = [], {}, {}
    for text in raw_nodes:
        m = re.match(r"^\[([^\]]+)\]\s*(.*)$", text)
        nid, text = (m.group(1), m.group(2)) if m else (None, text)
        nodes.append(cells(text))
        if nid:
            ids[nid] = len(nodes) - 1
        byname.setdefault(nodes[-1][0].lower(), len(nodes) - 1)
    E = []
    declared = len(nodes)
    for no, a, b, dashed, label, tone in edges:
        created = []
        E.append((resolve(a, nodes, ids, byname, created), resolve(b, nodes, ids, byname, created),
                  dashed, label, tone))
        for key in created if declared else ():
            known = list(ids) + [nd[0] for nd in nodes[:declared]]
            spec.warnings.append((no, "'%s' matches no node, so a new box was created%s"
                                  % (key, suggest(key, known) or "; use an [id], a row number or the exact label")))
    if not E:
        E = [(i, i + 1, False, "", "neutral") for i in range(len(nodes) - 1)]
    n = len(nodes)
    if not n:
        raise DoodleError("flow needs at least one node")
    adj = {i: [] for i in range(n)}
    for k, (a, b, *_rest) in enumerate(E):
        adj[a].append((b, k))
    state, back = {}, set()

    def dfs(u):
        state[u] = 1
        for v, k in adj[u]:
            if state.get(v) == 1:
                back.add(k)
            elif not state.get(v):
                dfs(v)
        state[u] = 2

    for u in range(n):
        if not state.get(u):
            dfs(u)
    layer = [0] * n
    for _ in range(n):
        changed = False
        for k, (a, b, *_rest) in enumerate(E):
            if k not in back and a != b and layer[b] < layer[a] + 1:
                layer[b] = layer[a] + 1
                changed = True
        if not changed:
            break
    L = max(layer) + 1
    vertical = "vertical" in spec.opts or (L > 4 and "horizontal" not in spec.opts)
    w = 240 if vertical else 190
    nodes = [Card(cv, label, note, tone, w, True) for label, note, tone in nodes]
    groups = [[i for i in range(n) if layer[i] == l] for l in range(L)]
    pos = {}
    for l, g in enumerate(groups):
        if l:
            def bary(i):
                ps = [pos[a] for a, b, *_r in E if b == i and a in pos and layer[a] < l]
                return sum(ps) / len(ps) if ps else pos.get(i, 0)
            g.sort(key=bary)
        for k, i in enumerate(g):
            pos[i] = k
    lab_w = max([cv.tw(e[3], 12.5) for k, e in enumerate(E) if e[3] and k not in back] + [0])
    if vertical:
        gap_main = 56 + (10 if lab_w else 0)
        y = cv.top
        width = max(len(g) * (w + 30) - 30 for g in groups)
        for g in groups:
            hh = max(nodes[i].h for i in g)
            rowx = PAD + (width - (len(g) * (w + 30) - 30)) / 2
            for k, i in enumerate(g):
                nodes[i].place(rowx + k * (w + 30), y + (hh - nodes[i].h) / 2)
            y += hh + gap_main
        right, bottom = PAD + width, y - gap_main
    else:
        gap_main = max(64, min(220, lab_w + 56))
        heights = [sum(nodes[i].h for i in g) + 26 * (len(g) - 1) for g in groups]
        H = max(heights)
        x = PAD
        for g, hh in zip(groups, heights):
            y = cv.top + (H - hh) / 2
            for i in g:
                nodes[i].place(x, y)
                y += nodes[i].h + 26
            x += w + gap_main
        right, bottom = x - gap_main, cv.top + H
    extra = low_label = 0
    for k, (a, b, dashed, lab, tone) in enumerate(E):
        A, B = nodes[a], nodes[b]
        if k in back or a == b:
            extra += 1
            if vertical:
                gx = right + 26 * extra
                x1, y1, x2, y2 = A.x + A.w + 4, A.cy, B.x + B.w + 6, B.cy
                d = "M%s %s C%s %s %s %s %s %s" % (f(x1), f(y1), f(gx), f(y1), f(gx), f(y2), f(x2), f(y2))
                lx, ly = gx, (y1 + y2) / 2
            else:
                gy = bottom + 30 * extra
                x1, y1, x2, y2 = A.cx, A.y + A.h + 4, B.cx, B.y + B.h + 6
                d = "M%s %s C%s %s %s %s %s %s" % (f(x1), f(y1), f(x1), f(gy), f(x2), f(gy), f(x2), f(y2))
                lx, ly = (x1 + x2) / 2, (y1 + y2) / 8 + gy * .75 + 17  # just under the curve's lowest point
                low_label = max(low_label, 22 if lab else 0)
        elif vertical:
            x1, y1, x2, y2 = A.cx, A.y + A.h + 2, B.cx, B.y - 4
            my = (y1 + y2) / 2
            d = "M%s %s C%s %s %s %s %s %s" % (f(x1), f(y1), f(x1), f(my), f(x2), f(my), f(x2), f(y2))
            lx, ly = (x1 + x2) / 2 + (cv.tw(lab, 12.5) / 2 + 10 if x1 == x2 else 0), my + 4
        else:
            x1, y1, x2, y2 = A.x + A.w + 2, A.cy, B.x - 4, B.cy
            mx = (x1 + x2) / 2
            d = "M%s %s C%s %s %s %s %s %s" % (f(x1), f(y1), f(mx), f(y1), f(mx), f(y2), f(x2), f(y2))
            # above the flat end of the curve, where it never crosses the text
            # (above it when the edge rises or runs flat, below it when the edge falls)
            lw = min(cv.tw(lab, 12.5), gap_main - 8)
            lx, ly = max(mx, x2 - 10 - lw / 2), (y2 + 18 if y2 > y1 + 2 else y2 - 8)
        cv.arrow(d, dashed, tone)
        if lab:
            forward = not (k in back or a == b)
            cv.label(lx, ly, lab, 170 if vertical else gap_main - 8, up=forward and not vertical and ly < y2)
    for c in nodes:
        c.draw()
    if any(k in back or E[k][0] == E[k][1] for k in range(len(E))):
        if vertical:
            right += 26 * extra + 40
        else:
            bottom += 30 * extra + 4 + low_label
    return right, bottom


def draw_sequence(cv, spec):
    actors, msgs = [], []
    index = {}

    def actor(name, tone="neutral", no=None):
        key = name.lower()
        if key not in index:
            hint = suggest(name, [x["name"] for x in actors], .85) if no else ""
            if hint:  # probably a typo of an existing actor
                spec.warnings.append((no, "new actor '%s'%s" % (name, hint)))
            index[key] = len(actors)
            actors.append({"name": name, "tone": tone})
        return index[key]

    for no, line in spec.rows:
        e = split_edge(line)
        if e:
            a, b, dashed, label, tone = e
            msgs.append((actor(a, no=no), actor(b, no=no), dashed, label, tone))
        else:
            label, note, tone = cells(line.strip())
            actor(label, tone)
    if not actors:
        raise DoodleError("sequence needs messages like 'A -> B: hello'")
    aw = [max(110.0, cv.tw(a["name"], TS, True) + 2 * PX) for a in actors]
    span = 0.0
    for a, b, _d, lab, _t in msgs:
        if a != b and lab:
            span = max(span, cv.tw(lab, 13) / max(1, abs(b - a)) + 40)
    col = max(170.0, max(aw) + 40, min(span, 300.0))
    xs = [PAD + aw[0] / 2 + i * col for i in range(len(actors))]
    top = cv.top
    for i, a in enumerate(actors):
        c = Card(cv, a["name"], "", a["tone"], aw[i], True)
        c.place(xs[i] - aw[i] / 2, top)
        a["card"] = c
    y = top + actors[0]["card"].h + 34
    rows = []
    for k, (a, b, dashed, lab, tone) in enumerate(msgs):
        maxw = (abs(xs[b] - xs[a]) - 40) if a != b else 180
        lines = cv.wrap(lab, 13, max(maxw, 90)) if lab else []
        y += max(0, len(lines) - 1) * 16
        rows.append((a, b, dashed, lines, tone, y))
        y += 46 if a != b else 62
    bottom = y - 10
    for i, a in enumerate(actors):
        cv.add('<path d="M%s %s V%s" class="ln d"/>' % (f(xs[i]), f(a["card"].y + a["card"].h), f(bottom)))
    for i, a in enumerate(actors):
        a["card"].draw()
    for k, (a, b, dashed, lines, tone, yy) in enumerate(rows):
        cls = "n" + (" x-" + tone if tone != "neutral" else "")
        num_tone = tone if tone != "neutral" else "info"
        if a == b:
            x = xs[a]
            cv.arrow("M%s %s h46 v22 h-42" % (f(x + 4), f(yy)), dashed, tone)
            ly = yy + 15 - (len(lines) - 1) * 8
            for j, line in enumerate(lines):
                cv.text(x + 58, ly + j * 16, line, cls)
            cv.badge(x - 16, yy + 11, str(k + 1), num_tone)
            continue
        x1, x2 = xs[a], xs[b]
        dirn = 1 if x2 > x1 else -1
        cv.arrow("M%s %s H%s" % (f(x1 + 4 * dirn), f(yy), f(x2 - 6 * dirn)), dashed, tone)
        for j, line in enumerate(lines):
            cv.text((x1 + x2) / 2, yy - 9 - (len(lines) - 1 - j) * 16, line, cls, mid=True)
        cv.badge(x1 - 16 * dirn, yy, str(k + 1), num_tone)
    right = xs[-1] + aw[-1] / 2
    if any(a == b for a, b, *_r in msgs):
        right = max(right, max(xs[a] + 58 + max((cv.tw(l, 13) for l in ls), default=0)
                               for a, b, _d, ls, _t, _y in rows if a == b))
    return max(right, PAD + aw[0]), bottom


NUMBER = re.compile(r"-?\d[\d.,]*")


def number(text):
    """First number in text: '1,200 ms' -> 1200, '2.5 s' -> 2.5, '1,5 s' -> 1.5, '1.234,5' -> 1234.5."""
    m = NUMBER.search(text)
    if not m:
        return None
    s = m.group(0).rstrip(".,")
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dec == "," else ",", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", "") if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s) else s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def draw_bars(cv, spec):
    items = []
    for no, line in spec.rows:
        label, note, tone = cells(line.strip())
        value = number(note) if note else number(label)
        if value is None:
            raise DoodleError("line %d: bars need a number in the note, like 'DNS lookup | 120 ms'" % no)
        if value < 0:
            raise DoodleError("line %d: bars can't show negative numbers" % no)
        items.append((label, note or ("%g" % value), tone, value))
    if not items:
        raise DoodleError("bars needs at least one row like 'Label | 42'")
    LABW, BAR, BH = 200, 360, 26
    labs = [cv.wrap(lab, 14, LABW, True) for lab, *_r in items]
    lw = max(max(cv.tw(s, 14, True) for s in ls) if ls else 0 for ls in labs)
    x0 = PAD + lw + 16
    vmax = max(v for *_r, v in items) or 1
    y, right = cv.top, x0 + BAR
    for (label, note, tone, value), ls in zip(items, labs):
        rh = max(BH, len(ls) * 18 + 6)
        cy = y + rh / 2
        for i, s in enumerate(ls):
            cv.add('<text x="%s" y="%s" class="t" style="font-size:14px" text-anchor="end">%s</text>'
                   % (f(x0 - 14), f(cy + 5 - (len(ls) - 1) * 9 + i * 18), esc(s)))
        bw = max(6.0, BAR * value / vmax)
        cv.add('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" class="f-%s"/>'
               % (f(x0), f(cy - BH / 2), f(bw), f(BH), f(min(cv.r * .5, 8)), tone))
        lines = cv.wrap(note, NS, 220)
        for i, s in enumerate(lines):
            cv.text(x0 + bw + 10, cy + 4.5 - (len(lines) - 1) * 9 + i * 18, s, "n" + (" x-" + tone if tone != "neutral" else ""))
        right = max(right, x0 + bw + 10 + max(cv.tw(s, NS) for s in lines))
        y += rh + 12
    cv.add('<path d="M%s %s V%s" class="ln"/>' % (f(x0), f(cv.top - 6), f(y - 6)))
    return right, y - 12


def overlaps(a, b, gap):
    return (a.x < b.x + b.w + gap and b.x < a.x + a.w + gap and
            a.y < b.y + b.h + gap and b.y < a.y + a.h + gap)


def draw_hub(cv, spec):
    rows = [cells(line.strip()) for _, line in spec.rows]
    if len(rows) < 2:
        raise DoodleError("hub needs the center on the first row and at least one more row around it")
    label, note, tone = rows[0]
    center = Card(cv, label, note, tone if tone != "neutral" else "info", 220, True)
    spokes = [Card(cv, lab, nt, tn, 190, True) for lab, nt, tn in rows[1:]]
    n = len(spokes)
    hmax = max(c.h for c in spokes)
    if n == 1:
        angles = [0.0]
    elif n == 2:
        angles = [math.pi, 0.0]
    else:
        angles = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
    rx, ry = center.w / 2 + 95 + 50, center.h / 2 + hmax / 2 + 40
    center.place(-center.w / 2, -center.h / 2)
    for _ in range(60):  # grow the ellipse until no two boxes touch
        for c, a in zip(spokes, angles):
            c.place(rx * math.cos(a) - c.w / 2, ry * math.sin(a) - c.h / 2)
        boxes = [center] + spokes
        if not any(overlaps(p, q, 30) for i, p in enumerate(boxes) for q in boxes[i + 1:]):
            break
        rx, ry = rx * 1.06, ry * 1.06
    minx = min(c.x for c in boxes)
    miny = min(c.y for c in boxes)
    for c in boxes:
        c.x += PAD - minx
        c.y += cv.top - miny
    arrow = "arrow" in spec.opts
    for c in spokes:
        x1, y1 = center.edge_point(c.cx, c.cy, 3)
        x2, y2 = c.edge_point(center.cx, center.cy, 5 if arrow else 3)
        cls = "e" + (" s-" + c.tone if c.tone != "neutral" else "")
        cv.add('<path d="M%s %s L%s %s" class="%s"%s/>'
               % (f(x1), f(y1), f(x2), f(y2), cls, ' marker-end="url(#ah)"' if arrow else ""))
    for c in boxes:
        c.draw()
    return max(c.x + c.w for c in boxes), max(c.y + c.h for c in boxes)


DRAW = {"flow": draw_flow, "cycle": draw_cycle, "timeline": draw_timeline, "compare": draw_compare,
        "tree": draw_tree, "stack": draw_stack, "sequence": draw_sequence, "bars": draw_bars, "hub": draw_hub}


def render(src, style=None):
    spec = parse(src)
    cv = Canvas(spec, style)
    w, h = DRAW[spec.kind](cv, spec)
    if spec.title:
        w = max(w, PAD + cv.tw(spec.title, 20, True))
    for s in spec.sub:
        w = max(w, PAD + cv.tw(s, 13))
    return spec, cv.render(w, h)


# ---------------------------------------------------------------- settings (doodle.json)

CONFIG_NAME = "doodle.json"
# Keys the renderer uses, then keys only the agent reads (how to write the explanation).
DEFAULTS = {
    "theme": "paper", "sketch": None, "scheme": "auto", "frame": True, "font": "", "imageDir": "img",
    "colors": {}, "darkColors": {},
    "audience": "beginner", "depth": "standard", "language": "auto", "docsDir": "", "notes": "",
}
CHOICES = {"audience": ("kid", "beginner", "developer", "expert"), "depth": ("quick", "standard", "deep"),
           "scheme": SCHEMES}


def user_config_path():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "doodle", "config.json")


def find_project_config(start):
    """The nearest doodle.json from start upward, stopping at the repository root."""
    d = os.path.abspath(start)
    while True:
        p = os.path.join(d, CONFIG_NAME)
        if os.path.isfile(p):
            return p
        if os.path.exists(os.path.join(d, ".git")) or os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def read_config(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except ValueError as e:
        raise DoodleError("%s: invalid JSON (%s)" % (path, e))
    if not isinstance(data, dict):
        raise DoodleError("%s: expected a JSON object like {\"theme\": \"clean\"}" % path)
    return data


def load_settings(start=".", explicit=None, warnings=None):
    """Merge built-in defaults < ~/.config/doodle/config.json < nearest doodle.json (or explicit)."""
    settings, sources = dict(DEFAULTS), []
    paths = [explicit] if explicit else [user_config_path(), find_project_config(start)]
    for p in paths:
        if not p or not os.path.isfile(p):
            if explicit:
                raise DoodleError("config file not found: %s" % p)
            continue
        data = read_config(p)
        for k, v in data.items():
            if k.startswith("$") or k.startswith("_"):
                continue
            if k not in DEFAULTS:
                if warnings is not None:
                    warnings.append("%s: unknown setting '%s'%s" % (p, k, suggest(k, DEFAULTS)))
                continue
            if k in CHOICES and v not in CHOICES[k]:
                raise DoodleError("%s: '%s' must be one of %s, got %r" % (p, k, ", ".join(CHOICES[k]), v))
            if k in ("colors", "darkColors") and isinstance(v, dict):
                v = dict(settings[k], **v)
            settings[k] = v
        sources.append(os.path.abspath(p))
    settings["sources"] = sources
    return settings


def style_from(settings):
    return Style(theme=settings.get("theme"), sketch=settings.get("sketch"), scheme=settings.get("scheme", "auto"),
                 frame=settings.get("frame", True), font=settings.get("font") or "",
                 colors=settings.get("colors"), dark_colors=settings.get("darkColors"))


STARTER = {
    "theme": "paper",
    "sketch": False,
    "scheme": "auto",
    "colors": {},
    "imageDir": "img",
    "audience": "beginner",
    "depth": "standard",
    "language": "auto",
    "docsDir": "",
    "notes": "",
}


# ---------------------------------------------------------------- markdown mode

FENCE = re.compile(r"^```doodle[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*([^`\s]*)")


def segments(md):
    """Split markdown into ('text'|'code'|'doodle', content) so code examples are never touched."""
    out, buf, fence, kind = [], [], None, None
    opening = ""
    for line in md.splitlines(keepends=True):
        m = FENCE_LINE.match(line)
        if fence is None:
            if m:
                if buf:
                    out.append(("text", "".join(buf)))
                fence, kind = m.group(1), "doodle" if m.group(2).lower() == "doodle" else "code"
                opening = line
                buf = [] if kind == "doodle" else [line]
            else:
                buf.append(line)
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip()[len(m.group(1)):]:
            if kind == "code":
                buf.append(line)
            out.append((kind, "".join(buf)))
            buf, fence, kind = [], None, None
        else:
            buf.append(line)
    if fence and kind == "doodle":
        buf.insert(0, opening)
    if buf:
        out.append(("code" if fence else "text", "".join(buf)))
    return out


DONE = re.compile(r"<!-- doodle\n(.*?)-->\n!\[[^\]]*\]\(([^)\s]+)\)", re.S)


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40] or "diagram"


def write_if_changed(path, text):
    """Write text unless the file already holds it (keeps timestamps and git diffs quiet)."""
    try:
        with open(path, encoding="utf-8") as fh:
            if fh.read() == text:
                return False
    except OSError:
        pass
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return True


def render_markdown(path, img_dir=None, style=None, dry_run=False, warnings=None):
    """Render every doodle block of a Markdown file. Returns the SVG paths (relative to the file).

    Nothing is written when any block fails, or with dry_run=True. Lint warnings are appended
    to `warnings` as 'file:line: message' strings."""
    with open(path, encoding="utf-8") as fh:
        md = fh.read()
    base = os.path.dirname(os.path.abspath(path))
    rel_dir = img_dir or "img"
    output_root = os.path.realpath(os.path.join(base, rel_dir))
    stem = slug(os.path.splitext(os.path.basename(path))[0])
    segs = segments(md)
    used = {p for kind, chunk in segs if kind == "text" for p in DONE_PATHS(chunk)}
    errors, pending = [], []
    where = os.path.relpath(path) if not os.path.isabs(path) else path

    def emit(src, rel, line):
        try:
            spec, svg = render(src, style)
        except DoodleError as e:
            msg = str(e)
            m = re.match(r"line (\d+): (.*)", msg, re.S)
            if m:
                msg = "%s:%d: %s" % (where, line + int(m.group(1)) - 1, m.group(2))
            else:
                msg = "%s:%d: %s" % (where, line, msg)
            errors.append(msg)
            return None
        if warnings is not None:
            for no, msg in spec.warnings:
                warnings.append("%s:%d: %s" % (where, line + (no or 1) - 1, msg))
        if rel is None:
            name = "%s-%s" % (stem, slug(spec.title or spec.kind))
            rel, k = "%s/%s.svg" % (rel_dir, name), 2
            while rel in used:
                rel, k = "%s/%s-%d.svg" % (rel_dir, name, k), k + 1
            used.add(rel)
        out = os.path.realpath(os.path.join(base, rel))
        if os.path.commonpath([output_root, out]) != output_root or not out.lower().endswith(".svg"):
            errors.append("%s:%d: SVG output must stay inside '%s' (got '%s'); pass the same -o or imageDir "
                          "used when this document was first rendered" % (where, line, rel_dir, rel))
            return None
        pending.append((out, svg, rel))
        block_src = src.strip("\n").replace("-->", "- ->")
        return "<!-- doodle\n%s\n-->\n![%s](%s)" % (block_src, (spec.title or spec.kind).replace("]", ")"), rel)

    parts, line = [], 1
    for kind, chunk in segs:
        if kind == "text":
            def redo(m, start=line, chunk=chunk):
                at = start + chunk.count("\n", 0, m.start()) + 1  # first spec line, after '<!-- doodle'
                return emit(m.group(1).replace("- ->", "-->"), m.group(2), at) or m.group(0)
            parts.append(DONE.sub(redo, chunk))
        elif kind == "doodle":
            block = emit(chunk, None, line + 1)
            parts.append(block + "\n" if block else "```doodle\n%s```\n" % chunk)
            line += 2  # the opening and closing fences are not part of the chunk
        else:
            parts.append(chunk)
        line += chunk.count("\n")
    md = "".join(parts)
    if errors:
        raise DoodleError("\n".join(errors))
    if not dry_run:
        for out, svg, _rel in pending:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            write_if_changed(out, svg)
        write_if_changed(path, md)
    return [rel for _out, _svg, rel in pending]


def DONE_PATHS(md):
    return [m.group(2) for m in DONE.finditer(md)]


def list_themes():
    width = max(len(n) for n in THEMES)
    return "\n".join("%-*s  %s" % (width, n, t["about"]) for n, t in THEMES.items())


def main(argv):
    ap = argparse.ArgumentParser(
        prog="doodle.py", description="Turn tiny text specs into friendly SVG diagrams.",
        epilog="Settings come from ~/.config/doodle/config.json and the nearest doodle.json; flags win. "
               "Syntax: references/dsl.md")
    ap.add_argument("input", nargs="?", help="a .md file, a spec file, or - for stdin")
    ap.add_argument("-o", dest="out", help="image folder (Markdown) or output .svg (single spec)")
    ap.add_argument("--theme", help="paper, clean, candy, blueprint or chalk")
    ap.add_argument("--sketch", action="store_true", default=None, help="hand-drawn look")
    ap.add_argument("--scheme", choices=SCHEMES, help="auto follows the viewer's light/dark mode")
    ap.add_argument("--config", help="use this settings file instead of searching for doodle.json")
    ap.add_argument("--check", action="store_true", help="validate and lint without writing files")
    ap.add_argument("--themes", action="store_true", help="list the themes")
    ap.add_argument("--settings", action="store_true", help="print the effective settings as JSON")
    ap.add_argument("--init", action="store_true", help="create a starter doodle.json in the current folder")
    ap.add_argument("-q", "--quiet", action="store_true", help="don't print lint warnings")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2
    try:
        if a.themes:
            print(list_themes())
            return 0
        if a.init:
            if os.path.exists(CONFIG_NAME):
                raise DoodleError("%s already exists; edit it instead" % CONFIG_NAME)
            with open(CONFIG_NAME, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(STARTER, indent=2, ensure_ascii=False) + "\n")
            print(os.path.abspath(CONFIG_NAME))
            return 0
        src = a.input
        start = os.path.dirname(os.path.abspath(src)) if src and src != "-" else os.getcwd()
        warnings = []
        settings = load_settings(start, a.config, warnings)
        for k in ("theme", "sketch", "scheme"):
            if getattr(a, k) is not None:
                settings[k] = getattr(a, k)
        if a.settings:
            print(json.dumps(settings, indent=2, ensure_ascii=False))
            return 0
        if not src:
            ap.print_help()
            return 2
        style = style_from(settings)
        if src == "-":
            spec, svg = render(sys.stdin.read(), style)
            warnings += ["stdin:%d: %s" % (no or 1, m) for no, m in spec.warnings]
            if not a.check:
                sys.stdout.write(svg)
        elif src.lower().endswith((".md", ".markdown")):
            rels = render_markdown(src, a.out or settings.get("imageDir") or "img", style, a.check, warnings)
            for rel in rels if not a.check else ():
                print(rel)
        else:
            with open(src, encoding="utf-8") as fh:
                spec, svg = render(fh.read(), style)
            warnings += ["%s:%d: %s" % (src, no or 1, m) for no, m in spec.warnings]
            if not a.check:
                dest = a.out or os.path.splitext(src)[0] + ".svg"
                write_if_changed(dest, svg)
                print(dest)
        if not a.quiet:
            for w in warnings:
                print("warning: %s" % w, file=sys.stderr)
        if a.check:
            print("ok%s" % (" (%d warning%s)" % (len(warnings), "s" if len(warnings) > 1 else "")
                            if warnings else ""), file=sys.stderr)
    except (DoodleError, OSError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
