"""Walk the synthetic fleet through exposure inventory, rollout, verification and cleanup.

    python run_demo.py                  # happy path: no health regressions
    python run_demo.py canary-failure   # the canary regresses, the rollout halts
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from patchgap import (ADVISORY, build_plan, classify, in_scope, load_fleet, mitigate,  # noqa: E402
                      naive_classification, remediate, run_rollout, verify)


def show_inventory(fleet):
    print(f"Advisory {ADVISORY['id']}: {ADVISORY['component']} >= {ADVISORY['affected_from']}, "
          f"< {ADVISORY['fixed_in']}, only with {ADVISORY['vulnerable_feature']} enabled\n")
    print(f"{'asset':<8} {'package-version scan':<22} {'evidence based':<14} {'prio':<5} basis")
    for asset_id, asset in sorted(fleet.assets.items()):
        cls = classify(asset)
        print(f"{asset_id:<8} {naive_classification(asset):<22} {cls['status']:<14} {str(cls['priority']):<5} {cls['basis']}")
    print()


def show_report(title, report):
    print(f"{title}: {report['counts']}")
    for asset_id, row in report["assets"].items():
        print(f"  {asset_id:<8} {row['status']:<17} {row['reason']}")
    print()


def main(scenario="happy-path"):
    fleet = load_fleet()
    show_inventory(fleet)
    scope = in_scope(fleet)
    plan = build_plan(fleet)
    print("Plan:", " -> ".join(f"{name}{ids}" for name, ids in plan), "\n")
    regressions = {"web-2"} if scenario == "canary-failure" else set()
    outcome = run_rollout(fleet, plan, regressions)
    print("Rollout:", outcome, "\n")
    report = verify(fleet, scope)
    show_report("Verification after rollout", report)
    if outcome["halted_at"]:
        for asset_id, row in report["assets"].items():
            if row["priority"] == "P1" and row["status"] == "still_vulnerable":
                mitigate(fleet, asset_id)
        show_report("After disabling the vulnerable feature on held-back internet-facing assets", verify(fleet, scope))
        return
    actions = remediate(fleet, report)
    for asset_id, action in actions:
        print(f"  action {asset_id}: {action}")
    print()
    show_report("Verification after remediation", verify(fleet, scope))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "happy-path")
