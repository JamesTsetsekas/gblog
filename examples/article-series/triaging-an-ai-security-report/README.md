# Triaging an AI security report: synthetic exercise

Companion code for the article "An AI Security Report Lands in Your Inbox. Now What?".

Everything here is synthetic and local. `minishare` is a tiny library invented for this exercise, `report/synthetic-report.md` is a made-up report written in the style of a long, confident submission, and the "secrets" are marker strings written into a temporary directory. Nothing touches the network, a real project, or anything outside the temporary directory the harness creates and deletes.

## Run it

Standard library only. Run and tested with Python 3.13 on Windows (`Path.is_relative_to` needs 3.9 or newer); other versions are untested. From the repository root:

```bash
python -m unittest discover -s examples/article-series/triaging-an-ai-security-report/tests -v
python examples/article-series/triaging-an-ai-security-report/triage/run_triage.py
```

Expected: `Ran 14 tests ... OK` (the symlink case explicitly skips if the operating system denies symlink creation), and this table, followed by `triage-ledger.json matches the harness output`:

```
id   reproduced  reachable  decision
C1   True        True       confirmed vulnerability
C2   False       True       not reproduced: the existing check blocks it
C3   False       True       not reproduced: the existing check blocks it
C4   True        True       duplicate of C1: it reproduces, but the null byte is not the mechanism
C5   True        False      defect reproduced; no path from declared entry points; security classification needs wider review
```

## The exercise

The synthetic report makes five claims and a headline severity. Read it, then use the harness (or write your own reproducers first) to decide what is true.

| Step | Question | Where it lives |
| --- | --- | --- |
| Reproduce | Does each claim actually do what the report says, in a clean sandbox? | `triage/claims.py`, `triage/sandbox.py` |
| Reach | Can a public entry point get to the flawed code? | `triage/reachability.py` |
| Scope the impact | What is demonstrated, as opposed to claimed? | `report_level` in `triage-ledger.json` |
| Patch | Replace the string prefix check with a resolved-path containment check. | `minishare/fixed.py` |
| Regress | Keep the reproducer, its variants and the legitimate behaviour as permanent tests. | `triage/regression.py`, `tests/test_triage.py` |

Things the tests pin down:

- The confirmed bug (C1) is narrower than the report says: sibling directories whose names share the base directory's prefix, not arbitrary files, and nothing about code execution.
- C2 and C3 are not reproduced because the existing check blocks them.
- C4 does reproduce, but only because it is C1 in disguise. Removing the null byte gives the same disclosure, and a real null byte just raises `ValueError`.
- C5 describes a real flaw with no path from the declared demo entry points. The helper remains directly importable, so its security classification needs repository-wide caller and deployment review; the heuristic alone cannot rule a vulnerability out.
- The regression checks fail against the vulnerable module and pass against the fixed one, which shows they can catch the bug. They also require legitimate reads (nested paths, a file named `..hidden`) to keep working, so an over-eager fix would fail too.

## Limits

- The reachability check is a single-file `ast` heuristic. It cannot see dynamic dispatch, other modules, frameworks, configuration or deployment. For real software, "reachable" is a human judgement backed by evidence about how the code is exposed.
- The decision labels are this exercise's vocabulary. They are not CVSS scores, and the harness does not assign a severity.
- The resolved-path patch assumes a trusted, immutable directory tree. It blocks the demonstrated prefix bypass and a stable symlink escape, but it does not prevent a check/open race if an attacker can mutate the tree. A production file server needs a platform-appropriate atomic opening strategy. The symlink test skips explicitly where the operating system does not permit creating one.
- A passing regression suite shows that the cases you thought of are handled. It does not prove the patch is complete.
- Behaviour was run on Windows with Python 3.13. Path handling differs by platform, so check the results on yours; if a check differs, that is a finding about your platform, not necessarily a bug in the exercise.
