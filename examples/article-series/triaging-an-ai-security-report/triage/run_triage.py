"""Run every claim against the vulnerable and fixed modules and print a triage table.

    python triage/run_triage.py            # print the table, compare with triage-ledger.json
    python triage/run_triage.py --write    # regenerate triage-ledger.json

Everything runs in a temporary directory against synthetic files.
"""
import importlib
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from triage import sandbox  # noqa: E402
from triage.claims import CLAIMS  # noqa: E402
from triage.reachability import defined_functions, reachable_functions  # noqa: E402
from triage.regression import regression_failures  # noqa: E402

LEDGER_PATH = os.path.join(ROOT, "triage-ledger.json")

# Which function each claim is really about, used for the reachability question.
TARGETS = {"C1": "_safe_path", "C2": "_safe_path", "C3": "_safe_path", "C4": "_safe_path", "C5": "_legacy_read"}

# Hand-written judgement that the harness cannot derive. Kept short and checked by a person.
REPORT_LEVEL = {
    "reported_severity": "Critical, remote code execution",
    "supported_impact": "Read of files in sibling directories whose names start with the shared directory's name. "
                        "No write, no code execution, no read of unrelated directories was demonstrated.",
}


def observe(module_name):
    module = importlib.import_module(module_name)
    with tempfile.TemporaryDirectory() as tmp:
        paths = sandbox.build(tmp)
        results = {cid: fn(module, paths) for cid, _, fn in CLAIMS}
        failures = regression_failures(module, paths)
    return module, results, failures


def decide(reproduced, reachable, observation):
    if reproduced and reachable and observation.get("claimed_mechanism_needed") is False:
        return "duplicate of C1: it reproduces, but the null byte is not the mechanism"
    if reproduced and reachable:
        return "confirmed vulnerability"
    if reproduced and not reachable:
        return "defect reproduced; no path from declared entry points; security classification needs wider review"
    if observation["exception"] == "PermissionError":
        return "not reproduced: the existing check blocks it"
    if observation["exception"]:
        return "not a vulnerability: no disclosure, an unhandled error at worst"
    return "not reproduced"


def build_ledger():
    vuln_mod, vuln, _ = observe("minishare.vulnerable")
    fixed_mod, fixed, _ = observe("minishare.fixed")
    reach = reachable_functions(vuln_mod)
    defined = defined_functions(vuln_mod)
    entries = []
    for cid, title, _ in CLAIMS:
        target = TARGETS[cid]
        reachable = target in reach
        entries.append({
            "id": cid,
            "claim": title,
            "target_function": target,
            "target_exists_in_vulnerable": target in defined,
            "reachable_from_declared_entry_points": reachable,
            "vulnerable_observation": vuln[cid],
            "fixed_observation": fixed[cid],
            "decision": decide(vuln[cid]["disclosed"], reachable, vuln[cid]),
        })
    return {"synthetic": True, "report_level": REPORT_LEVEL, "claims": entries}


def main():
    ledger = build_ledger()
    rendered = json.dumps(ledger, indent=2, sort_keys=True) + "\n"
    print(f"{'id':<4} {'reproduced':<11} {'reachable':<10} decision")
    for entry in ledger["claims"]:
        print(f"{entry['id']:<4} {str(entry['vulnerable_observation']['disclosed']):<11} "
              f"{str(entry['reachable_from_declared_entry_points']):<10} {entry['decision']}")
    if "--write" in sys.argv:
        with open(LEDGER_PATH, "w", newline="\n") as handle:
            handle.write(rendered)
        print(f"wrote {os.path.basename(LEDGER_PATH)}")
        return 0
    with open(LEDGER_PATH, newline="") as handle:
        committed = handle.read().replace("\r\n", "\n")  # tolerate CRLF checkouts
    if committed != rendered:
        print("triage-ledger.json is out of date: rerun with --write and review the diff")
        return 1
    print("triage-ledger.json matches the harness output")
    return 0


if __name__ == "__main__":
    sys.exit(main())
