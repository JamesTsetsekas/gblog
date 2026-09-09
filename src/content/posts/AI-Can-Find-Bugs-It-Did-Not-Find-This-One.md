---
title: "AI Can Find Bugs. It Didn’t Find This One."
description: "Coinkite’s entropy incident is a useful correction to AI-security hype: models can expand review capacity, but build boundaries, hidden state, and missing tests still demand deterministic evidence."
pubDate: "2026-09-09 15:00:00"
category: ["ai", "security", "technology", "bitcoin"]
banner: "@images/banners/ai-security-review.png"
tags: ["AI Security", "Code Review", "COLDCARD", "Software Supply Chain", "Testing"]
oldViewCount: 0
selected: true
---

The obvious version of this article would have been: “AI found the COLDCARD bug, so put an agent in every security review.”

That version would be false.

[Coinkite’s public investigation](https://blog.coinkite.com/adding-to-public-record/) says AI-assisted code review conducted before the exploit did not catch the entropy weakness. After the incident, the company also tested multiple frontier models against the code and says they did not independently identify it.

That does not mean AI code review is useless. It means we should stop treating a plausible explanation from a model as proof that the relevant system property holds.

## Why this bug was a hard target

The weakness reportedly emerged from inherited platform behavior activated by a link-time error at a submodule boundary. The intended source-level path and the behavior of the final build were not the same.

That is difficult for any reviewer—human or model—because the defect is spread across context:

- source code in more than one repository or submodule;
- build flags and link behavior;
- assumptions about an inherited platform implementation;
- the gap between a named security component and its actual use;
- the runtime behavior of a hardware target;
- a missing end-to-end assertion about the final entropy path.

Give a model one changed function and it may explain that function beautifully. If the failure only exists after a particular build composition, the explanation can be locally correct and globally irrelevant.

## The three limits of AI review

### 1. The review is bounded by the context

A model cannot inspect a toolchain, binary, dependency, or runtime trace it was never shown. Repository-scale agents can gather more context, but they still need an explicit map of which artifacts and build boundaries matter.

### 2. Model confidence is not coverage

A review response is a sample from a probabilistic system. Receiving no finding does not establish that every path was checked. Asking three models and getting three clean reports is not equivalent to a proof, a property test, or exhaustive analysis.

### 3. Security depends on observable invariants

“This function calls the RNG” is weaker evidence than “the release binary fails a test when either required entropy source is removed.” The latter ties the assurance to behavior we can reproduce.

## What AI is genuinely good at

AI can still improve a mature security process. I find it useful for:

- mapping unfamiliar code and identifying trust boundaries;
- generating variant searches after one vulnerability is understood;
- noticing suspicious error handling, unsafe defaults, and inconsistent validation;
- proposing property tests and fault-injection cases;
- comparing a patch with its stated security invariant;
- tracing which callers, serializers, and configuration paths touch sensitive data;
- turning a threat model into a review checklist;
- reviewing repetitive changes where humans lose attention.

Those are force multipliers. They produce leads, questions, and tests—not a certificate that the system is safe.

## A better AI-assisted security workflow

The order matters.

### 1. State the invariant

Write the property in a form that can fail. For a seed generator: every production seed must incorporate the required independent entropy sources, and generation must stop if the required path is unavailable.

### 2. Map the complete artifact path

Include source repositories, submodules, generated code, flags, linker behavior, firmware packaging, release signing, and hardware execution. Ask the AI to identify assumptions between those stages.

### 3. Use models adversarially

Do not ask only “is this secure?” Assign competing tasks: construct an exploit hypothesis, challenge the threat model, list unobserved state, and identify which conclusion cannot be verified from the supplied evidence.

### 4. Turn claims into deterministic tests

Use unit tests, integration tests, property tests, fuzzing, static analysis, fault injection, and instrumented release builds. A strong model finding should make the test suite stronger even after the chat is gone.

### 5. Review the build, not just the diff

Reproduce the shipped artifact and test it on the real target. Record dependency revisions and build inputs. Treat toolchain and submodule changes with the same suspicion as application code.

### 6. Keep humans accountable for the decision

The reviewer approving a security-sensitive release should be able to name the invariant, the evidence, the limits of that evidence, and the recovery path if the assumption is wrong.

## “The AI missed it” is also too simple

Security failures are rarely caused by one reviewer failing to be omniscient. If a critical property exists only as an assumption in someone’s head, every review process is fragile.

The more useful questions are:

- Was the model shown the final build path?
- Did the prompt ask about dependency and link-time behavior?
- Was there a test that could observe the missing entropy?
- Did the organization treat a clean AI response as evidence of coverage?
- Could an independent team reproduce the assurance from the release artifact?

Coinkite’s account is valuable precisely because it resists an easy AI success story. Models were part of the process. They did not catch the defect. The response should be better engineering around them, not a pendulum swing between “AI replaces review” and “AI has no place in review.”

## The durable standard

Use AI to search wider, ask more questions, and draft more tests. Use deterministic systems to decide whether an invariant holds. Use humans to own the threat model and the release decision.

AI can find bugs. When it does, take the win. When it does not, your security case still needs to stand on evidence that can be rerun without asking a model to sound confident.

### Sources

- [Coinkite: Adding to the Public Record](https://blog.coinkite.com/adding-to-public-record/)
- [COLDCARD Security Status](https://coldcard.com/security/status)

**Last verified:** September 9, 2026.
