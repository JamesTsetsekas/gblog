"""Ring based rollout, rollback, verification and gap remediation on the synthetic fleet."""
from .model import ADVISORY, classify, parse, version_affected

FIXED = ADVISORY["fixed_in"]


# ---- individual actions (each returns what the *job* would report) --------------------
def apply_patch(fleet, asset_id: str) -> str:
    """Run the deployment job. Note that "ok" means the job ran, not that exposure ended."""
    asset = fleet.assets[asset_id]
    asset["patch_attempted"] = True
    kind = asset["kind"]
    if kind == "package":
        asset["package_version"] = FIXED                  # installed, but the old process keeps running
    elif kind == "container":
        if asset.get("image_pinned_digest"):
            fleet.log.append(f"{asset_id}: manifest updated but the pinned digest still points at the old image")
        else:
            asset["package_version"] = FIXED
            asset["running_version"] = FIXED
    elif kind == "vendored":
        fleet.log.append(f"{asset_id}: nothing the package manager manages was changed")
    return "ok"


def restart(fleet, asset_id: str) -> str:
    asset = fleet.assets[asset_id]
    if asset.get("restart_deferred"):
        return "skipped"
    if asset["kind"] == "package" and asset.get("package_version"):
        asset["running_version"] = asset["package_version"]
    return "restarted"


def health_check(fleet, asset_id: str, regressions: set) -> bool:
    asset = fleet.assets[asset_id]
    running = asset.get("running_version")
    return not (asset_id in regressions and running and not version_affected(running))


# ---- planning ------------------------------------------------------------------------
def build_plan(fleet) -> list:
    """Canary first, then remaining internet facing, then internal, then mitigated assets."""
    rings = {"canary": [], "ring1-internet": [], "ring2-internal": [], "ring3-mitigated": []}
    for asset_id, asset in sorted(fleet.assets.items()):
        result = classify(asset)
        if result["status"] == "not_affected":
            continue
        if asset.get("canary") and result["status"] == "affected":
            rings["canary"].append(asset_id)
        elif result["priority"] == "P1":
            rings["ring1-internet"].append(asset_id)
        elif result["priority"] == "P2":
            rings["ring2-internal"].append(asset_id)
        else:
            rings["ring3-mitigated"].append(asset_id)
    return [(name, ids) for name, ids in rings.items() if ids]


def run_rollout(fleet, plan: list, regressions: set = frozenset()) -> dict:
    """Patch ring by ring. Halt and roll the failing ring back if any health check fails."""
    outcome = {"rings_completed": [], "halted_at": None, "rolled_back": [], "untouched": [],
               "jobs_reported_ok": 0}
    for index, (name, ids) in enumerate(plan):
        snapshots = {i: fleet.snapshot(i) for i in ids}
        failed = []
        for asset_id in ids:
            if apply_patch(fleet, asset_id) == "ok":
                outcome["jobs_reported_ok"] += 1
            restart(fleet, asset_id)
            if not health_check(fleet, asset_id, set(regressions)):
                failed.append(asset_id)
        if failed:
            for asset_id in ids:
                fleet.restore(asset_id, snapshots[asset_id])
            outcome["halted_at"] = name
            outcome["rolled_back"] = list(ids)
            outcome["untouched"] = [n for n, _ in plan[index + 1:]]
            fleet.log.append(f"halted at {name}: health check failed on {failed}; rolled back {ids}")
            return outcome
        outcome["rings_completed"].append(name)
    return outcome


# ---- mitigation ----------------------------------------------------------------------
def mitigate(fleet, asset_id: str) -> None:
    """Interim control while a patch is held back: turn the vulnerable feature off."""
    fleet.assets[asset_id]["feature_enabled"] = False


# ---- verification --------------------------------------------------------------------
def in_scope(fleet) -> list:
    """Assets that are exposed before any patching (run this before the rollout)."""
    return [i for i, a in sorted(fleet.assets.items()) if classify(a)["status"] != "not_affected"]


def verify(fleet, scope: list = None) -> dict:
    """Judge each in-scope asset by what is observed, not by what a job reported."""
    rows, counts = {}, {}
    scope = scope if scope is not None else in_scope(fleet)
    for asset_id in scope:
        asset = fleet.assets[asset_id]
        cls = classify(asset)
        if cls["status"] == "mitigated" and not asset.get("patch_attempted"):
            status, reason = "mitigated", "vulnerable feature disabled; patch still needed"
        elif cls["status"] == "unknown":
            status, reason = "unknown", f"runtime or backport evidence unverified: {cls['basis']}"
        elif cls["status"] == "not_affected":
            status, reason = "fixed", cls["basis"]
        else:
            running = asset["running_version"]
            if not version_affected(running):
                status, reason = "fixed", "running process reports a fixed version"
            elif not asset.get("patch_attempted"):
                status, reason = "still_vulnerable", "not patched yet"
            elif asset["kind"] == "vendored":
                status, reason = "still_vulnerable", "vendored copy was not updated"
            elif asset["kind"] == "container" and asset.get("image_pinned_digest"):
                status, reason = "still_vulnerable", "pinned image digest was not bumped"
            elif asset.get("package_version") and not version_affected(asset["package_version"]):
                status, reason = "still_vulnerable", "package updated but the old process is still running"
            else:
                status, reason = "still_vulnerable", "not patched yet"
        rows[asset_id] = {"status": status, "reason": reason, "priority": cls["priority"]}
        counts[status] = counts.get(status, 0) + 1
    return {"assets": rows, "counts": counts}


# ---- closing the gaps ----------------------------------------------------------------
def remediate(fleet, report: dict) -> list:
    """Act on the reasons verification found. Some gaps need a person, and say so."""
    actions = []
    for asset_id, row in report["assets"].items():
        asset = fleet.assets[asset_id]
        if row["status"] != "still_vulnerable" and row["status"] != "unknown":
            continue
        if row["reason"].startswith("package updated"):
            asset["restart_deferred"] = False
            restart(fleet, asset_id)
            actions.append((asset_id, "restarted the service in the agreed window"))
        elif row["reason"].startswith("pinned image"):
            asset["image_pinned_digest"] = False
            apply_patch(fleet, asset_id)
            actions.append((asset_id, "bumped the pinned digest and redeployed"))
        elif row["reason"].startswith("vendored"):
            actions.append((asset_id, "MANUAL: owner must rebuild with the fixed library"))
        elif row["status"] == "unknown":
            actions.append((asset_id, "MANUAL: restore the version probe before trusting any status"))
        elif row["reason"] == "not patched yet":
            apply_patch(fleet, asset_id)
            restart(fleet, asset_id)
            actions.append((asset_id, "patched in a follow-up pass"))
    return actions
