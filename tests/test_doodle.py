import contextlib
import io
import json
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
    os.path.join(ROOT, "skills", "doodle", "SKILL.md"),
    os.path.join(ROOT, "README.md"), os.path.join(ROOT, "README.pt-BR.md")]


def blocks(path):
    with open(path, encoding="utf-8") as fh:
        return doodle.FENCE.findall(fh.read())


def cli(args):
    """Run the command line quietly; returns the exit code."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return doodle.main(args)


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


class LintTest(unittest.TestCase):
    def warnings(self, src):
        return [m for _no, m in doodle.render(src)[0].warnings]

    def test_clean_spec_has_no_warnings(self):
        for src in blocks(DSL):
            self.assertEqual(self.warnings(src), [], src)

    def test_unknown_and_misplaced_options(self):
        spec = doodle.parse("stack: S\n@arow @vertical\nA")
        msgs = dict((m.split("'")[1], no) for no, m in spec.warnings)
        self.assertIn("@arow", msgs)
        self.assertEqual(msgs["@arow"], 2)
        self.assertTrue(any("did you mean 'arrow'" in m for _n, m in spec.warnings))
        self.assertTrue(any("'@vertical' has no effect on stack" in m for _n, m in spec.warnings))

    def test_tone_typo(self):
        ws = self.warnings("stack: S\nA | note | warnn")
        self.assertTrue(any("write warn" in w for w in ws), ws)
        self.assertEqual(self.warnings("stack: S\nA | note | lunch"), [])

    def test_long_text_and_many_rows(self):
        ws = self.warnings("stack: S\nOne two three four five six seven\n" + "X\n" * 8)
        self.assertTrue(any("label has 7 words" in w for w in ws))
        self.assertTrue(any("9 rows" in w for w in ws))

    def test_flow_edge_typo_creates_node_with_warning(self):
        spec, _ = doodle.render("flow: F\n[a] Start\n[b] Home\na -> Hom")
        self.assertEqual(spec.warnings[0][0], 4)
        self.assertIn("did you mean 'Home'", spec.warnings[0][1])
        self.assertEqual(self.warnings("flow: F\nA -> B"), [])  # no declared nodes: creating is the intent

    def test_sequence_actor_typo(self):
        ws = self.warnings("sequence: S\nBrowser -> Server: hi\nBrowsr -> Server: again")
        self.assertTrue(any("did you mean 'Browser'" in w for w in ws), ws)

    def test_markdown_warnings_point_at_document_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "t.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write("# T\n\n```doodle\nstack: S\nA | x | okk\n```\n\n<!-- doodle\nstack: R\n@arow\nB\n-->\n"
                         "![R](img/t-r.svg)\n")
            warnings = []
            doodle.render_markdown(md, warnings=warnings)
            self.assertEqual([w.split(":")[1] for w in warnings], ["5", "10"])

    def test_check_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "t.md")
            text = "```doodle\nstack: S\nA\n```\n"
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(text)
            self.assertEqual(cli([md, "--check"]), 0)
            with open(md, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), text)
            self.assertEqual(os.listdir(tmp), ["t.md"])
            with open(md, "w", encoding="utf-8") as fh:
                fh.write("```doodle\npie: S\n```\n")
            self.assertEqual(cli([md, "--check"]), 1)

    def test_error_lines_point_at_document_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "t.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write("# T\n\n```doodle\n// draft\npie: S\n```\n")
            with self.assertRaisesRegex(doodle.DoodleError, r"t\.md:5: unknown kind 'pie'"):
                doodle.render_markdown(md)


class StyleTest(unittest.TestCase):
    def test_every_theme_renders_valid_svg(self):
        for name in doodle.THEMES:
            with self.subTest(theme=name):
                _, svg = doodle.render("flow: F\nA | x | ok\nB | y | bad", doodle.Style(theme=name))
                ET.fromstring(svg)
                self.assertIn(doodle.THEMES[name]["light"]["bg"], svg)

    def test_block_theme_option(self):
        spec, svg = doodle.render("stack: S\n@theme blueprint @arrow\nA\nB")
        self.assertEqual(spec.theme, "blueprint")
        self.assertEqual(spec.opts, {"arrow"})
        self.assertIn('id="grid"', svg)
        self.assertEqual(doodle.parse("stack: S\n@theme=chalk\nA").theme, "chalk")

    def test_unknown_theme_suggests(self):
        with self.assertRaisesRegex(doodle.DoodleError, "did you mean 'chalk'"):
            doodle.render("stack: S\n@theme chalck\nA")

    def test_chalk_is_sketchy_by_default(self):
        self.assertTrue(doodle.Style(theme="chalk").sketch)
        self.assertFalse(doodle.Style(theme="chalk", sketch=False).sketch)

    def test_scheme(self):
        auto = doodle.Style().css()
        self.assertIn("prefers-color-scheme:dark", auto)
        light = doodle.Style(scheme="light").css()
        self.assertNotIn("prefers-color-scheme", light)
        self.assertIn(doodle.PAPER_LIGHT["bg"], light)
        dark = doodle.Style(scheme="dark").css()
        self.assertIn(doodle.PAPER_DARK["bg"], dark)
        self.assertNotIn(doodle.PAPER_LIGHT["bg"], dark)

    def test_custom_colors_and_dark_derivation(self):
        st = doodle.Style(colors={"info": "#7c3aed", "bg": "#ffffff", "error": "#ff0000"})
        self.assertEqual(st.light["info"][1], "#7c3aed")
        self.assertEqual(st.light["bad"][1], "#ff0000")  # tone aliases work as color names
        self.assertEqual(st.light["bg"], "#ffffff")
        self.assertNotEqual(st.dark["info"][1], "#7c3aed")  # lightened for dark backgrounds
        self.assertEqual(st.dark["bg"], doodle.PAPER_DARK["bg"])
        st = doodle.Style(colors={"ok": "#00aa00"}, dark_colors={"ok": "#33ff33"})
        self.assertEqual(st.dark["ok"][1], "#33ff33")

    def test_bad_colors(self):
        with self.assertRaisesRegex(doodle.DoodleError, "must look like"):
            doodle.Style(colors={"info": "purple"})
        with self.assertRaisesRegex(doodle.DoodleError, "unknown color"):
            doodle.Style(colors={"accent": "#123456"})

    def test_frame_off_and_no_shadow(self):
        _, svg = doodle.render("stack: S\nA", doodle.Style(theme="clean", frame=False))
        self.assertNotIn('class="bg"', svg)
        self.assertNotIn("url(#sh)", svg)

    def test_description_for_screen_readers(self):
        _, svg = doodle.render("flow: F\n[a] Start | go | ok\na -> B: next")
        self.assertIn("<desc>Start - go; a -&gt; B: next</desc>", svg)

    def test_badge_text_contrasts_in_dark_mode(self):
        self.assertEqual(doodle.PAPER_DARK["on"], doodle.PAPER_DARK["bg"])


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.old = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = os.path.join(self.root, "xdg")

    def tearDown(self):
        if self.old is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.old
        self.tmp.cleanup()

    def write(self, rel, data):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(data if isinstance(data, str) else json.dumps(data))
        return path

    def test_defaults(self):
        s = doodle.load_settings(self.root)
        self.assertEqual((s["theme"], s["audience"], s["sources"]), ("paper", "beginner", []))

    def test_project_overrides_user_and_merges_colors(self):
        self.write("xdg/doodle/config.json", {"theme": "candy", "audience": "kid", "colors": {"info": "#111111"}})
        self.write("repo/.git/HEAD", "")
        self.write("repo/doodle.json", {"theme": "clean", "colors": {"ok": "#222222"}})
        os.makedirs(os.path.join(self.root, "repo", "docs", "deep"))
        s = doodle.load_settings(os.path.join(self.root, "repo", "docs", "deep"))
        self.assertEqual((s["theme"], s["audience"]), ("clean", "kid"))
        self.assertEqual(s["colors"], {"info": "#111111", "ok": "#222222"})
        self.assertEqual(len(s["sources"]), 2)

    def test_search_stops_at_repository_root(self):
        self.write("doodle.json", {"theme": "chalk"})
        self.write("repo/.git/HEAD", "")
        self.assertEqual(doodle.load_settings(os.path.join(self.root, "repo"))["theme"], "paper")

    def test_validation(self):
        warnings = []
        self.write("doodle.json", {"theme": "clean", "colour": {}})
        doodle.load_settings(self.root, warnings=warnings)
        self.assertTrue(any("unknown setting 'colour'" in w for w in warnings))
        self.write("doodle.json", {"audience": "toddler"})
        with self.assertRaisesRegex(doodle.DoodleError, "audience"):
            doodle.load_settings(self.root)
        self.write("doodle.json", "{oops")
        with self.assertRaisesRegex(doodle.DoodleError, "invalid JSON"):
            doodle.load_settings(self.root)

    def test_markdown_uses_project_settings(self):
        self.write("doodle.json", {"theme": "blueprint", "imageDir": "figures"})
        md = self.write("topic.md", "```doodle\nstack: S\nA\n```\n")
        self.assertEqual(cli([md, "-q"]), 0)
        with open(os.path.join(self.root, "figures", "topic-s.svg"), encoding="utf-8") as fh:
            self.assertIn('id="grid"', fh.read())

    def test_cli_flags_win(self):
        self.write("doodle.json", {"theme": "blueprint"})
        spec = self.write("s.txt", "stack: S\nA\n")
        self.assertEqual(cli([spec, "--theme", "clean", "--scheme", "light"]), 0)
        with open(os.path.join(self.root, "s.svg"), encoding="utf-8") as fh:
            svg = fh.read()
        self.assertNotIn('id="grid"', svg)
        self.assertNotIn("prefers-color-scheme", svg)

    def test_init_and_settings_commands(self):
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            self.assertEqual(cli(["--init"]), 0)
            self.assertEqual(cli(["--init"]), 1)  # never overwrites
            with open("doodle.json", encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["theme"], "paper")
        finally:
            os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
