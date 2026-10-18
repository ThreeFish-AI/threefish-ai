"""Machine guards for the README contracts that --lint cannot see (Section B2).

The marker stream, its parity and the assets closure are audited by
scripts/build_profile_svgs.py --lint on every PR. Three load-bearing surfaces
used to rest on human discipline only; these tests lock them:

1. Anchor triple-consistency — every <summary><a name="X"> anchor, every
   #user-content-X link in the two cluster-nav <sub> rows, and every FIG key
   must be the same set, anchors in FIG-cluster order. A broken link here
   fails silently on GitHub (the user-content- prefix is renderer-side).
2. Bilingual line-mirror — the two READMEs must carry their markers and their
   structural skeleton (details/summary/anchors/tables/code fences) at
   identical line numbers, and stay the same length. Prose may differ; the
   shape may not.
3. Monotonicity state source — DATA:cur_year/DATA:cur_total must survive in
   both files: the monthly refresh reads them back from disk as its only
   state (see main() in the generator).
"""
import re
import unittest

from tests._bps import ROOT

EN, ZH = "README.md", "docs/i18n/zh-CN/README.md"

MARKER = re.compile(r"<!-- (/?)(DATA|FIG):([a-z0-9_]+) -->")
FIG_OPEN = re.compile(r"<!-- FIG:([a-z0-9_]+) -->")
ANCHOR = re.compile(r'<a name="([a-z]+)"></a>')
NAV = re.compile(r"#user-content-([a-z]+)")
SKELETON = re.compile(
    r"<details|</details|<summary|```|^---$|^### |^\[\^|#user-content-|<a name=")


def _lines(rel):
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()


class TestAnchorTripleConsistency(unittest.TestCase):
    def test_anchors_fig_keys_and_nav_links_are_one_set_per_file(self):
        for rel in (EN, ZH):
            lines = _lines(rel)
            figs = [m.group(1) for l in lines for m in FIG_OPEN.finditer(l)]
            anchors = [m.group(1) for l in lines for m in ANCHOR.finditer(l)]
            navs = sorted(m.group(1) for l in lines for m in NAV.finditer(l))
            self.assertEqual(figs, anchors, f"{rel}: anchor order != FIG order")
            self.assertEqual(sorted(anchors), navs, f"{rel}: nav links != anchors")


class TestBilingualLineMirror(unittest.TestCase):
    def test_markers_sit_on_identical_line_numbers(self):
        for pat in (MARKER, SKELETON):
            en = [i + 1 for i, l in enumerate(_lines(EN)) if pat.search(l)]
            zh = [i + 1 for i, l in enumerate(_lines(ZH)) if pat.search(l)]
            self.assertEqual(en, zh, f"line drift under {pat.pattern}")

    def test_same_length(self):
        self.assertEqual(len(_lines(EN)), len(_lines(ZH)))


class TestMonotonicityStateSource(unittest.TestCase):
    def test_cur_year_and_total_survive_in_both_files(self):
        for rel in (EN, ZH):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertRegex(text, r"<!-- DATA:cur_year -->\d{4}<!-- /DATA:cur_year -->")
            self.assertRegex(text, r"<!-- DATA:cur_total -->[\d,]+<!-- /DATA:cur_total -->")


if __name__ == "__main__":
    unittest.main()
