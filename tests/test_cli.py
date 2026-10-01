"""Characterization of the CLI boundary: --lint is the exact audit the PR CI
job runs (zero network), and an unknown argument must die without writing."""
import subprocess
import sys
import unittest

from tests._bps import ROOT


class TestCliLint(unittest.TestCase):
    def test_lint_passes_with_stable_output_format(self):
        r = subprocess.run(
            [sys.executable, "scripts/build_profile_svgs.py", "--lint"],
            cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("OK  lint: "), r.stdout)
        self.assertIn("DATA + ", r.stdout)
        self.assertIn(
            "identical set and order in both READMEs; assets/ clean",
            r.stdout)

    def test_unknown_argument_dies(self):
        r = subprocess.run(
            [sys.executable, "scripts/build_profile_svgs.py", "--bogus"],
            cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stderr.startswith("ABORT:"), r.stderr)


if __name__ == "__main__":
    unittest.main()
