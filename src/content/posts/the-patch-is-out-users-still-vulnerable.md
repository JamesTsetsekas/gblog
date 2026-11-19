---
title: "The Patch Is Out. Your Users Are Still Vulnerable."
description: "A released fix does not end anyone's exposure. How to find what you actually run, roll a patch out in rings with a way back, and verify by observation, with a synthetic fleet model you can run."
pubDate: "2026-11-19 00:00:00"
category: ["software-engineering", "security"]
banner: "@images/banners/article-series/the-patch-is-out-users-still-vulnerable.webp"
bannerAlt: "A miniature server fleet with one replacement component installed and another ready for deployment."
ogImage: "@images/banners/article-series/the-patch-is-out-users-still-vulnerable-social.png"
tags: ["Patch Management", "Vulnerability Management", "Deployment", "Rollback", "Operations"]
selected: false
---

A fix merges, a release goes out, an advisory is published, and a ticket somewhere moves to "patched." A release begins another phase of work for the people running the software. Exposure continues through the interval between "a fix exists" and "the fix is running everywhere it needs to be."

This article is about that interval from the operator's side: what you run, in which order you change it, how you recover if the change goes wrong, and how you know it worked. It is separate from the question of how fast vulnerabilities are being found, or how maintainers sort through reports. Assume a good fix exists and ask what happens next.

## Why the gap matters more now

Defenders have been told for years that the window between disclosure and exploitation is shrinking. Mandiant's analysis of vulnerabilities exploited in 2023 [put the average time to exploit at five days](https://cloud.google.com/blog/topics/threat-intelligence/time-to-exploit-trends-2023), down from 63 days for 2018 and 2019. That figure comes from one vendor's incident data, covers a limited set of vulnerabilities, and excludes 15 outliers that would otherwise lift the average to 47 days, so I read it as a direction and not a precise constant.

Maintainers who are seeing more reports expect the downstream effect to land on operators. In April 2026 curl's maintainer wrote that the surge in AI-assisted reports would produce more CVEs and that [everyone then has to update to the fixed releases, which is likely to take even longer](https://daniel.haxx.se/blog/2026/04/22/high-quality-chaos/). That is a forecast from one project, not a measurement, but it points at the right bottleneck: someone has to deploy every fix.

## Start with what you actually run

The most documented example of an inventory failure is old and instructive. In the U.S. House Oversight Committee's report on the 2017 Equifax breach, a critical Apache Struts flaw was disclosed on March 7 and [an internal email went to roughly 430 people on March 9, asking for a patch within 48 hours](https://oversight.house.gov/wp-content/uploads/2018/12/Equifax-Report.pdf). A scan to find vulnerable components did not find the affected system. The committee records the interim chief security officer's explanation that the scan was run on a root directory and not on the subdirectory where Struts was listed. The vulnerable internet-facing portal was not patched, and the attack that followed lasted 76 days.

That is one case from 2017, and it had other failures around it, including an expired certificate on a traffic-monitoring device. The lesson that generalizes is narrow. A scanner reports what it was pointed at, and "no findings" is a statement about the scan.

Modern variants are easy to list:

- **Distribution backports.** Enterprise distributions often fix a flaw in an older version without changing the upstream version number. Red Hat's documentation notes that [scanning tools that judge only by version number produce false positives for backported fixes](https://access.redhat.com/solutions/57665), and that Red Hat publishes machine-readable OVAL definitions tools can use to get the real status.
- **Vendored copies.** A library compiled into an application or copied into a repository is invisible to the package manager.
- **Pinned images.** A container image referenced by digest keeps running the old code until the digest changes.
- **Processes that never restarted.** The package on disk is new and the process in memory is old.
- **Assets nobody can ask.** If you cannot query a system for its running version, its status is unknown, not fine.

The practical answer is to treat the version string as a claim and prefer evidence from the running thing: a version endpoint, a build identifier, a behavioural check. Then record how you know. "Observed from the process" and "declared in a manifest" are different confidence levels, and an inventory that does not distinguish them will quietly overstate your position.

## Order the work by exposure

