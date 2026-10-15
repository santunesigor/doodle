#!/usr/bin/env python3
"""doodle - turn tiny text specs into friendly SVG diagrams. Python 3.8+, stdlib only.

Usage:
  doodle.py FILE.md [-o IMG_DIR]   render every ```doodle block in FILE.md to an SVG
                                   and swap the block for an image link (re-runnable)
  doodle.py SPEC.txt [-o OUT.svg]  render a single spec file
  doodle.py -                      read one spec from stdin, write the SVG to stdout

Spec format (see references/dsl.md):
  kind: Title                  kind = flow | cycle | timeline | compare | tree | stack | sequence
  > optional subtitle
  @sketch @vertical            options
  label | note | tone          tone = neutral | info | ok | bad | warn
"""
import math
import os
import re
import sys
import unicodedata

KINDS = ("flow", "cycle", "timeline", "compare", "tree", "stack", "sequence")
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
        self.rows = []  # (line number, raw line without trailing spaces)


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
            spec.opts.update(w.lstrip("@").lower() for w in st.split())
        elif st == ">" or st.startswith("> "):
            spec.sub.append(st[1:].strip())
        else:
            spec.rows.append((no, line))
    if not spec.kind:
        raise DoodleError("empty spec: the first line must be 'kind: Title'")
    return spec


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


def tw(s, size, bold=False, sketch=False):
    """Rough rendered width of s in px (no font metrics in the stdlib)."""
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


def wrap(text, size, maxw, bold=False, sketch=False):
    out = []
    for para in str(text).split("\n"):
        line = ""
        for word in para.split():
            while tw(word, size, bold, sketch) > maxw and len(word) > 1:
                if line:
                    out.append(line)
                    line = ""
                cut = len(word) - 1
                while cut > 1 and tw(word[:cut], size, bold, sketch) > maxw:
                    cut -= 1
                out.append(word[:cut])
                word = word[cut:]
            cand = line + " " + word if line else word
            if not line or tw(cand, size, bold, sketch) <= maxw:
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
FONT_SKETCH = ('"Comic Neue","Comic Sans MS","Chalkboard SE","Segoe Print",'
               '"Bradley Hand",ui-rounded,sans-serif')

LIGHT = dict(bg="#fffdf9", line="#ebe5da", ink="#1f2933", mut="#5f6b7a", edge="#7b8794",
             neutral=("#f4f1ea", "#8a8174"), info=("#e8f1fc", "#3a78c2"), ok=("#e7f6eb", "#2f8a4b"),
             bad=("#fdecea", "#c8423b"), warn=("#fff5df", "#c38410"))
DARK = dict(bg="#14181d", line="#2a3038", ink="#e6e9ed", mut="#a2acb8", edge="#8d98a5",
            neutral=("#23272e", "#8b949e"), info=("#132a43", "#6aa8ec"), ok=("#12301d", "#5cc184"),
            bad=("#3b1716", "#f07c74"), warn=("#3a2c0c", "#f0b543"))


def palette_vars(p):
    v = ["--bg:%s;--line:%s;--ink:%s;--mut:%s;--edge:%s" % (p["bg"], p["line"], p["ink"], p["mut"], p["edge"])]
    for t in TONES:
        v.append("--%s1:%s;--%s2:%s" % (t, p[t][0], t, p[t][1]))
    return ";".join(v)


def css(sketch):
    tones = "".join(
        ".c-{t}{{fill:var(--{t}1);stroke:var(--{t}2)}}.f-{t}{{fill:var(--{t}2)}}"
        ".s-{t}{{stroke:var(--{t}2)}}.x-{t}{{fill:var(--{t}2)}}".format(t=t) for t in TONES)
    return (
        "svg{%s}@media (prefers-color-scheme:dark){svg{%s}}"
        "text{font-family:%s;fill:var(--ink)}"
        ".bg{fill:var(--bg);stroke:var(--line)}"
        ".h{font-size:20px;font-weight:700}.sub{font-size:13px;fill:var(--mut)}"
        ".t{font-size:%dpx;font-weight:650}.n{font-size:%dpx;fill:var(--mut)}"
        ".card{stroke-width:1.6}.w{fill:#fff;font-size:12px;font-weight:700}"
        ".e{fill:none;stroke:var(--edge);stroke-width:1.8;stroke-linecap:round}"
        ".d{stroke-dasharray:6 5}.ah{fill:var(--edge)}.ln{stroke:var(--line);stroke-width:2;fill:none}"
        ".el{font-size:12.5px;fill:var(--mut);paint-order:stroke;stroke:var(--bg);"
        "stroke-width:5px;stroke-linejoin:round}"
        ".big{font-size:64px;fill:var(--line)}%s"
    ) % (palette_vars(LIGHT), palette_vars(DARK), FONT_SKETCH if sketch else FONT, TS, NS, tones)


