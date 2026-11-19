"""Advisory, fleet state, and exposure classification.

The advisory is invented: a fictional component `examplelib`, vulnerable from 2.0.0
up to (not including) 2.4.7, only when the `legacy_upload` feature is enabled.
"""
import copy
import json
import os

ADVISORY = {
    "id": "SYNTH-2026-0001",
    "component": "examplelib",
    "affected_from": "2.0.0",
    "fixed_in": "2.4.7",
    "vulnerable_feature": "legacy_upload",
}


def parse(version: str) -> tuple:
    return tuple(int(part) for part in version.split("."))


def version_affected(version: str) -> bool:
    return parse(ADVISORY["affected_from"]) <= parse(version) < parse(ADVISORY["fixed_in"])


def naive_classification(asset: dict) -> str:
    """What a scanner that trusts only the package manager's version string would say."""
    version = asset.get("package_version")
    return "affected" if version and version_affected(version) else "not affected"


def best_version(asset: dict) -> dict:
    """Keep observed and declared evidence distinct; declarations cannot close exposure."""
    if asset.get("running_version") and not asset.get("probe_unreachable"):
        return {"version": asset["running_version"], "observed": True,
                "basis": "observed from the running process"}
    declared = asset.get("package_version") or asset.get("vendored_version")
    return {"version": declared, "observed": False, "basis": "declared, not observed"}


def classify(asset: dict) -> dict:
    """Exposure classification using evidence beyond the package version string."""
    evidence = best_version(asset)
    version, basis = evidence["version"], evidence["basis"]
    priority = "P1" if asset.get("internet_facing") else "P2"
    if not evidence["observed"]:
        return {"status": "unknown", "priority": priority, "basis": basis}
    if ADVISORY["id"] in asset.get("backported_fixes", []):
        proof = asset.get("backport_evidence", {})
        if (proof.get("verified") is True and proof.get("current") is True
                and proof.get("source") and proof.get("advisory") == ADVISORY["id"]
                and proof.get("package_version") == asset.get("package_version") == version):
            return {"status": "not_affected", "priority": None,
                    "basis": "current verified synthetic distribution advisory matches observed package version"}
        return {"status": "unknown", "priority": priority,
                "basis": "backport claim lacks current matching source evidence"}
    if not version_affected(version):
        return {"status": "not_affected", "priority": None, "basis": basis}
    if not asset.get("feature_enabled", True):
        return {"status": "mitigated", "priority": "P3",
                "basis": f"{basis}; vulnerable feature disabled by configuration"}
    return {"status": "affected", "priority": priority, "basis": basis}


class Fleet:
    def __init__(self, assets: list):
        self.assets = {a["id"]: copy.deepcopy(a) for a in assets}
        self.log: list = []

    def snapshot(self, asset_id: str) -> dict:
        return copy.deepcopy(self.assets[asset_id])

    def restore(self, asset_id: str, snapshot: dict) -> None:
        self.assets[asset_id] = snapshot


def load_fleet(path: str = None) -> Fleet:
    path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fleet.json")
    with open(path, encoding="utf-8") as handle:
        return Fleet(json.load(handle)["assets"])
