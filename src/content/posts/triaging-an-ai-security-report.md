---
title: "An AI Security Report Lands in Your Inbox. Now What?"
description: "A long, confident vulnerability report is a hypothesis until someone reproduces it. A triage workflow for AI-assisted reports, exercised on a synthetic example you can run, with recent maintainer evidence from curl."
pubDate: "2026-11-19 00:00:00"
category: ["ai", "security", "technology"]
banner: "@images/banners/ai-security-review.png"
tags: ["AI Security", "Vulnerability Triage", "Open Source", "Regression Testing", "Disclosure"]
selected: false
---

The report arrives with a title like "Critical remote code execution via path traversal." It runs for several pages, names five separate flaws, quotes function names correctly, and recommends a CVSS score. It does not include a runnable reproducer.

You cannot tell from the prose whether a person, a model, or both wrote it, and you should not spend effort trying. The prose tells you very little about whether the code does what it says. What matters is that each sentence in the report that begins "an attacker can" is a testable claim, and the job is to turn each one into evidence or discard it.

## What maintainers are describing

The picture from the people receiving these reports has changed quickly, so a little context helps before the workflow.

Seth Larson, who triages security reports for several Python projects, wrote in December 2024 about [a wave of low-quality, spammy and model-hallucinated reports](https://sethmlarson.dev/slop-security-reports) that looked legitimate at first glance and therefore cost real time to refute. One of his triage questions is still useful: is the vulnerability in the project, or in the proof-of-concept code that misuses it?

curl provides a detailed public record. Daniel Stenberg wrote when [ending curl's bug bounty](https://daniel.haxx.se/blog/2026/01/26/the-end-of-the-curl-bug-bounty/) that the share of submissions confirmed as vulnerabilities had been above roughly 15 percent in earlier years and fell below 5 percent from the start of 2025. The program stopped at the end of January 2026.

Then the pattern shifted. In April he reported that the project [had returned to HackerOne in March](https://daniel.haxx.se/blog/2026/04/22/high-quality-chaos/), that nearly every security report now involved AI to some degree, that report volume was about double 2025's, and that the confirmed rate was back in the 15 to 16 percent range. By October he wrote that [the "slop" had practically gone since spring](https://daniel.haxx.se/blog/2026/10/22/ignore-the-slop/) and that the harder problem was high volume with high quality: reports were accurate more often, usually came with working reproducers, but were very long, and the tools were still unreliable at telling a bug from a vulnerability and at judging severity.

Two caveats belong here. This is one project's maintainer describing his own queue, plus an informal poll of other maintainers that he labels unscientific, so treat it as testimony and not a measurement of the ecosystem. And a high confirmed rate does not mean each report is right. When curl had a [scan run with Anthropic's Mythos model](https://daniel.haxx.se/blog/2026/05/11/mythos-finds-a-curl-vulnerability/), the report listed five "confirmed" vulnerabilities. After several hours of work, the security team kept one, a low severity issue. Three were false positives that pointed at behaviour already documented in the API, and one was a bug.

Five claims, one real finding. That shape is common enough to practise on.

## A synthetic exercise

The accompanying exercise can be run locally. Everything in it is invented: a tiny file-sharing library called `minishare`, a made-up report in the style above, and marker strings standing in for secrets inside a temporary directory. It is not a replica of any real project or report, and its 1-in-5 outcome is a deliberately chosen fixture, not an observed rate.

The library's containment check compares strings instead of paths: it normalizes the requested path and tests `startswith(base)`. The synthetic report makes five claims and headlines the severity as remote code execution. Here is how each claim behaves in the runnable harness.

| Claim | Reproduced | Reachable | Decision |
| --- | --- | --- | --- |
| C1: the prefix check lets a sibling directory with a matching name prefix be read | yes | yes | confirmed vulnerability |
| C2: arbitrary file read anywhere through `../` | no | yes | the existing check blocks it |
| C3: an absolute path discards the base directory | no | yes | the existing check blocks it |
| C4: a null byte truncates the path | yes | yes | duplicate of C1, the null byte is not the mechanism |
| C5: `_legacy_read` has no check | yes | not shown | defect confirmed; wider exposure review needed |

Each row exercises a different step.

## Reproduce first, in a clean sandbox

A reproducer that runs against a clean copy, in a throwaway directory, with only synthetic data, is the cheapest filter you have. Two of the five claims died here. Reading outside the base directory with `../outside/secret.txt` raises `PermissionError`, because the string check does catch that. The absolute path case fails the same way. A report that asserts "any file on disk" has made a broader claim than its one working example supports.

If the report has no reproducer, asking for one is reasonable. Stenberg also notes that a good report starts with a short paragraph from a human who understands the problem, and that [models now make reproducers cheap to produce](https://daniel.haxx.se/blog/2026/10/22/ignore-the-slop/), which removes one excuse for leaving them out.

## Ask whether anything can reach it

C5 is true in isolation. `_legacy_read` has no containment check and will happily read a file it should not. No path from the declared demo entry points calls it in the one-file graph. The harness uses a small `ast` walk from the names in `__all__` to check those paths. Python still allows a consumer to import the helper directly: neither `__all__` nor an underscore is an access-control boundary. That is a one-file heuristic: it cannot see dynamic dispatch, other modules, frameworks or configuration, and for real software the answer to "is this exposed" has to come from how it is deployed and called.

The finding is still useful, but its security classification remains open. A wider review must check consumers, supported extension interfaces, framework routes, reflection and deployment configuration. Removing an unused helper may be sensible once that review establishes it is unused; this heuristic alone cannot decide whether an advisory is warranted. Stenberg [makes a related observation](https://daniel.haxx.se/blog/2026/10/20/do-minor-curl-vulnerabilities-in-the-open/) about reports built from unusual option combinations that real applications are unlikely to use, and he says he intends to push back harder on those.

## Scope the impact to what you demonstrated

The headline said remote code execution. The demonstrated impact in C1 is a read of directories whose names start with the shared directory's name. No write and no execution was shown, and unrelated directories stayed blocked. I would write that sentence into the ledger exactly as narrowly as the evidence allows, and let anyone who wants to widen it provide a reproducer.

For deciding how urgent the narrowed finding is, CISA's [SSVC guide](https://www.cisa.gov/sites/default/files/publications/cisa-ssvc-guide%20508c.pdf) offers a vocabulary I find more useful than a bare score: the state of exploitation, whether exploitation can be reliably automated, and the technical impact, which together with mission and public well-being context lead to Track, Track\*, Attend or Act. The exercise does not implement it. Its ledger records decisions in plain words instead of pretending to compute a severity.

## Look for a shared root cause

C4 reproduces. The payload contains a null byte, the file is disclosed, and the report credits the null byte. Remove the null byte and the same disclosure happens. After normalization no null byte survives, so the mechanism is C1 again. A genuine null byte in a path just raises `ValueError`. The exercise has a test for each of those facts. Without the control, you would be tempted to track two vulnerabilities, write two fixes and answer two reporters.

## Patch, then keep the evidence

The toy regression fix replaces the string check with a resolved-path comparison and removes the helper from the example. It assumes a trusted, immutable directory tree. A pre-open path check does not prevent another process swapping directories or symlinks between the check and the open. On a mutable adversarial filesystem, a production design needs an appropriate atomic, descriptor-relative opening strategy and a platform-specific threat model. [Python path resolution](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve), [Linux openat2 resolution controls](https://man7.org/linux/man-pages/man2/openat2.2.html). The part that outlives the triage is the regression suite, which has three jobs:

- Keep the original reproducer and its variants. The suite tries four forms of the sibling escape and a base directory with a trailing slash, because a patch that blocks only the exact string from the report is not a patch.
- Require legitimate behaviour to keep working: nested paths, `docs/../readme.txt`, and a file whose name begins with two dots. A fix that blocks too much is also a regression.
- Prove the suite can fail. The same checks fail against the vulnerable module and pass against the fixed one.

Getting the first fix right matters more than it used to. Stenberg observes that [when a set of fixes is announced, researchers using AI quickly run them against their tools](https://daniel.haxx.se/blog/2026/10/20/do-minor-curl-vulnerabilities-in-the-open/) to look for similar mistakes or omissions. A fix that misses a sibling variant leaves it available to renewed scrutiny.

## Run it

Python's standard library is all it needs. From the repository root:

```bash
python -m unittest discover -s examples/article-series/triaging-an-ai-security-report/tests -v
python examples/article-series/triaging-an-ai-security-report/triage/run_triage.py
```

In the recorded local run (Windows, Python 3.13) the expanded suite checks the table above, preserves the unresolved C5 classification, and exercises a stable symlink escape where the operating system permits symlink creation. The example's README lists what the harness does not do. The reachability check is a heuristic, the decision labels are not CVSS, and a passing regression suite covers the cases someone thought of, not every case.

## What I would take from it

A report from a model deserves the same treatment as a report from a person: reproduce, check reach, bound the impact, find the shared cause, fix with variants, and keep the tests. The difference is mostly volume and polish. Fluent text raises the cost of reading a report and says nothing about whether the claim is true, so the reproducer has to carry the weight that the prose used to be trusted with.

## Further reading

- Seth Larson, [New era of slop security reports for open source](https://sethmlarson.dev/slop-security-reports) (December 2024).
- Daniel Stenberg, [The end of the curl bug-bounty](https://daniel.haxx.se/blog/2026/01/26/the-end-of-the-curl-bug-bounty/), [High quality chaos](https://daniel.haxx.se/blog/2026/04/22/high-quality-chaos/), [Mythos finds a curl vulnerability](https://daniel.haxx.se/blog/2026/05/11/mythos-finds-a-curl-vulnerability/), and ["ignore the slop"](https://daniel.haxx.se/blog/2026/10/22/ignore-the-slop/).
- CISA, [Stakeholder-Specific Vulnerability Categorization guide](https://www.cisa.gov/sites/default/files/publications/cisa-ssvc-guide%20508c.pdf).