When many assets are affected, everything cannot go first. Whether the vulnerable feature is enabled and whether the asset faces the internet are usually better ordering inputs than a severity score alone. CISA's [BOD 26-04, Prioritizing Security Updates Based on Risk](https://www.cisa.gov/news-events/directives/bod-26-04-prioritizing-security-updates-based-risk), issued in June 2026, provides a current public example: its required response depends on exploitation evidence, automation, technical impact, and exposure. It supersedes and revokes BOD 22-01; that older directive's default deadlines are historical. [FedRAMP's June notice](https://demo.fedramp.gov/notices/0014/) confirms the factors and the December 7, 2026 deadline for agencies to begin evaluating and remediating under the new timelines. An application team must define priorities appropriate to its own environment. The [SSVC guide](https://www.cisa.gov/sites/default/files/publications/cisa-ssvc-guide%20508c.pdf) takes a similar decision-tree approach.

NIST's patch management guide is candid about the trade-off underneath. In [SP 800-40 Rev. 4](https://doi.org/10.6028/NIST.SP.800-40r4), deploying faster shortens the attacker's window but raises the risk of operational disruption, while testing longer does the opposite and still may miss problems. It also describes separate scenarios for routine patching, emergency patching, emergency mitigation before a patch exists, and unpatchable assets. A mitigation, such as disabling the affected feature, belongs in the plan as a named interim state, not as a quiet substitute for the fix.

## Roll out in rings, with a way back

A patch is a change, and changes break things. The most visible reminder is CrowdStrike's own [root cause analysis of its July 2024 incident](https://www.crowdstrike.com/en-us/blog/channel-file-291-rca-available/). Among its remediations, the company says new content instances will pass canary testing and then be promoted through successively wider deployment rings with bake-in time and telemetry, or rolled back if problems appear, and that customers get more control over where and when updates land. That is a vendor's account of its own failure, but the structure it describes is the same one operators should apply to security fixes.

A workable shape:

1. **Canary.** One low-risk but representative asset first, with a health check that tests something real.
2. **Rings.** Widen in steps, ordered by exposure, with a defined bake time between them.
3. **Halt rule.** If a ring fails its health check, stop, restore that ring, and leave later rings untouched.
4. **Rollback you have exercised.** Kubernetes Deployments, for instance, keep revision history and support [`kubectl rollout undo`](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment), but a rollback path is only a plan until someone has run it.
5. **An interim control for what the halt leaves exposed.** A held-back rollout is not a safe state, so decide in advance what you will do about the internet-facing assets that are still vulnerable.

## Verify by observation

NIST lists verification and monitoring as their own steps after deployment: confirming a patch was installed and took effect, and later confirming it is still installed. The operational point is that a deployment job reporting success is evidence about the job. It says the playbook ran, the manifest applied or the package installed. It does not say the vulnerable code is gone from the process answering requests. The check that closes the loop asks the running system, ideally with something harder to fool than a version string, such as a harmless request that behaves differently once the fix is in. Where you cannot write that check, say so in the ticket, because "verified by version" and "verified by behaviour" are different claims.

## A synthetic fleet you can run

The accompanying Python model makes those gaps concrete. It has nine invented assets, one invented advisory for a fictional library, and rings with a canary, a health check, and rollback. It is deliberately built to contain the failure modes above. It does not sample real fleets, so none of its counts say how often these things happen.

```bash
python -m unittest discover -s examples/article-series/the-patch-is-out-users-still-vulnerable/tests -v
python examples/article-series/the-patch-is-out-users-still-vulnerable/run_demo.py
python examples/article-series/the-patch-is-out-users-still-vulnerable/run_demo.py canary-failure
```

In the recorded local run on Windows with Python 3.13, the expanded 15-test suite passes. In the happy-path scenario seven deployment jobs report success, and observation shows three assets fixed, three still vulnerable and one unknown. The three: one package was updated but its process was never restarted, one container image digest was pinned and not bumped, and one vendored copy was untouched by the package-manager job. After an automated remediation pass that restarts the service and bumps the digest, five are fixed and two remain. Those two print `MANUAL`: the vendored copy needs its owner to rebuild, and the asset with an unreachable version probe needs a working probe before its status means anything.

The inventory step keeps evidence quality explicit. A fixed version declared by a package manager cannot close an asset whose runtime is unobservable. A backport claim needs current matching source evidence and an observed runtime; the fixture models those trust checks as input fields, not signature verification. Missing or stale evidence leaves an asset unknown and in scope.

The inventory step has its own result. A scan that trusts the package version gets two assets wrong: it flags a distribution-backported asset that is already fixed, and it misses the vendored copy entirely.

In the canary-failure scenario the canary's health check fails, the rollout halts, the canary is restored and nothing else is touched. Verification then reports five assets still vulnerable, one unknown and one mitigated until the vulnerable feature is turned off on the held-back internet-facing assets, which moves them to "mitigated" but not "fixed."

The limits are serious. The "running version" is a field in a JSON file, health checks are one boolean, there is no time or concurrency, and real rollouts have dependencies, maintenance windows and approvals the model ignores. It is a way to rehearse the questions, not a tool to run against production.

## Questions to answer before closing the ticket

- How do you know which assets run the affected code, and which of those answers are observed?
- Which of them are exposed with the vulnerable feature enabled?
- What is the order, the canary and the halt rule, and has the rollback been tried?
- What is the interim control if the rollout stops?
- What would you query to prove the fix is running, and who owns the assets that cannot be queried?

If you cannot answer the last one, the honest status of the ticket is "deployment attempted."

## Further reading

- NIST, [SP 800-40 Rev. 4, Guide to Enterprise Patch Management Planning](https://doi.org/10.6028/NIST.SP.800-40r4) (2022).
- CISA, [BOD 26-04](https://www.cisa.gov/news-events/directives/bod-26-04-prioritizing-security-updates-based-risk) and its [SSVC guide](https://www.cisa.gov/sites/default/files/publications/cisa-ssvc-guide%20508c.pdf).
- CrowdStrike, [Channel File 291 root cause analysis](https://www.crowdstrike.com/en-us/blog/channel-file-291-rca-available/).
- U.S. House Committee on Oversight and Government Reform, [The Equifax Data Breach](https://oversight.house.gov/wp-content/uploads/2018/12/Equifax-Report.pdf) (December 2018).
- Mandiant, [Time-to-Exploit Trends: 2023](https://cloud.google.com/blog/topics/threat-intelligence/time-to-exploit-trends-2023).
