"""One reproducer per claim in report/synthetic-report.md.

Each reproducer takes (module, paths) and returns an observation dict:
  disclosed: bool       the synthetic secret came back to the caller
  exception: str|None   exception type name if the call raised
They never touch anything outside the temporary directory they are given.
"""
from . import sandbox


def _try_read(module, base, user_path, secret):
    try:
        data = module.download(base, user_path)
    except Exception as exc:  # noqa: BLE001 - we want to record whatever happened
        return {"disclosed": False, "exception": type(exc).__name__}
    return {"disclosed": data == secret, "exception": None}


def c1_sibling_prefix(module, paths):
    return _try_read(module, paths["base"], "../public-private/secret.txt", sandbox.SIBLING_SECRET)


def c2_arbitrary_file_read(module, paths):
    return _try_read(module, paths["base"], "../outside/secret.txt", sandbox.OUTSIDE_SECRET)


def c3_absolute_path(module, paths):
    return _try_read(module, paths["base"], paths["outside_secret"], sandbox.OUTSIDE_SECRET)


def c4_null_byte(module, paths):
    nul = chr(0)  # the report's payload contains a NUL; built here so the source file stays plain text
    payload = "readme.txt" + nul + "/../../public-private/secret.txt"
    observation = _try_read(module, paths["base"], payload, sandbox.SIBLING_SECRET)
    # Control: is the null byte actually needed? Remove it and try again.
    control = _try_read(module, paths["base"], payload.replace(nul, ""), sandbox.SIBLING_SECRET)
    observation["claimed_mechanism_needed"] = not control["disclosed"]
    return observation


def c5_legacy_read(module, paths):
    helper = getattr(module, "_legacy_read", None)
    if helper is None:
        return {"disclosed": False, "exception": "AttributeError"}
    try:
        data = helper(paths["base"], "../outside/secret.txt")
    except Exception as exc:  # noqa: BLE001
        return {"disclosed": False, "exception": type(exc).__name__}
    return {"disclosed": data == sandbox.OUTSIDE_SECRET, "exception": None}


CLAIMS = [
    ("C1", "Directory containment uses startswith, so a sibling directory sharing the name prefix is readable",
     c1_sibling_prefix),
    ("C2", "Arbitrary file read anywhere on disk through ../ sequences", c2_arbitrary_file_read),
    ("C3", "An absolute path discards the base directory", c3_absolute_path),
    ("C4", "An embedded null byte truncates the path and bypasses the check", c4_null_byte),
    ("C5", "_legacy_read performs no containment check", c5_legacy_read),
]
