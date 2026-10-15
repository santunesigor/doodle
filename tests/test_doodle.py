import os
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "doodle", "scripts"))

import doodle  # noqa: E402

ROOT = os.path.join(HERE, "..")
DSL = os.path.join(ROOT, "skills", "doodle", "references", "dsl.md")
DOCS = [os.path.join(ROOT, "docs", n) for n in ("tutorial.md", "tutorial.pt-BR.md")] + [
    os.path.join(ROOT, "skills", "doodle", "SKILL.md")]


def blocks(path):
    with open(path, encoding="utf-8") as fh:
        return doodle.FENCE.findall(fh.read())


class ParseTest(unittest.TestCase):
    def test_header_options_subtitle(self):
        spec = doodle.parse("flow: Hello\n> sub\n@sketch @vertical\n// comment\nA\nB\n")
        self.assertEqual((spec.kind, spec.title, spec.sub), ("flow", "Hello", ["sub"]))
        self.assertEqual(spec.opts, {"sketch", "vertical"})
        self.assertEqual([r[1] for r in spec.rows], ["A", "B"])

    def test_unknown_kind(self):
        with self.assertRaisesRegex(doodle.DoodleError, "unknown kind 'pie'"):
            doodle.parse("pie: x\nA")

    def test_empty(self):
        with self.assertRaises(doodle.DoodleError):
            doodle.parse("\n// nothing\n")

    def test_cells(self):
        self.assertEqual(doodle.cells("A"), ("A", "", "neutral"))
        self.assertEqual(doodle.cells("A | note"), ("A", "note", "neutral"))
        self.assertEqual(doodle.cells("A | note | bad"), ("A", "note", "bad"))
        self.assertEqual(doodle.cells("A | error"), ("A", "", "bad"))
        self.assertEqual(doodle.cells("A | x | y | warning"), ("A", "x | y", "warn"))

    def test_edges(self):
        self.assertEqual(doodle.split_edge("A -> B"), ("A", "B", False, "", "neutral"))
        self.assertEqual(doodle.split_edge("A ~> B: hi | ok"), ("A", "B", True, "hi", "ok"))
        self.assertIsNone(doodle.split_edge("just a row"))


class WrapTest(unittest.TestCase):
    def test_wraps_within_width(self):
        lines = doodle.wrap("one two three four five six seven eight", 13, 80)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(doodle.tw(l, 13) <= 80 for l in lines))

    def test_long_word_is_split(self):
        lines = doodle.wrap("x" * 60, 13, 60)
        self.assertGreater(len(lines), 1)
        self.assertEqual("".join(lines), "x" * 60)

    def test_explicit_break(self):
        self.assertEqual(doodle.wrap("a\nb", 13, 500), ["a", "b"])


class RenderTest(unittest.TestCase):
    def check_svg(self, svg):
        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))
        w, h = int(root.get("width")), int(root.get("height"))
        self.assertEqual(root.get("viewBox"), "0 0 %d %d" % (w, h))
        return root, w, h

    def test_every_reference_example(self):
        found = blocks(DSL)
        self.assertGreaterEqual(len(found), 7)
        kinds = set()
        for src in found:
            spec, svg = doodle.render(src)
            kinds.add(spec.kind)
            self.check_svg(svg)
        self.assertEqual(kinds, set(doodle.KINDS))

    def test_every_docs_example(self):
        for path in DOCS:
            found = blocks(path)
            self.assertTrue(found, path)
            for src in found:
                self.check_svg(doodle.render(src)[1])

    def test_content_fits_canvas(self):
        for src in blocks(DSL):
            _, svg = doodle.render(src)
            _, w, h = self.check_svg(svg)
            for x, y in re.findall(r'<rect x="([\d.]+)" y="([\d.]+)"', svg):
                self.assertLess(float(x), w, src)
                self.assertLess(float(y), h, src)

    def test_dark_mode_and_sketch(self):
        _, svg = doodle.render("stack: S\n@sketch\nA | b | ok")
        self.assertIn("prefers-color-scheme:dark", svg)
        self.assertIn('filter="url(#rough)"', svg)
        self.assertNotIn("<text", svg.split('<g filter="url(#rough)">')[1].split("</g>")[0])

    def test_escaping(self):
        _, svg = doodle.render('flow: <a & "b">\nx < y | a & b')
        self.check_svg(svg)
        self.assertIn("&lt;a &amp; &quot;b&quot;&gt;", svg)

    def test_flow_auto_nodes_and_back_edge(self):
        _, svg = doodle.render("flow: F\nA -> B\nB -> C\nC -> A: again")
        self.check_svg(svg)
        self.assertEqual(svg.count('marker-end="url(#ah)"'), 3)

    def test_compare_items_inherit_column_tone(self):
        _, svg = doodle.render("compare: C\n## Bad | bad\nA\nB | x | ok")
        self.assertIn(doodle.ICON["bad"], svg)
        self.assertIn(doodle.ICON["ok"], svg)

    def test_errors(self):
        for src in ("cycle: c\nA", "compare: c", "sequence: s", "tree: t"):
            with self.assertRaises(doodle.DoodleError, msg=src):
                doodle.render(src)


