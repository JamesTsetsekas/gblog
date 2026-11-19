---
title: "Passing Tests Is Not a Proof: What AI Verification Means for Developers"
description: "Google DeepMind's AlphaProof Code established scoped properties of a compiled one-to-one libsignal harness. The lesson for everyday developers is less about AI proofs than about writing specifications worth proving."
pubDate: "2026-11-19 00:00:00"
category: ["software-engineering", "security", "ai"]
banner: "@images/banners/article-series/passing-tests-is-not-a-proof.webp"
bannerAlt: "Three fitted ivory pieces inside a measuring frame, beside sample pieces and an inspection lens."
ogImage: "@images/banners/article-series/passing-tests-is-not-a-proof-social.png"
tags: ["Formal Verification", "Testing", "Lean", "Signal", "Specifications", "AI"]
selected: false
---

Imagine a function that splits a payout across recipients by weight. It scales each share and rounds it. Three example tests pass: 100 split evenly is 50 and 50, 90 split one to two is 30 and 60, 10 split one, one, three is 2, 2 and 6. A reviewer reads it, the CI check turns green, and it ships.

Then someone splits 100 sats three ways and the function pays out 99. Someone else splits 1 sat between two people and the function pays out 2.

The tests were not wrong. They were a sample, and the sample happened to avoid every input where independent rounding drifts away from the total. The [small runnable example](https://github.com/JamesTsetsekas/gblog/tree/main/examples/article-series/passing-tests-is-not-a-proof) makes the distinction concrete at toy scale. A far larger piece of recent research gives it a timely setting.

## What DeepMind actually verified

On November 10, 2026, Google DeepMind released [AlphaProof Code](https://deepmind.google/documents/36/Formal_Verification_of_Signal_4.pdf), reporting AI-generated Lean proofs about an AArch64 executable built around a one-to-one libsignal harness. The PQXDH and Triple Ratchet results separate symbolic guarantees on collision-free executions, including handshake secrecy under a modeled later DH break, from a classical computational bound on adversary advantage. That bound can become uninformative over many ratchet epochs.

The paper's limits are essential: low-level cryptographic routines enter through trusted contracts; key generation and side channels are outside scope. Its computational bounds do not establish security against quantum adversaries, and its ratchet theorems do not prove SPQR's intended post-quantum healing. The target is a particular harness build under stated machine and operating-system models, not Signal's mobile applications.

Those are the researchers' reported results. The [public repository](https://github.com/google-deepmind/code-verification) provides artifacts and build instructions; the full proofs were not rebuilt for this article. Its comparator checks a submitted proof against an approved specification, including the definitions that give the statement its meaning. A convenient name for a theorem is insufficient if the definitions underneath it have changed. The trust argument includes the kernel, machine/process model, crypto contracts, symbol extraction and build scripts; rustc correctness is not assumed because the proof targets the compiled artifact. The [announcement](https://deepmind.google/blog/introducing-alphaproof-code/) describes the division between human specification work and agent proof work. The [Signal Shot project](https://www.beneficialaifoundation.org/signal-shot) provides further context for the verification effort.

## A specification is a product decision

An important point in Swarat Chaudhuri's [interview with The Register](https://www.theregister.com/ai-and-ml/2026/11/10/google-deepmind-melds-humans-and-ai-agents-to-vet-signals-secure-messaging-techniques/5308625) is the effort required to choose specifications worth proving. The software-development version of that problem is familiar even without Lean.

Suppose a requirement says an invoice can be read only by its owner. An implementation and its tests might agree perfectly while checking ownership against a user ID supplied in the request body. Every sample request looks consistent, but the authorization boundary was never established. The requirement needs to identify which identity source is trusted, where the ownership record comes from, and what happens when either cannot be read.

The payout function has a quieter version of the same problem. Preserving the total is one requirement. Distributing it in proportion to weights is another. Choosing a deterministic tie-breaker is a third. A proof of conservation would not settle the fairness rule. That choice belongs to the people defining the behavior, and it should be visible before someone produces evidence that the implementation satisfies it.

I would keep the reviewed requirement separate from a candidate implementation. If a candidate needs a stronger precondition or a weaker postcondition, that becomes a reviewable change with a reason and an example of who it excludes. A developer or agent should not be able to make a failing check pass by silently changing which users, inputs or failures the claim covers.

It also helps to ask what would make the check fail. Removing the authorization comparison should invalidate an access-control claim. Dropping an output recipient should invalidate a payout claim. If both mutations still pass, more green checks do not fix the missing requirement. The next step is to strengthen the specification and verify the specification itself can distinguish the behavior people care about.

## The same failure modes at toy scale

The payout example exercises each of those ideas in a few hundred lines of JavaScript and Node's built-in test runner. The results below come from deterministic local checks recorded with Node v22.12.0.

**Bounded exhaustive checking.** Instead of three examples, the checker runs every input in a defined domain: totals from 0 to 60, one to three recipients, weights from 1 to 6. That is 15,738 cases. The rounded draft fails on the first interesting one: a total of 1 split between two equal weights returns `[1, 1]`. A largest-remainder version, which gives everyone the floor of their exact share and hands leftover units to the largest fractional remainders, passes every case.

That is an exhaustive result for the finite domain, assuming the checker and runtime work as intended. It is not a proof of the unbounded input contract; a total of 61 is outside that domain. What it does is turn the specification into something executable, which means the specification itself can be tested.

**Specification strength.** A weak specification, "the output has the right length and no part exceeds the total," accepts the broken draft and all four deliberately broken mutants. A strong specification, adding conservation (parts sum to the total) and proportionality (each part is the floor or ceiling of its exact share), rejects three of the four mutants.

**A surviving mutant.** The fourth mutant gives leftover units to the first recipients with a fractional share instead of the largest ones. Every part is still a floor or a ceiling, so the strong specification accepts it. Only an explicit largest-remainder rule rejects it. Whether that mutant is a bug depends on the requirement, and the code cannot tell you which. That is the specification problem in miniature.

**Vacuity.** A property hidden behind a guard that can never be true accepts a function that always returns `[999]`. Counting how many inputs satisfy the guard (zero) exposes it immediately. This is the toy version of DeepMind's requirement that agents show their hypotheses hold on some reachable state.

## What changes for developers

AI-assisted verification will reach ordinary codebases unevenly, and for most teams a Lean proof of the production binary is still not the right tool. But the habits that make those proofs trustworthy are available now.

1. **Write the property before the cases.** Conservation of money, monotonic version numbers, "no response without an authorization check." A named invariant is reviewable in a way that a list of examples is not.
2. **Test the specification as well as the code.** Inject plausible bugs and confirm the checks fail. Check that preconditions can actually be satisfied. Confirm a known historical bug would have been caught.
3. **Write down the trusted base.** Which compiler, runtime, library contracts and hardware behavior does your assurance assume? If nobody can list them, nobody can review them.
4. **Keep the specification away from the thing producing the evidence.** If one agent writes the code, the tests and the specification, it can make all three agree while the requirement goes unmet. A human-reviewed specification that changes only through a visible amendment is the cheapest version of DeepMind's gatekeeper.
5. **Spend proof where the stakes justify it.** Cheaper proofs change that calculation. They do not remove it. Choosing a trustworthy specification, maintaining the toolchain and reviewing the assumptions still take engineering effort.

The question I want reviewers to ask about any green check, whether it came from a test suite, a model or a proof assistant, is short: what exactly was established, about which artifact, assuming what? That answer defines the scope of the assurance. Without it, reviewers cannot tell whether a guarantee covers their use.

### Sources

- Chaudhuri et al., [AlphaProof Code: Verifying Signal's Security at the Machine-Code Level](https://deepmind.google/documents/36/Formal_Verification_of_Signal_4.pdf) (Google DeepMind, November 10, 2026)
- Google DeepMind, [Introducing AlphaProof Code](https://deepmind.google/blog/introducing-alphaproof-code/)
- [google-deepmind/code-verification](https://github.com/google-deepmind/code-verification) (Lean specifications, proofs and build instructions)
- The Register, [Google DeepMind melds humans and AI agents to vet Signal's secure messaging techniques](https://www.theregister.com/ai-and-ml/2026/11/10/google-deepmind-melds-humans-and-ai-agents-to-vet-signals-secure-messaging-techniques/5308625)
- Beneficial AI Foundation, [Signal Shot](https://www.beneficialaifoundation.org/signal-shot)
- [Runnable example for this article](https://github.com/JamesTsetsekas/gblog/tree/main/examples/article-series/passing-tests-is-not-a-proof)

**Review status:** DeepMind's results are self-reported and the proofs have not been independently rebuilt for this article. The toy example is a bounded check, not a formal proof. Sources last checked November 18, 2026.