class Canvas:
    def __init__(self, spec):
        self.spec = spec
        self.sketch = "sketch" in spec.opts
        self.parts = []
        self.top = PAD
        if spec.title:
            self.top += 26
        self.top += 19 * len(spec.sub)
        if spec.title or spec.sub:
            self.top += 18

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, cls, mid=False):
        self.add('<text x="%s" y="%s" class="%s"%s>%s</text>'
                 % (f(x), f(y), cls, ' text-anchor="middle"' if mid else "", esc(s)))

    def wrap(self, text, size, maxw, bold=False):
        return wrap(text, size, maxw, bold, self.sketch)

    def tw(self, s, size, bold=False):
        return tw(s, size, bold, self.sketch)

    def arrow(self, d, dashed=False, tone=None):
        cls = "e" + (" d" if dashed else "") + (" s-" + tone if tone and tone != "neutral" else "")
        self.add('<path d="%s" class="%s" marker-end="url(#ah)"/>' % (d, cls))

    def label(self, x, y, s, maxw=170):
        for i, line in enumerate(self.wrap(s, 12.5, maxw)):
            self.text(x, y + i * 16, line, "el", mid=True)

    def badge(self, x, y, n, tone):
        self.add('<circle cx="%s" cy="%s" r="11" class="f-%s"/>' % (f(x), f(y), tone))
        self.text(x, y + 4, n, "w", mid=True)

    def render(self, w, h):
        spec, sk = self.spec, self.sketch
        head = []
        y = PAD + 8
        if spec.title:
            y += 12
            head.append('<text x="%d" y="%s" class="h">%s</text>' % (PAD, f(y), esc(spec.title)))
        for s in spec.sub:
            y += 19
            head.append('<text x="%d" y="%s" class="sub">%s</text>' % (PAD, f(y), esc(s)))
        w, h = math.ceil(w + PAD), math.ceil(h + PAD)
        rough = ('<filter id="rough"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" '
                 'seed="7"/><feDisplacementMap in="SourceGraphic" scale="2.6"/></filter>') if sk else ""
        # shapes first, then all text on top, so the sketch filter never blurs letters
        shapes = "".join(p for p in self.parts if not p.startswith("<text"))
        texts = "".join(p for p in self.parts if p.startswith("<text"))
        body = ('<g filter="url(#rough)">%s</g>' % shapes if sk else shapes) + texts
        label = esc(spec.title or spec.kind)
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            'role="img" aria-label="{label}"><title>{label}</title><style>{css}</style><defs>'
            '<marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ah"/></marker>'
            '<filter id="sh" x="-10%" y="-10%" width="120%" height="140%"><feDropShadow dx="0" dy="1.5" '
            'stdDeviation="1.6" flood-color="#000" flood-opacity=".10"/></filter>{rough}</defs>'
            '<rect x="1" y="1" width="{w2}" height="{h2}" rx="16" class="bg"/>{head}{body}</svg>\n'
        ).format(w=w, h=h, w2=w - 2, h2=h - 2, label=label, css=css(sk), rough=rough,
                 head="".join(head), body=body)


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
        cv.add('<rect x="%s" y="%s" width="%s" height="%s" rx="12" class="card c-%s" filter="url(#sh)"/>'
               % (f(self.x), f(self.y), f(self.w), f(self.h), self.tone))
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
        cv.add('<rect x="%s" y="%s" width="%s" height="%s" rx="14" class="card c-%s" filter="url(#sh)"/>'
               % (f(x), f(y0), f(cw), f(H), c["tone"]))
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
        cv.add('<rect x="%s" y="%s" width="%s" height="30" rx="9" class="card c-%s" filter="url(#sh)"/>'
               % (f(x), f(y), f(n["pw"]), t))
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


def resolve(ref, nodes, ids, byname):
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
    return len(nodes) - 1


def draw_flow(cv, spec):
    raw_nodes, edges = [], []
    for no, line in spec.rows:
        e = split_edge(line)
        if e:
            edges.append(e)
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
    for a, b, dashed, label, tone in edges:
        E.append((resolve(a, nodes, ids, byname), resolve(b, nodes, ids, byname), dashed, label, tone))
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
    extra = 0
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
                lx, ly = (x1 + x2) / 2, gy - 18
        elif vertical:
            x1, y1, x2, y2 = A.cx, A.y + A.h + 2, B.cx, B.y - 4
            my = (y1 + y2) / 2
            d = "M%s %s C%s %s %s %s %s %s" % (f(x1), f(y1), f(x1), f(my), f(x2), f(my), f(x2), f(y2))
            lx, ly = (x1 + x2) / 2 + (cv.tw(lab, 12.5) / 2 + 10 if x1 == x2 else 0), my + 4
        else:
            x1, y1, x2, y2 = A.x + A.w + 2, A.cy, B.x - 4, B.cy
            mx = (x1 + x2) / 2
            d = "M%s %s C%s %s %s %s %s %s" % (f(x1), f(y1), f(mx), f(y1), f(mx), f(y2), f(x2), f(y2))
            lx, ly = mx, (y1 + y2) / 2 - 8
        cv.arrow(d, dashed, tone)
        if lab:
            cv.label(lx, ly, lab, 170 if vertical else gap_main - 8)
    for c in nodes:
        c.draw()
    if any(k in back or E[k][0] == E[k][1] for k in range(len(E))):
        if vertical:
            right += 26 * extra + 40
        else:
            bottom += 30 * extra + 4
    return right, bottom


