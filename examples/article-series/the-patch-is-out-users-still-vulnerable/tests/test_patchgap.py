import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from patchgap import (build_plan, classify, in_scope, load_fleet, mitigate,
                      naive_classification, remediate, run_rollout, verify)


def ids_where(fleet, predicate):
    return {i for i, a in fleet.assets.items() if predicate(a)}


class Inventory(unittest.TestCase):
    def setUp(self):
        self.fleet = load_fleet()

    def test_package_version_scan_gets_two_assets_wrong(self):
        naive = ids_where(self.fleet, lambda a: naive_classification(a) == "affected")
        evidence = ids_where(self.fleet, lambda a: classify(a)["status"] in ("affected", "mitigated", "unknown"))
        self.assertEqual(naive, {"api-1", "edge-1", "tool-1", "web-1", "web-2", "web-4", "worker-1"})
        self.assertEqual(evidence, {"api-1", "batch-1", "edge-1", "tool-1", "web-1", "web-2", "web-4"})
        self.assertEqual(naive - evidence, {"worker-1"})      # backported fix: scanner false positive
        self.assertEqual(evidence - naive, {"batch-1"})       # vendored copy: scanner false negative

    def test_priorities(self):
        self.assertEqual(classify(self.fleet.assets["web-1"])["priority"], "P1")
        self.assertEqual(classify(self.fleet.assets["batch-1"])["priority"], "P2")
        self.assertEqual(classify(self.fleet.assets["tool-1"])["status"], "mitigated")

    def test_unobserved_asset_is_flagged_as_declared_only(self):
        self.assertIn("not observed", classify(self.fleet.assets["edge-1"])["basis"])
        self.assertEqual(classify(self.fleet.assets["edge-1"])["status"], "unknown")

    def test_fixed_declaration_with_unreachable_probe_stays_in_scope(self):
        asset = self.fleet.assets["edge-1"]
        asset["package_version"] = "2.4.7"
        self.assertEqual(classify(asset)["status"], "unknown")
        self.assertEqual(classify(asset)["priority"], "P1")
        self.assertIn("edge-1", in_scope(self.fleet))
        self.assertIn("edge-1", {i for _, ids in build_plan(self.fleet) for i in ids})

    def test_missing_declared_and_observed_versions_are_unknown(self):
        asset = self.fleet.assets["edge-1"]
        asset["package_version"] = None
        asset["running_version"] = None
        self.assertEqual(classify(asset)["status"], "unknown")
        self.assertEqual(verify(self.fleet)["assets"]["edge-1"]["status"], "unknown")

    def test_backport_claim_requires_current_matching_verified_evidence(self):
        original = self.fleet.assets["worker-1"]
        self.assertEqual(classify(original)["status"], "not_affected")
        for field, value in [("source", ""), ("verified", False), ("current", False),
                             ("package_version", "2.3.0")]:
            with self.subTest(field=field):
                asset = copy.deepcopy(original)
                asset["backport_evidence"][field] = value
                self.assertEqual(classify(asset)["status"], "unknown")
        asset = copy.deepcopy(original)
        del asset["backport_evidence"]
        self.assertEqual(classify(asset)["status"], "unknown")

    def test_plan_puts_the_canary_first_and_skips_unaffected_assets(self):
        plan = build_plan(self.fleet)
        self.assertEqual([name for name, _ in plan],
                         ["canary", "ring1-internet", "ring2-internal", "ring3-mitigated"])
        self.assertEqual(plan[0][1], ["web-2"])
        planned = {i for _, ids in plan for i in ids}
        self.assertNotIn("web-3", planned)
        self.assertNotIn("worker-1", planned)


class HappyPath(unittest.TestCase):
    def setUp(self):
        self.fleet = load_fleet()
        self.scope = in_scope(self.fleet)
        self.outcome = run_rollout(self.fleet, build_plan(self.fleet))

    def test_every_ring_completes(self):
        self.assertIsNone(self.outcome["halted_at"])
        self.assertEqual(len(self.outcome["rings_completed"]), 4)

    def test_job_success_overstates_what_is_fixed(self):
        report = verify(self.fleet, self.scope)
        self.assertEqual(self.outcome["jobs_reported_ok"], 7)
        self.assertEqual(report["counts"], {"fixed": 3, "still_vulnerable": 3, "unknown": 1})
        self.assertGreater(self.outcome["jobs_reported_ok"], report["counts"]["fixed"])

    def test_each_gap_has_a_specific_reason(self):
        rows = verify(self.fleet, self.scope)["assets"]
        self.assertEqual(rows["web-1"]["reason"], "package updated but the old process is still running")
        self.assertEqual(rows["api-1"]["reason"], "pinned image digest was not bumped")
        self.assertEqual(rows["batch-1"]["reason"], "vendored copy was not updated")
        self.assertEqual(rows["edge-1"]["status"], "unknown")

    def test_remediation_closes_what_automation_can_and_names_the_rest(self):
        actions = dict(remediate(self.fleet, verify(self.fleet, self.scope)))
        self.assertEqual(verify(self.fleet, self.scope)["counts"],
                         {"fixed": 5, "still_vulnerable": 1, "unknown": 1})
        self.assertTrue(actions["batch-1"].startswith("MANUAL"))
        self.assertTrue(actions["edge-1"].startswith("MANUAL"))
        self.assertFalse(actions["web-1"].startswith("MANUAL"))

    def test_rerunning_the_rollout_leaves_fixed_assets_alone(self):
        remediate(self.fleet, verify(self.fleet, self.scope))
        before = {i: copy.deepcopy(self.fleet.assets[i]) for i in ("web-1", "web-2", "web-4", "api-1", "tool-1")}
        run_rollout(self.fleet, build_plan(self.fleet))
        for asset_id, state in before.items():
            self.assertEqual(self.fleet.assets[asset_id], state, asset_id)


class CanaryFailure(unittest.TestCase):
    def setUp(self):
        self.fleet = load_fleet()
        self.original = copy.deepcopy(self.fleet.assets)
        self.scope = in_scope(self.fleet)
        self.outcome = run_rollout(self.fleet, build_plan(self.fleet), regressions={"web-2"})

    def test_rollout_halts_at_the_canary_and_touches_nothing_else(self):
        self.assertEqual(self.outcome["halted_at"], "canary")
        self.assertEqual(self.outcome["rings_completed"], [])
        self.assertEqual(self.outcome["untouched"], ["ring1-internet", "ring2-internal", "ring3-mitigated"])
        self.assertEqual(self.fleet.assets, self.original)    # canary rolled back, others never changed

    def test_halting_leaves_exposure_and_the_report_says_so(self):
        report = verify(self.fleet, self.scope)
        self.assertEqual(report["counts"], {"still_vulnerable": 5, "unknown": 1, "mitigated": 1})
        self.assertEqual(report["assets"]["web-1"]["reason"], "not patched yet")

    def test_interim_mitigation_changes_status_but_not_the_need_to_patch(self):
        for asset_id in ("web-1", "web-2", "web-4", "api-1"):
            mitigate(self.fleet, asset_id)
        counts = verify(self.fleet, self.scope)["counts"]
        self.assertEqual(counts, {"mitigated": 5, "still_vulnerable": 1, "unknown": 1})
        self.assertNotIn("fixed", counts)


if __name__ == "__main__":
    unittest.main()
