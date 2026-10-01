"""Characterization of the marker/parity/substitution contract (Section A).

Locks today's behavior of scan_markers / audit_parity / audit_assets /
substitute — the functions the monthly cron and the PR lint job both stand on —
plus a real-file Golden Master over both READMEs and assets/."""
import contextlib
import io
import os
import pathlib
import re
import tempfile
import unittest

from tests._bps import NS, ROOT

scan_markers = NS["scan_markers"]
audit_parity = NS["audit_parity"]
audit_assets = NS["audit_assets"]
substitute = NS["substitute"]
FIG_SPEC = NS["FIG_SPEC"]
EN, ZH = NS["EN"], NS["ZH"]

# A minimal README skeleton exercising both marker kinds. Facts/alt stubs are
# intentionally unlike anything real so a byte-exact diff proves replacement.
_DOC = (
    "<!-- FIG:growth -->stale body<!-- /FIG:growth -->\n"
    "total <!-- DATA:cur_total -->old<!-- /DATA:cur_total --> now\n"
    "<!-- DATA:cur_year -->2020<!-- /DATA:cur_year -->\n"
)
_FACTS = {"cur_total": "9,313", "cur_year": "2026"}
_ALTS = {"growth": 'says "1, 0" & more'}
_STUB_FACTS = {k: "2026" if k == "cur_year" else "0" for k in NS["FACT_KEYS"]}
_STUB_ALTS = {k: "stub alt" for k in FIG_SPEC}


def _die_message(case, call):
    """Run `call`, returning (exit_code, stderr_text) of the expected die()."""
    err = io.StringIO()
    with case.assertRaises(SystemExit) as cm, contextlib.redirect_stderr(err):
        call()
    return cm.exception.code, err.getvalue()


class TestScanMarkers(unittest.TestCase):
    def test_wellformed_order(self):
        text = _DOC + "x <!-- FIG:streak -->y<!-- /FIG:streak -->"
        self.assertEqual(
            scan_markers(text, EN),
            [("FIG", "growth"), ("DATA", "cur_total"), ("DATA", "cur_year"),
             ("FIG", "streak")])

    def test_unknown_key_dies(self):
        code, err = _die_message(self, lambda: scan_markers(
            "<!-- DATA:nope -->1<!-- /DATA:nope -->", EN))
        self.assertEqual(code, 1)
        self.assertIn("not derivable", err)

    def test_nested_region_dies(self):
        code, err = _die_message(self, lambda: scan_markers(
            "<!-- FIG:growth --><!-- DATA:cur_year --><!-- /DATA:cur_year -->"
            "<!-- /FIG:growth -->", EN))
        self.assertEqual(code, 1)
        self.assertIn("nested", err)

    def test_unclosed_region_dies(self):
        code, err = _die_message(self, lambda: scan_markers(
            "<!-- FIG:growth -->body", EN))
        self.assertEqual(code, 1)
        self.assertIn("unclosed", err)

    def test_mismatched_closer_dies(self):
        code, err = _die_message(self, lambda: scan_markers(
            "<!-- FIG:growth -->body<!-- /FIG:streak -->", EN))
        self.assertEqual(code, 1)
        self.assertIn("does not close", err)