def draw_sequence(cv, spec):
    actors, msgs = [], []
    index = {}

    def actor(name, tone="neutral"):
        key = name.lower()
        if key not in index:
            index[key] = len(actors)
            actors.append({"name": name, "tone": tone})
        return index[key]

    for no, line in spec.rows:
        e = split_edge(line)
        if e:
            a, b, dashed, label, tone = e
            msgs.append((actor(a), actor(b), dashed, label, tone))
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


DRAW = {"flow": draw_flow, "cycle": draw_cycle, "timeline": draw_timeline, "compare": draw_compare,
        "tree": draw_tree, "stack": draw_stack, "sequence": draw_sequence}


def render(src):
    spec = parse(src)
    cv = Canvas(spec)
    w, h = DRAW[spec.kind](cv, spec)
    if spec.title:
        w = max(w, PAD + cv.tw(spec.title, 20, True))
    for s in spec.sub:
        w = max(w, PAD + cv.tw(s, 13))
    return spec, cv.render(w, h)


# ---------------------------------------------------------------- markdown mode

FENCE = re.compile(r"^```doodle[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*([^`\s]*)")


def segments(md):
    """Split markdown into ('text'|'code'|'doodle', content) so code examples are never touched."""
    out, buf, fence, kind = [], [], None, None
    for line in md.splitlines(keepends=True):
        m = FENCE_LINE.match(line)
        if fence is None:
            if m:
                if buf:
                    out.append(("text", "".join(buf)))
                fence, kind = m.group(1), "doodle" if m.group(2).lower() == "doodle" else "code"
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
    if buf:
        out.append(("code" if fence else "text", "".join(buf)))
    return out
DONE = re.compile(r"<!-- doodle\n(.*?)-->\n!\[[^\]]*\]\(([^)\s]+)\)", re.S)


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40] or "diagram"


def render_markdown(path, img_dir=None):
    with open(path, encoding="utf-8") as fh:
        md = fh.read()
    base = os.path.dirname(os.path.abspath(path))
    rel_dir = img_dir or "img"
    stem = slug(os.path.splitext(os.path.basename(path))[0])
    used = {p for kind, chunk in segments(md) if kind == "text" for p in DONE_PATHS(chunk)}
    errors, written = [], []

    def emit(src, rel):
        try:
            spec, svg = render(src)
        except DoodleError as e:
            errors.append("%s: %s" % (rel or "block", e))
            return None
        if rel is None:
            name = "%s-%s" % (stem, slug(spec.title or spec.kind))
            rel, k = "%s/%s.svg" % (rel_dir, name), 2
            while rel in used:
                rel, k = "%s/%s-%d.svg" % (rel_dir, name, k), k + 1
            used.add(rel)
        out = os.path.join(base, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(svg)
        written.append(rel)
        block_src = src.strip("\n").replace("-->", "- ->")
        return "<!-- doodle\n%s\n-->\n![%s](%s)" % (block_src, (spec.title or spec.kind).replace("]", ")"), rel)

    def redo(m):
        return emit(m.group(1).replace("- ->", "-->"), m.group(2)) or m.group(0)

    parts = []
    for kind, chunk in segments(md):
        if kind == "text":
            parts.append(DONE.sub(redo, chunk))
        elif kind == "doodle":
            block = emit(chunk, None)
            parts.append(block + "\n" if block else "```doodle\n%s```\n" % chunk)
        else:
            parts.append(chunk)
    md = "".join(parts)
    if errors:
        raise DoodleError("\n".join(errors))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(md)
    return written


def DONE_PATHS(md):
    return [m.group(2) for m in DONE.finditer(md)]


def main(argv):
    args = [a for a in argv if a not in ("-o",)]
    out = None
    if "-o" in argv:
        i = argv.index("-o")
        if i + 1 >= len(argv):
            print("error: -o needs a value", file=sys.stderr)
            return 2
        out = argv[i + 1]
        args = argv[:i] + argv[i + 2:]
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if args and args[0] in ("-h", "--help") else 2
    src = args[0]
    try:
        if src == "-":
            sys.stdout.write(render(sys.stdin.read())[1])
        elif src.lower().endswith((".md", ".markdown")):
            for rel in render_markdown(src, out):
                print(rel)
        else:
            with open(src, encoding="utf-8") as fh:
                svg = render(fh.read())[1]
            dest = out or os.path.splitext(src)[0] + ".svg"
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(svg)
            print(dest)
    except DoodleError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    except OSError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
