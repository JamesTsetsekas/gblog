---
title: "An AI Produced a Proof. What Counts as Understanding It?"
description: "The claimed refutation of the Exponential Time Hypothesis arrived with machine-checked Lean proofs. That settles less than it seems: checking a proof, checking its statement and understanding it are three different jobs."
pubDate: "2026-11-19 00:00:00"
category: ["mathematics", "ai"]
banner: "@images/banners/article-series/ai-proof-and-understanding.webp"
bannerAlt: "A translucent bridge model and its drawings linked by an orange joint under a magnifying lens."
ogImage: "@images/banners/article-series/ai-proof-and-understanding-social.png"
tags: ["Mathematics", "Lean", "Formal Verification", "Exponential Time Hypothesis", "AI Research"]
selected: false
---

On October 26, 2026, OpenAI added a manuscript to its public [openai/math](https://github.com/openai/math) repository. The author line reads "OpenAI." The [repository README](https://github.com/openai/math) says the manuscripts were produced by an unnamed internal model. The title was blunt: ["The Exponential Time Hypothesis is False."](https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf) A few hours later, Anthropic published [a different AI-generated proof](https://github.com/anthropics/formal-math/tree/main/eth) of a similar result. Both came with Lean formalizations that a computer can check.

If the claim holds, it overturns a hypothesis that has organized decades of complexity theory. Refereeing the mathematics is a job for complexity theorists, and I won't attempt it here. What I can do is look closely at what was released and ask a narrower question: when a proof arrives this way, what has actually been established, and what is still left for people to do?

My answer is that three different jobs get blurred together. Checking that the proof is valid. Checking that the formal statement says what the paper claims. Understanding why it is true. Machines are now very good at the first, useful at the second, and have not settled the third on their own.

## What was released

The OpenAI manuscript, dated October 17 and revised October 25, gives a deterministic algorithm that counts the satisfying assignments of any fixed-width CNF formula in subexponential time and polynomial space. Applied to 3-SAT, it would refute the Exponential Time Hypothesis, which says 3-SAT needs time exponential in the number of variables. It does not claim P equals NP. The stated upper bound remains superpolynomial; it provides no polynomial-time guarantee.

The surrounding repository is candid about what kind of artifact this is. Its README describes hundreds of manuscripts with only part of the collection formalized, and calls the manuscripts "a form of raw research data, rather than polished academic papers." It warns that some unformalized results could have issues. The [release history](https://github.com/openai/math/blob/main/history.md) backs that up: on October 7, OpenAI withdrew three manuscripts after a sign error broke a key argument, and revised fourteen others.

The ETH result has a Lean formalization, but of a slightly weaker bound than the paper's main theorem, according to OpenAI's [scope note](https://github.com/openai/math/blob/main/lean/docs/378.md). The weaker bound is still subexponential. OpenAI's statement fixes a deterministic multitape machine per clause width, charges a canonical formula encoding, and bounds workspace polynomially in that input length. Its exponent scale contains a squared log-log factor; the manuscript's general bound has one log-log factor, and the linear-clause case has none. Anthropic's project includes a short statement file so a human reader can compare the formal definitions with the paper. Its README explicitly leaves that semantic comparison outside automated checking.

Later, the organizers of the community review [posted the prompt](https://ethdiscussion.blog/2026/11/12/openai-prompt-that-led-to-the-eth-refutation/) that OpenAI says led to the result. It asked for an unconditional refutation of the Strong Exponential Time Hypothesis, demanded that every quantifier be audited, and ended with a line I wish every AI research prompt included: "Useful rigorous partial progress is preferable to a fabricated solution."

## Job one: checking the proof

Lean's kernel is a small program that accepts a proof only if every step follows from the rules. Both projects also use Lean's comparator tool, which checks that the proved theorem matches a trusted challenge statement exactly, including every definition it depends on, and that the proof uses only Lean's standard axioms. Anthropic's continuous integration additionally replays the proof in nanoda, a second, independently written kernel.

The community [replication thread](https://ethdiscussion.blog/2026/10/30/lean-replications/) includes Totó Busnello's October 31 account and [archived receipts](https://doi.org/10.5281/zenodo.23820111). Busnello reports acceptance of both submitted developments under their comparators. His OpenAI run used Lean's default kernel; the Anthropic run also used nanoda. He distinguishes those executable checks from the separate task of judging whether the definitions formalize the intended mathematical claim. These are his reported runs, not runs performed for this article.

These recorded checks make one layer of assurance reproducible. A reader with suitable hardware and the documented environment can rerun them; that does not complete the statement or mathematical review.

## Job two: does the statement say the right thing?

A kernel can certify that a theorem follows from its definitions. It cannot certify that the definitions capture the idea. For a claim about running time, the details are everything: what counts as a step, which machine model, how a formula is encoded as input, whether one fixed algorithm must work for every input size.

Anthropic's [statement file](https://github.com/anthropics/formal-math/blob/main/eth/MainResults.lean) makes this reviewable. It defines the counting proposition and `ETHIsFalse` using finite-stack machines; [Solution.lean](https://github.com/anthropics/formal-math/blob/main/eth/Solution.lean) proves those propositions. The statement file also identifies the ordinary-machine simulation and formula re-encoding that remain outside Lean, describing the translation as "not part of the Lean statements or proofs." Those are bridges a human expert should inspect.

OpenAI's formal theorem is existential: some machine and some constants exist that meet the bound. An independent reproduction effort, carried out with AI assistance and published as [a verification record](https://github.com/unaltuzun/exponential-time-hypothesis-verify), audited that statement against the usual definition of ETH and reported no loophole. It also noted that the final step from the formal bound to "ETH is false" is informal in OpenAI's library, though trivial. The authors describe their own finding as "a negative finding by two AI reviewers, not a substitute for expert review." That is the right label.

Separately, [ComplexityLib's formal abstract merge](https://github.com/cslib-community/cslib-frontier/pull/1338), dated October 27, records native exact-counting, `not_eth` and `not_seth` headlines using the weaker quantitative route. That extends the formal endpoints beyond OpenAI's original library. It still leaves readers to assess the correspondence between the formal machine model and the mathematical question; it is not a verdict from the independent review group.

## Job three: understanding

Russell Impagliazzo, Ramamohan Paturi and Ryan Williams are organizing the community examination. Their [open letter](https://docs.google.com/document/d/1adB0IhJgLzsmbfCgoLrtoJTjnlPf74UnyjMo35P5JHo/edit) states: "Our involvement should not be taken as certification of the claim." They ask for scrutiny and for an understanding "that others can reconstruct, question, and build upon," and they separate examining the argument from studying its consequences.

That understanding is being built in public. Mark Sellke posted [slides outlining the algorithm](https://msellke.com/Files/ETH-False-Slides.pdf). Ryan O'Donnell wrote [an exposition](https://www.cs.cmu.edu/~odonnell/some_eth_false_exposition.pdf) that recasts the core as computing the permanent of a sparse matrix, and notes that it was produced through interaction with language models. Finding a frame where an unfamiliar argument becomes familiar is what understanding usually looks like in mathematics, and O'Donnell's note shows AI taking part in that work too.

Anthropic tried something stranger. Its README includes a condensed paragraph from which, it says, Claude Opus 5.5 can rederive a refutation of ETH, though only the weaker form that 3-SAT runs in time 2^(δn) for every δ > 0. That is a kind of explanation addressed to a model. It shows the idea is compact. Whether a seed another model can grow counts as human understanding is an open question.

Understanding also means knowing what does not follow. The OpenAI manuscript itself points out that some lower bounds once justified by ETH or its stronger cousin also follow from weaker hypotheses that may still hold. That kind of sorting is what lets a field absorb a result rather than just record it.

## What I would count

For a result like this, I would call it understood, as opposed to merely checked, when:

1. Independent kernels have accepted the proof, run by people outside the lab that produced it.
2. Experts outside that lab have compared the formal statement with the standard definition, and every informal bridge is written down.
3. At least one human-readable proof exists that experts can teach and that other researchers can modify.
4. The community can state both consequences and non-consequences with confidence.
5. Corrections, withdrawals and credit are recorded publicly, including credit for the people who checked, simplified and explained it. The reviewers' letter raises exactly this point.

By November 18, 2026, outside replications of the kernel checks exist (both kernels for Anthropic's proof, Lean's default kernel for OpenAI's), statement review is underway, and the rest are in progress. No published verdict from the review group was identified during source checking. That is not a criticism; careful examination takes time.

Developers face a smaller version of the same split. When an AI system hands you code with a machine-checked guarantee, the kernel can confirm the proof, but someone still has to confirm the specification means what the business needs, and someone has to understand the system well enough to change it next year. That engineering question is explored in [Passing Tests Is Not a Proof](/posts/passing-tests-is-not-a-proof). For what the ETH claim does and does not mean for Bitcoin, see [Will AI Break Bitcoin's Cryptography?](/posts/will-ai-break-bitcoin-cryptography)

### Further reading

- OpenAI, [The Exponential Time Hypothesis is False](https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf), [repository README](https://github.com/openai/math) and [release history](https://github.com/openai/math/blob/main/history.md)
- Anthropic, [formal-math/eth](https://github.com/anthropics/formal-math/tree/main/eth)
- Impagliazzo, Paturi and Williams, [open letter](https://docs.google.com/document/d/1adB0IhJgLzsmbfCgoLrtoJTjnlPf74UnyjMo35P5JHo/edit), and the [community discussion blog](https://ethdiscussion.blog/)
- Ryan O'Donnell, [Some exposition of "The Exponential Time Hypothesis Is False"](https://www.cs.cmu.edu/~odonnell/some_eth_false_exposition.pdf)
- Mark Sellke, [An Outline of OpenAI's 2^o(n)-Time k-SAT Algorithm](https://msellke.com/Files/ETH-False-Slides.pdf)
- Related reporting: [The New York Times, November 6, 2026](https://www.nytimes.com/2026/11/06/science/ai-exponential-time-hypothesis.html). This report was unavailable during source checking; the technical discussion relies on the linked primary artifacts.

**Review status:** The ETH result is an unreviewed preprint. Its Lean proofs check formal statements that are close to, but not identical with, the paper's strongest claims. Neither full proof development was rebuilt for this article. Sources last checked November 18, 2026.