class MarkdownTest(unittest.TestCase):
    def test_render_and_rerender(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "Topic.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write("# T\n\n```doodle\ncycle: Loop é\nA\nB --> C\n```\n\ntext\n\n"
                         "```doodle\nstack: Loop é\nA\n```\n")
            out = doodle.render_markdown(md)
            self.assertEqual(out, ["img/topic-loop-e.svg", "img/topic-loop-e-2.svg"])
            for rel in out:
                self.assertTrue(os.path.exists(os.path.join(tmp, rel)))
            with open(md, encoding="utf-8") as fh:
                first = fh.read()
            self.assertNotIn("```doodle", first)
            self.assertIn("![Loop é](img/topic-loop-e.svg)", first)
            self.assertIn("B - -> C", first)  # '-->' would close the HTML comment
            self.assertEqual(doodle.render_markdown(md), out)
            with open(md, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), first)

    def test_code_examples_are_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "doc.md")
            text = ("````md\n```doodle\nstack: no\nA\n```\n````\n\n"
                    "```\n<!-- doodle\nstack: no\nA\n-->\n![no](img/no.svg)\n```\n\n"
                    "```doodle\nstack: yes\nA\n```\n")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(text)
            self.assertEqual(doodle.render_markdown(md), ["img/doc-yes.svg"])
            with open(md, encoding="utf-8") as fh:
                result = fh.read()
            self.assertTrue(result.startswith(text[:text.index("```doodle\nstack: yes")]))
            self.assertFalse(os.path.exists(os.path.join(tmp, "img", "no.svg")))

    def test_two_node_cycle_does_not_overlap(self):
        spec = doodle.parse("cycle: c\nA | x\nB | y")
        cv = doodle.Canvas(spec)
        doodle.draw_cycle(cv, spec)
        xs = [float(x) for x in re.findall(r'<rect x="([\d.]+)" y="[\d.]+" width="210"', "".join(cv.parts))]
        self.assertEqual(len(xs), 2)
        self.assertGreater(abs(xs[1] - xs[0]), 210)

    def test_error_leaves_file_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "x.md")
            text = "```doodle\nnope: x\n```\n"
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(text)
            with self.assertRaises(doodle.DoodleError):
                doodle.render_markdown(md)
            with open(md, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), text)

    def test_unclosed_fences_are_preserved(self):
        for tail in ("```doodle", "```doodle\n", "  ~~~~doodle\nstack: Draft\nA\n"):
            with self.subTest(tail=tail), tempfile.TemporaryDirectory() as tmp:
                md = os.path.join(tmp, "draft.md")
                text = "# Draft\n\n" + tail
                with open(md, "w", encoding="utf-8") as fh:
                    fh.write(text)
                self.assertEqual(doodle.render_markdown(md), [])
                with open(md, encoding="utf-8") as fh:
                    self.assertEqual(fh.read(), text)

    def test_invalid_block_leaves_existing_images_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "topic.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write("```doodle\nstack: Valid\nOriginal\n```\n")
            rel = doodle.render_markdown(md)[0]
            svg = os.path.join(tmp, rel)
            with open(svg, encoding="utf-8") as fh:
                original_svg = fh.read()
            with open(md, encoding="utf-8") as fh:
                text = fh.read().replace("Original", "Changed")
            text += "\n```doodle\nstack: New\nA\n```\n\n```doodle\ninvalid: Bad\n```\n"
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(text)
            with self.assertRaises(doodle.DoodleError):
                doodle.render_markdown(md)
            with open(md, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), text)
            with open(svg, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), original_svg)
            self.assertEqual(os.listdir(os.path.join(tmp, "img")), [os.path.basename(svg)])

    def test_existing_comments_cannot_overwrite_other_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "topic.md")
            os.mkdir(os.path.join(tmp, "img"))
            targets = ["outside.svg", "img/../outside.svg", "img/../img-other/outside.svg",
                       "img/notes.md", os.path.join(tmp, "absolute.svg")]
            for rel in targets:
                with self.subTest(path=rel):
                    text = "<!-- doodle\nstack: Example\nA\n-->\n![Example](%s)\n" % rel
                    with open(md, "w", encoding="utf-8") as fh:
                        fh.write(text)
                    with self.assertRaisesRegex(doodle.DoodleError, "SVG output must stay inside"):
                        doodle.render_markdown(md)
                    with open(md, encoding="utf-8") as fh:
                        self.assertEqual(fh.read(), text)
            self.assertCountEqual(os.listdir(tmp), ["img", "topic.md"])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_existing_comments_cannot_follow_symlinks_outside_image_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.mkdir(os.path.join(tmp, "img"))
            target = os.path.join(tmp, "outside.svg")
            with open(target, "w", encoding="utf-8") as fh:
                fh.write("keep this")
            os.symlink(target, os.path.join(tmp, "img", "linked.svg"))
            md = os.path.join(tmp, "topic.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write("<!-- doodle\nstack: Example\nA\n-->\n![Example](img/linked.svg)\n")
            with self.assertRaises(doodle.DoodleError):
                doodle.render_markdown(md)
            with open(target, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "keep this")

    def test_custom_image_directory_can_be_rerendered(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "topic.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write("```doodle\nstack: Custom\nA\n```\n")
            expected = ["assets/diagrams/topic-custom.svg"]
            self.assertEqual(doodle.render_markdown(md, "assets/diagrams"), expected)
            self.assertEqual(doodle.render_markdown(md, "assets/diagrams"), expected)
            with self.assertRaises(doodle.DoodleError):
                doodle.render_markdown(md)


if __name__ == "__main__":
    unittest.main()
