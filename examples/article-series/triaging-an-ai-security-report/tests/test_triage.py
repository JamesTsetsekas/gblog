import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

from triage import sandbox
from triage.claims import CLAIMS
from triage.reachability import reachable_functions
from triage.regression import SIBLING_VARIANTS, regression_failures
from triage.run_triage import LEDGER_PATH, build_ledger


class Tree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.paths = sandbox.build(self._tmp.name)
        self.vulnerable = importlib.import_module("minishare.vulnerable")
        self.fixed = importlib.import_module("minishare.fixed")

    def run_claims(self, module):
        return {cid: fn(module, self.paths) for cid, _, fn in CLAIMS}


class ClaimReproduction(Tree):
    def test_c1_sibling_prefix_is_reproduced_on_the_vulnerable_version(self):
        self.assertTrue(self.run_claims(self.vulnerable)["C1"]["disclosed"])

    def test_c2_arbitrary_file_read_is_not_reproduced(self):
        obs = self.run_claims(self.vulnerable)["C2"]
        self.assertFalse(obs["disclosed"])
        self.assertEqual(obs["exception"], "PermissionError")

    def test_c3_absolute_path_is_not_reproduced(self):
        obs = self.run_claims(self.vulnerable)["C3"]
        self.assertFalse(obs["disclosed"])
        self.assertEqual(obs["exception"], "PermissionError")

    def test_c4_reproduces_but_the_null_byte_is_not_the_mechanism(self):
        obs = self.run_claims(self.vulnerable)["C4"]
        self.assertTrue(obs["disclosed"])
        self.assertFalse(obs["claimed_mechanism_needed"])

    def test_a_real_null_byte_is_an_error_not_a_bypass(self):
        with self.assertRaises(ValueError):
            self.vulnerable.download(self.paths["base"], "readme.txt" + chr(0))

    def test_c5_has_no_declared_call_path_but_remains_importable(self):
        self.assertTrue(self.run_claims(self.vulnerable)["C5"]["disclosed"])
        reachable = reachable_functions(self.vulnerable)
        self.assertNotIn("_legacy_read", reachable)
        self.assertIn("_safe_path", reachable)
        self.assertTrue(callable(getattr(self.vulnerable, "_legacy_read")))

    def test_reachability_heuristic_sees_a_planted_call(self):
        # Guard against the heuristic silently returning "unreachable" for everything.
        import importlib.util
        src = "\n".join([
            "__all__ = ['entry']",
            "def entry():",
            "    return helper()",
            "def helper():",
            "    return 1",
            "def dead():",
            "    return 2",
            "",
        ])
        path = os.path.join(self._tmp.name, "planted.py")
        with open(path, "w") as handle:
            handle.write(src)
        spec = importlib.util.spec_from_file_location("planted", path)
        planted = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(planted)
        self.assertEqual(reachable_functions(planted), {"entry", "helper"})


class Patch(Tree):
    def test_existing_symlink_escape_is_blocked_in_stable_tree(self):
        base = Path(self.paths["base"])
        target = Path(self._tmp.name) / "symlink-target"
        target.mkdir()
        (target / "marker.txt").write_bytes(b"synthetic outside marker")
        link = base / "linked-outside"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"symlink creation unavailable: {error}")
        with self.assertRaises(PermissionError):
            self.fixed.download(str(base), "linked-outside/marker.txt")

    def test_fixed_version_blocks_every_claim(self):
        for cid, obs in self.run_claims(self.fixed).items():
            self.assertFalse(obs["disclosed"], cid)

    def test_regression_checks_pass_on_the_fixed_version(self):
        self.assertEqual(regression_failures(self.fixed, self.paths), [])

    def test_regression_checks_fail_on_the_vulnerable_version(self):
        failures = regression_failures(self.vulnerable, self.paths)
        # One failure per sibling variant, plus the trailing-slash base case.
        self.assertGreaterEqual(len(failures), len(SIBLING_VARIANTS) + 1)
        self.assertTrue(all("legitimate path" not in f for f in failures),
                        "the vulnerable version should still serve legitimate paths")

    def test_fix_does_not_break_legitimate_reads_or_listing(self):
        self.assertEqual(self.fixed.download(self.paths["base"], "docs/guide.txt"), b"public guide")
        self.assertEqual(self.fixed.list_names(self.paths["base"]),
                         self.vulnerable.list_names(self.paths["base"]))


class Ledger(unittest.TestCase):
    def test_committed_ledger_matches_the_harness(self):
        with open(LEDGER_PATH, encoding="utf-8") as handle:
            committed = json.load(handle)
        self.assertEqual(committed, build_ledger())

    def test_ledger_decisions(self):
        decisions = {c["id"]: c["decision"] for c in build_ledger()["claims"]}
        self.assertEqual(decisions["C1"], "confirmed vulnerability")
        self.assertTrue(decisions["C2"].startswith("not reproduced"))
        self.assertTrue(decisions["C3"].startswith("not reproduced"))
        self.assertTrue(decisions["C4"].startswith("duplicate of C1"))
        self.assertIn("security classification needs wider review", decisions["C5"])
        c5 = next(c for c in build_ledger()["claims"] if c["id"] == "C5")
        self.assertFalse(c5["reachable_from_declared_entry_points"])


if __name__ == "__main__":
    unittest.main()
