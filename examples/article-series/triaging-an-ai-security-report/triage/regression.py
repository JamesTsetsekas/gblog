"""The regression checks that outlive the triage.

`regression_failures(module, paths)` returns a list of human readable failures. It is
used against the fixed module (expect none) and against the vulnerable one (expect
failures, which proves the checks can actually catch the bug).
"""
from . import sandbox

# Variants of the confirmed bug. A fix that only blocks the exact string from the
# report would still pass the original reproducer, so the checks cover siblings of it.
SIBLING_VARIANTS = [
    "../public-private/secret.txt",
    "./../public-private/secret.txt",
    "docs/../../public-private/secret.txt",
    "../public-private/../public-private/secret.txt",
]

# Behaviour the fix must preserve. A fix that blocks too much is also a regression.
LEGITIMATE = [
    ("readme.txt", b"public readme"),
    ("docs/guide.txt", b"public guide"),
    ("docs/../readme.txt", b"public readme"),
    ("..hidden", b"dots are legal in file names"),
]


def regression_failures(module, paths) -> list:
    failures = []
    for variant in SIBLING_VARIANTS:
        try:
            data = module.download(paths["base"], variant)
        except PermissionError:
            continue
        except Exception as exc:  # noqa: BLE001
            failures.append(f"variant {variant!r} raised {type(exc).__name__} instead of PermissionError")
            continue
        if data == sandbox.SIBLING_SECRET:
            failures.append(f"variant {variant!r} disclosed the sibling secret")
    for user_path, expected in LEGITIMATE:
        try:
            data = module.download(paths["base"], user_path)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"legitimate path {user_path!r} raised {type(exc).__name__}")
            continue
        if data != expected:
            failures.append(f"legitimate path {user_path!r} returned unexpected bytes")
    # A trailing separator on the base directory must not change the answer.
    try:
        module.download(paths["base"] + "/", "../public-private/secret.txt")
        failures.append("trailing slash on base re-opened the sibling escape")
    except PermissionError:
        pass
    except Exception as exc:  # noqa: BLE001
        failures.append(f"trailing-slash base raised {type(exc).__name__}")
    return failures
