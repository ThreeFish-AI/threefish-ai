"""Characterization of the SVG write gates (Section C) and three
representative renderers (Section C/D) as Golden Masters.

The 13 on-disk assets are the real renderers' Golden Master (all must pass
assert_svg_sane); crafted mutants lock each gate's refusal behavior; synthetic
inputs lock renderer output byte-for-byte (see tests/golden/)."""
import datetime
import pathlib
from collections import Counter
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
    """Synthetic inputs, byte-exact expectations for ALL 13 renderers: any
    structural change that alters rendering output by a byte fails here.
    Goldens are regenerated ONLY by a reviewed, deliberate act (the lab's
    gen_golden*.py scripts verify determinism and gate-cleanliness first)."""

    ASOF = "2026-09-05"
    ARIA = "synthetic aria"
    D = datetime.date
    DOMAIN = (D(2026, 1, 5), D(2026, 3, 1))

    def _cases(self):
        R, D, ASOF, ARIA = NS, self.D, self.ASOF, self.ARIA
        return {
            "growth": lambda: R["render_growth"](
                [1, 0, 0, 13, 129, 198, 676, 589, 1181, 3193, 9313],
                list(range(2016, 2027)), ASOF, ARIA),
            "rhythm": lambda: R["render_rhythm"](
                Counter({18: 400, 10: 200}), ASOF, ARIA),
            "ground": lambda: R["render_ground"](
                {"negentropy": 40, "coding-proxy": 12, "hyper-git": 7},
                {"coding-proxy": 3, "hyper-git": 1}, ASOF, ARIA),
            "punchcard": lambda: R["render_punchcard"](
                Counter({(0, 22): 30, (6, 21): 25, (3, 10): 12, (5, 23): 8}),
                self.DOMAIN, ASOF, ARIA),
            "surplus": lambda: R["render_surplus"](
                Counter({22: 60, 10: 30}), Counter({22: 80, 11: 20}),
                40, 12, self.DOMAIN, ASOF, ARIA),
            "accrual": lambda: R["render_accrual"](
                Counter({("negentropy", D(2026, 1, 1)): 20,
                         ("negentropy", D(2026, 2, 1)): 10,
                         ("hyper-git", D(2026, 2, 1)): 5}),
                [(D(2026, 2, 15), "hyper-git")], self.DOMAIN, ASOF, ARIA),
            "lifecycles": lambda: R["render_lifecycles"](
                [("negentropy", D(2026, 1, 1), D(2026, 3, 1), False),
                 ("old-wing", D(2025, 6, 1), D(2026, 2, 1), True)],
                (D(2025, 6, 1), D(2026, 3, 1)), ASOF, ARIA),
            "cadence": lambda: R["render_cadence"](
                {"coding-proxy": [
                    {"tag_name": "v0.1.0", "published_at": "2026-01-20T10:00:00Z",
                     "prerelease": False},
                    {"tag_name": "v0.2.0", "published_at": "2026-02-14T09:30:00Z",
                     "prerelease": True}],
                 "negentropy": [
                     {"tag_name": "v0.0.1", "published_at": "2026-02-01T08:00:00Z",
                      "prerelease": False}]},
                self.DOMAIN, ASOF, ARIA),
            "streak": lambda: R["render_streak"](
                {D(2026, 6, d): (d % 5) for d in range(1, 31)},
                (D(2026, 6, 10), D(2026, 6, 19)),
                (D(2026, 6, 1), D(2026, 6, 30)), ASOF, ARIA),
            "latency": lambda: R["render_latency"](
                [("<1m", 5), ("1-2", 2), ("2-5", 3), ("5-15", 4), ("15-60m", 3),
                 ("1-4h", 2), ("4-24h", 1), (">24h", 0)],
                [27.8, 38.9, 55.6, 77.8, 94.4, 100.0, 100.0, 100.0],
                {"n": 20, "unmerged": 2, "med": "6 min", "p90": "2.8 h",
                 "med_i": 3, "hour_i": 4, "lat_max": "11.9 d"}, ASOF, ARIA),
            "grammar": lambda: R["render_grammar"](
                [("fix", 827), ("docs", 725), ("feat", 697), ("test", 6)],
                996, 4349, 19.0, ASOF, ARIA),
            "tongues": lambda: R["render_tongues"](
                Counter({"HTML": 50000, "Python": 20000, "TypeScript": 8000}),
                Counter({"Python": 20000, "TypeScript": 8000, "HTML": 500}),
                "threefish-ai.github.io", [], ASOF, ARIA),
            "upstream": lambda: R["render_upstream"](
                [{"html_url": "https://github.com/langgenius/dify/pull/1",
                  "repository_url": "https://api.github.com/repos/langgenius/dify",
                  "state": "closed",
                  "pull_request": {"merged_at": "2026-01-10T00:00:00Z"},
                  "number": 5631, "created_at": "2026-01-09T00:00:00Z"},
                 {"html_url": "https://github.com/foo/bar/pull/2",
                  "repository_url": "https://api.github.com/repos/foo/bar",
                  "state": "closed",
                  "pull_request": {"merged_at": None},
                  "number": 124, "created_at": "2026-02-01T00:00:00Z"}],
                500, ASOF, ARIA),
        }

    def test_all_renderers_match_goldens(self):
        for name, render in self._cases().items():
            with self.subTest(figure=name):
                actual = render()
                assert_svg_sane(actual, name)  # goldens must be gate-clean
                expected = (GOLDEN / f"{name}_synthetic.svg").read_text(
                    encoding="utf-8")
                self.assertEqual(actual, expected)

    def test_golden_files_are_exactly_thirteen(self):
        self.assertEqual(
            sorted(p.name for p in GOLDEN.glob("*.svg")),
            [f"{k}_synthetic.svg" for k in sorted(self._cases())])


if __name__ == "__main__":
    unittest.main()