class TestSubstitute(unittest.TestCase):
    def test_fig_body_rebuilt_from_spec_exactly(self):
        out = substitute(_DOC, EN, _FACTS, _ALTS)
        # html.escape(alt, quote=True): quotes become entities, amp doubled.
        expected_img = ('<img src="assets/growth.svg" width="700" '
                        'alt="says &quot;1, 0&quot; &amp; more" />')
        self.assertIn(
            f"<!-- FIG:growth -->{expected_img}<!-- /FIG:growth -->", out)
        self.assertNotIn("stale body", out)

    def test_zh_src_is_absolute(self):
        out = substitute(_DOC, ZH, _FACTS, _ALTS)
        self.assertIn('src="https://raw.githubusercontent.com/ThreeFish-AI/'
                      'threefish-ai/master/assets/growth.svg"', out)

    def test_data_bodies_replaced_multiline(self):
        doc = "<!-- DATA:cur_total -->old\nspans lines<!-- /DATA:cur_total -->"
        self.assertIn("<!-- DATA:cur_total -->9,313<!-- /DATA:cur_total -->",
                      substitute(doc, EN, _FACTS, _ALTS))

    def test_backreference_mismatch_leaves_body_untouched(self):
        doc = "<!-- FIG:growth -->keep me<!-- /FIG:streak -->"
        self.assertEqual(substitute(doc, EN, _FACTS, _ALTS), doc)

    def test_text_outside_regions_is_byte_identical(self):
        def skeleton(t):
            t = re.sub(r"(<!-- DATA:([a-z0-9_]+) -->).*?(<!-- /DATA:\2 -->)",
                       r"\1\3", t, flags=re.S)
            return re.sub(r"(<!-- FIG:([a-z0-9_]+) -->).*?(<!-- /FIG:\2 -->)",
                          r"\1\3", t, flags=re.S)
        for f in (EN, ZH):
            text = (ROOT / f).read_text(encoding="utf-8")
            once = substitute(text, f, _STUB_FACTS, _STUB_ALTS)
            self.assertEqual(skeleton(text), skeleton(once), f)
            self.assertEqual(substitute(once, f, _STUB_FACTS, _STUB_ALTS),
                             once, f"{f}: not idempotent")


class TestAuditParity(unittest.TestCase):
    def test_identical_streams_pass(self):
        order = [("FIG", "growth"), ("DATA", "cur_total")]
        audit_parity({EN: order, ZH: list(order)})

    def test_drift_dies(self):
        a = [("FIG", "growth"), ("DATA", "cur_total")]
        b = [("FIG", "growth"), ("DATA", "cur_year")]
        code, err = _die_message(
            self, lambda: audit_parity({EN: a, ZH: b}))
        self.assertEqual(code, 1)
        self.assertIn("region 1 differs", err)

    def test_length_drift_dies(self):
        a = [("FIG", "growth")]
        b = [("FIG", "growth"), ("DATA", "cur_total")]
        code, err = _die_message(
            self, lambda: audit_parity({EN: a, ZH: b}))
        self.assertEqual(code, 1)
        self.assertIn("extra region", err)

    def test_empty_contract_dies(self):
        code, err = _die_message(
            self, lambda: audit_parity({EN: [], ZH: []}))
        self.assertEqual(code, 1)
        self.assertIn("no refreshable regions", err)


class TestAuditAssets(unittest.TestCase):
    def test_real_assets_dir_passes(self):
        audit_assets()  # cwd is the repo root while unittest runs from ROOT

    def test_stray_file_dies(self):
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            pathlib.Path(tmp, "assets").mkdir()
            pathlib.Path(tmp, "assets", "growth.svg").write_text("ok")
            pathlib.Path(tmp, "assets", "sprite.png").write_bytes(b"\x89")
            try:
                os.chdir(tmp)
                code, err = _die_message(self, audit_assets)
            finally:
                os.chdir(cwd)
        self.assertEqual(code, 1)
        self.assertIn("ungenerated file", err)


class TestRealReadmesGoldenMaster(unittest.TestCase):
    """The contract as it stands on disk: identical marker streams, known
    counts, and figures in cluster order (the header tab layout of PR #8)."""

    def test_both_readmes_carry_identical_marker_stream(self):
        en = scan_markers((ROOT / EN).read_text(encoding="utf-8"), EN)
        zh = scan_markers((ROOT / ZH).read_text(encoding="utf-8"), ZH)
        self.assertEqual(en, zh)
        self.assertEqual(sum(1 for k, _ in en if k == "DATA"), 75)
        self.assertEqual(sum(1 for k, _ in en if k == "FIG"), 13)
        self.assertEqual(
            [key for kind, key in en if kind == "FIG"],
            ["growth", "rhythm", "punchcard", "surplus", "ground",
             "accrual", "lifecycles", "cadence", "streak",
             "latency", "grammar", "tongues", "upstream"])


if __name__ == "__main__":
    unittest.main()
