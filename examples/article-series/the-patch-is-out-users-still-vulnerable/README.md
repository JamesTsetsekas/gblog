# The patch is out, your users are still vulnerable: synthetic rollout model

Companion code for the article "The Patch Is Out. Your Users Are Still Vulnerable."

Everything is synthetic. The advisory (`SYNTH-2026-0001`), the component (`examplelib`) and the nine-asset fleet in `fleet.json` are invented. Nothing connects to a network, a package manager or a real deployment system. The model is deliberately constructed to contain several different ways a patch fails to reach the thing that is running. It is not a sample of real fleets, and the counts it prints say nothing about how often these failures occur.

## Run it

Standard library only. Run and tested with Python 3.13 on Windows; other versions are untested. From the repository root:

```bash
python -m unittest discover -s examples/article-series/the-patch-is-out-users-still-vulnerable/tests -v
python examples/article-series/the-patch-is-out-users-still-vulnerable/run_demo.py
python examples/article-series/the-patch-is-out-users-still-vulnerable/run_demo.py canary-failure
```

Expected: `Ran 15 tests ... OK`.

Happy-path run, verification right after the rollout: 7 deployment jobs report success, and observation shows `{'fixed': 3, 'still_vulnerable': 3, 'unknown': 1}`. After the automated remediation pass: `{'fixed': 5, 'still_vulnerable': 1, 'unknown': 1}`. The remaining two need a person.

Canary-failure run: the canary's health check fails, the rollout halts and rolls the canary back, and nothing else was touched. Verification then shows `{'still_vulnerable': 5, 'unknown': 1, 'mitigated': 1}` until the vulnerable feature is turned off on the held-back internet-facing assets, which moves them to `mitigated` but still not `fixed`.

## What it shows

| Idea | Where |
| --- | --- |
| A package-version scan misses a vendored copy and flags a distribution backport as vulnerable, so exposure needs more evidence than a version string | `patchgap/model.py`, `Inventory` tests |
| Exposure also depends on whether the vulnerable feature is on and whether the asset faces the internet, which sets the order | `classify`, `build_plan` |
| Rings with a canary, a health check and a rollback that restores prior state, halting before later rings | `run_rollout`, `CanaryFailure` tests |
| "Job succeeded" and "no longer vulnerable" are different facts. Verification reads what the running process reports | `verify`, `HappyPath` tests |
| Typical gaps: package updated but process not restarted, container digest pinned, vendored copy, unobservable asset | `patchgap/rollout.py` |
| An interim mitigation lowers exposure without being a fix | `mitigate` |

## Limits

- Unobserved runtimes remain unknown even if a manifest declares a fixed version. A backport exemption requires matching current source evidence and an observed runtime. The source/verified/current fields are synthetic inputs representing those trust decisions, not cryptographic validation or a live advisory feed.
- The "running version" is a field in a JSON file. A real probe can be wrong, spoofed or stale, and a version string is weak evidence that the vulnerable code path is gone. Behavioural checks, such as a safe test for the fixed behaviour, are stronger where you can write one.
- Health checks, bake time, traffic shifting, database migrations, dependencies between services and change approval are reduced to one boolean.
- No concurrency, partial failure inside a ring, or time. A real rollout takes hours or days and the world changes while it runs.
- The remediation pass only performs the actions the model understands, and prints `MANUAL` for the rest. Real gaps often need a person and a conversation with a different team.
