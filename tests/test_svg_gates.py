"""Characterization of the SVG write gates (Section C) and three
representative renderers (Section C/D) as Golden Masters.

The 13 on-disk assets are the real renderers' Golden Master (all must pass
assert_svg_sane); crafted mutants lock each gate's refusal behavior; synthetic
inputs lock renderer output byte-for-byte (see tests/golden/)."""
import datetime
import pathlib
import unittest

from tests._bps import NS, ROOT

assert_svg_sane = NS["assert_svg_sane"]

ASSETS = ROOT / "assets"
GOLDEN = ROOT / "tests" / "golden"

# A gate-clean chassis: role/aria, viewBox, well-formed, tiny, no motion.
_CHASSIS = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="700" height="40" '
    'viewBox="0 0 700 40" role="img" aria-label="chassis">'
    '<text x="10" y="24" font-size="12" class="lbl">ok</text></svg>')


class TestRealAssetsPassGates(unittest.TestCase):
    def test_all_thirteen_assets_pass(self):
        svgs = sorted(p.name for p in ASSETS.glob("*.svg"))
        self.assertEqual(len(svgs), 13)
        for name in svgs:
            n = assert_svg_sane((ASSETS / name).read_text(encoding="utf-8"),
                                name)
            self.assertLessEqual(n, 8192, name)


class TestGateRefusals(unittest.TestCase):
    def test_loop_animation_banned(self):
        src = _CHASSIS.replace("ok", "infinite")
        with self.assertRaises(AssertionError) as cm:
            assert_svg_sane(src, "mutant")
        self.assertIn("infinite/indefinite loop", str(cm.exception))

    def test_fill_only_class_on_stroked_mark(self):
        src = _CHASSIS.replace("</svg>",
                               '<line class="bar" x1="0" y1="30" x2="50" '
                               'y2="30"/></svg>')
        with self.assertRaises(AssertionError) as cm:
            assert_svg_sane(src, "mutant")
        self.assertIn("carries fill-only class", str(cm.exception))

    def test_label_past_right_edge(self):
        long_label = "label_" + "x" * 200  # ~1.2kpx at 12px, past the 700px canvas
        src = _CHASSIS.replace(">ok</text>", f">{long_label}</text>")
        with self.assertRaises(AssertionError) as cm:
            assert_svg_sane(src, "mutant")
        self.assertIn("past the 700px canvas", str(cm.exception))

    def test_labels_overlapping_on_shared_baseline(self):
        src = _CHASSIS.replace(
            "</svg>",
            '<text x="10" y="24" font-size="12" class="lbl">aaaaaaaaaa</text>'
            '<text x="12" y="24" font-size="12" class="lbl">bbbbbbbbbb</text>'
            "</svg>")
        with self.assertRaises(AssertionError) as cm:
            assert_svg_sane(src, "mutant")
        self.assertIn("overlap on baseline", str(cm.exception))

    def test_a11y_metadata_missing(self):
        src = _CHASSIS.replace(' role="img" aria-label="chassis"', "")
        with self.assertRaises(AssertionError) as cm:
            assert_svg_sane(src, "mutant")
        self.assertIn("a11y metadata missing", str(cm.exception))

    def test_malformed_xml(self):
        src = _CHASSIS.replace("ok", "a < b")
        with self.assertRaises(AssertionError) as cm:
            assert_svg_sane(src, "mutant")
        self.assertIn("not well-formed XML", str(cm.exception))

    def test_byte_budget(self):
        padding = "<!--" + "p" * 8300 + "-->"
        src = _CHASSIS.replace("</svg>", padding + "</svg>")
        with self.assertRaises(AssertionError) as cm:
            assert_svg_sane(src, "mutant")
        self.assertIn("over budget", str(cm.exception))

    def test_external_resource(self):
        src = _CHASSIS.replace("ok", "@import url(x)")
        with self.assertRaises(AssertionError) as cm:
            assert_svg_sane(src, "mutant")
        self.assertIn("external resource", str(cm.exception))

    def test_motion_must_be_opt_in(self):
        src = _CHASSIS.replace(
            "</svg>",
            "<style>.x{animation:fade 1s both}</style></svg>")
        with self.assertRaises(AssertionError) as cm:
            assert_svg_sane(src, "mutant")
        self.assertIn("motion not opt-in", str(cm.exception))


class TestRendererGoldenMaster(unittest.TestCase):
    """Synthetic inputs, byte-exact expectations: any structural change that
    alters rendering output by a pixel fails here. Goldens are regenerated
    ONLY by a reviewed, deliberate act (see lab progress notes)."""

    GROWTH_VALUES = [1, 0, 0, 13, 129, 198, 676, 589, 1181, 3193, 9313]
    GROWTH_YEARS = list(range(2016, 2027))
    ASOF = "2026-09-05"

    STREAK_DOM = (datetime.date(2026, 6, 1), datetime.date(2026, 6, 30))
    STREAK_RUN = (datetime.date(2026, 6, 10), datetime.date(2026, 6, 19))
    STREAK_DAYS = {datetime.date(2026, 6, d): (d % 5) for d in range(1, 31)}

    GRAMMAR_TYPES = [("fix", 827), ("docs", 725), ("feat", 697), ("test", 6)]

    def _golden(self, name, render):
        actual = render()
        assert_svg_sane(actual, name)  # goldens must themselves be gate-clean
        expected = (GOLDEN / f"{name}.svg").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)

    def test_growth(self):
        self._golden(
            "growth_synthetic",
            lambda: NS["render_growth"](self.GROWTH_VALUES, self.GROWTH_YEARS,
                                        self.ASOF, "synthetic aria"))

    def test_streak(self):
        self._golden(
            "streak_synthetic",
            lambda: NS["render_streak"](self.STREAK_DAYS, self.STREAK_RUN,
                                        self.STREAK_DOM, self.ASOF,
                                        "synthetic aria"))

    def test_grammar(self):
        self._golden(
            "grammar_synthetic",
            lambda: NS["render_grammar"](self.GRAMMAR_TYPES, 996, 4349, 19.0,
                                         self.ASOF, "synthetic aria"))


if __name__ == "__main__":
    unittest.main()
