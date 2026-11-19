---
title: "Will AI Break Bitcoin's Cryptography? How to Read the Claim"
description: "A claimed AI refutation of the Exponential Time Hypothesis set off 'is Bitcoin safe?' questions. Here is what Bitcoin's security rests on, what the result does and does not touch, and where the real risks sit."
pubDate: "2026-11-19 00:00:00"
category: ["bitcoin", "cryptography", "security", "ai"]
banner: "@images/banners/bitcoin-security-stack.png"
tags: ["Bitcoin", "Cryptography", "Exponential Time Hypothesis", "Schnorr", "ECDSA", "Quantum Computing"]
selected: false
---

In late October 2026, OpenAI published a manuscript titled ["The Exponential Time Hypothesis is False"](https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf), produced by an unnamed internal model and accompanied by a Lean formalization. Within hours, Anthropic posted [its own AI-generated proof](https://github.com/anthropics/formal-math/tree/main/eth) of a similar result. Crypto media had fun with the name, since ETH is also Ether's ticker ([Decrypt](https://decrypt.co/381956/opena-eth-false-crypto-twitter-has-questions)), but a more serious question followed: if AI can overturn a long-standing hardness assumption, is Bitcoin's cryptography next?

My view is that this result gives no reason to think so, and that AI breaking Bitcoin's cryptography outright is unlikely. "Unlikely" is not "impossible," though, so this piece lays out the reasoning and what would change my mind.

## What Bitcoin's cryptography actually does

Bitcoin transaction validation operates on public ledger data. Peer-to-peer transport can separately encrypt communications, as in [BIP 324](https://github.com/bitcoin/bips/blob/master/bip-0324.mediawiki); that is distinct from the ledger's signature and hash guarantees:

- **Signatures** prove that the holder of a private key authorized a spend. Bitcoin uses ECDSA and, since Taproot, Schnorr signatures as specified in [BIP 340](https://github.com/bitcoin/bips/blob/master/bip-0340.mediawiki), both over the secp256k1 curve.
- **Hashes** (SHA-256, applied twice in proof of work and transaction IDs) bind blocks and transactions together and make mining costly.

There is no encrypted ledger to decrypt. A signature attack could recover a private key from a public key, the elliptic curve discrete logarithm problem (ECDLP), or otherwise forge a signature. Hash attacks have different consequences for commitments and mining: mining requires a hash below a difficulty target, and a generic collision is not automatically a shortcut to that target.

BIP 340 states its security argument plainly: Schnorr signatures are strongly unforgeable in the random oracle model assuming ECDLP is hard, with a target security level of 128 bits. Nothing in that argument mentions the Exponential Time Hypothesis.

## What the ETH claim says

The Exponential Time Hypothesis, formulated by Russell Impagliazzo and Ramamohan Paturi, says 3-SAT cannot be solved in time that grows more slowly than exponentially in the number of variables. The OpenAI manuscript, dated October 17 and revised October 25, gives, for each fixed clause width k, a deterministic exact-counting algorithm with a subexponential upper bound: a polynomial in the numbers of variables and clauses multiplied by 2 raised to O(n log log n / sqrt(log n)). Its constants can depend on k. This is a superpolynomial upper bound, not a polynomial-time guarantee or a proof that P equals NP.

Three caveats come from the primary sources themselves:

- **Review status.** The result is a preprint. Impagliazzo, Paturi and Ryan Williams are organizing a community examination, and their [open letter](https://docs.google.com/document/d/1adB0IhJgLzsmbfCgoLrtoJTjnlPf74UnyjMo35P5JHo/edit) explicitly withholds certification of the claim. No published verdict was identified during source checking as of November 18, 2026.
- **Practicality.** Anthropic's project page explicitly separates its asymptotic result from practical SAT-solving performance.
- **Scope.** The OpenAI manuscript notes that 2^o(n) bounds do not carry over through general polynomial-time reductions, so the result does not imply that NP problems in general have subexponential algorithms. For one family of candidate one-way functions with constant locality, it rules out exponential inversion hardness, then adds that this "does not rule out one-wayness against polynomial-time algorithms."

## Why the result does not reach secp256k1

### Bitcoin never rested on ETH

Cryptography depends on specific problems being hard on randomly generated instances: ECDLP on secp256k1, preimage resistance in SHA-256. ETH is a statement about the worst case of general SAT. ETH being true never proved ECDLP hard, and ETH being false does not make it easy. Cryptographers judge those specific problems through decades of cryptanalysis, not through ETH.

### Formula variables are not key bits

To point a SAT algorithm at a Bitcoin key, you would encode "find the private key for this public key" as a formula. The `n` in the running time then counts every variable in that formula, including every auxiliary variable the encoding needs. A particular encoding may introduce many more than 256 variables. As an illustration, a schoolbook circuit for one 256-by-256-bit multiplication has 65,536 partial-product AND gates. That describes one construction, not a lower bound on SAT encoding size or every scalar-multiplication implementation.

The best known generic classical attacks on a curve like secp256k1 take on the order of 2^128 group operations, consistent with BIP 340's 128-bit target. A useful SAT approach would need a concrete end-to-end cost comparison; SAT bit operations and elliptic-curve group operations are different units.

The theorems do not tell us whether it could, because their constants are unstated. The [Lean challenge](https://github.com/openai/math/blob/main/lean/ComparatorChallenges/SubexponentialSAT.lean) states an existential claim about a machine and constants; the [solution theorem](https://github.com/openai/math/blob/main/lean/OAI/Algorithms/SubexponentialSAT/SqrtLogSpace/Final.lean) supplies its proof. The accompanying [short script](https://github.com/JamesTsetsekas/gblog/tree/main/examples/article-series/will-ai-break-bitcoin-cryptography) makes that concrete:

- For the manuscript's bound on sparse formulas, 2^(A·n/√ln n), and a hypothetical input of one million variables, the growth term is about 269,000·A bits. The unknown constant A would need to be below about 0.0005 for that term alone to fall under 128 bits.
- For the exponential factor in the bound formalized in Lean, with A set to 1, that factor sits *above* 2^n, from about n = 49 until n is roughly 10^2390. That reproduces an arithmetic note posted to the community [ETH discussion blog](https://ethdiscussion.blog/2026/10/30/lean-replications/). With a small enough constant it would not. The theorem does not say which. This calculation omits its additional constant and polynomial in encoded input length; it does not time an algorithm.

None of that means the algorithm is slow in practice or fast in practice. It means an asymptotic theorem with existential constants cannot be read as a statement about 256-bit keys.

## Where AI could matter

**Cryptanalysis is not immune to machine learning.** In 2019, Aron Gohr used neural networks to [improve attacks on round-reduced Speck32/64](https://eprint.iacr.org/2019/037), a small lightweight block cipher, reducing the remaining security of an 11-round version to roughly 38 bits. That is a reduced-round cipher, not a full-strength primitive, but it shows models can find structure that classical analysis missed. AI systems are now producing claimed research-level results like the ETH manuscript. I cannot rule out that one eventually finds a real idea against ECDLP or SHA-256. If one does and it is published, cryptographers can check it like any other result, whoever or whatever wrote it.

**Implementation failures are the realistic threat.** Bitcoin's history has many cases of keys lost to bad software rather than broken math:

- In 2013, a flaw in Android's random number generator made keys generated by Android wallets vulnerable to theft, according to [Bitcoin.org's alert](https://bitcoin.org/en/alert/2013-08-11-android).
- [CVE-2023-39910](https://nvd.nist.gov/vuln/detail/CVE-2023-39910), the "Milk Sad" issue, limited Libbitcoin Explorer's seed entropy to 32 bits. NVD notes it was exploited in the wild.
- This year's [COLDCARD entropy failure](/posts/the-coldcard-entropy-failure-what-air-gapped-really-protects) weakened seeds through a build problem, not a cryptographic break.

Nonce handling is the classic signature example. The teaching script uses textbook ECDSA to sign two messages with the same nonce on the real secp256k1 parameters, then recovers the private key with a few lines of modular arithmetic. No discrete logarithm is computed. BIP 340 addresses nonce generation for Schnorr and warns about reusing deterministic nonce derivation across different schemes. AI that finds bugs faster helps both attackers and defenders here, which is the subject of [the companion article on patching](/posts/ai-vulnerability-discovery-patching-bottleneck). The defensive side is real too: DeepMind recently used AI agents to [prove scoped properties of a compiled one-to-one libsignal harness](/posts/passing-tests-is-not-a-proof).

## Quantum is a different question

Shor's algorithm, run on a large fault-tolerant quantum computer, would solve ECDLP efficiently. That threat has nothing to do with ETH or with classical AI.

The engineering estimates are now concrete. A March 2026 [Google Quantum AI whitepaper](https://quantumai.google/static/site-assets/downloads/cryptocurrency-whitepaper.pdf) estimates that its secp256k1 attack designs use about 1,200 logical qubits and 90 million Toffoli gates, or about 1,450 logical qubits and 70 million Toffoli gates, and fewer than half a million physical qubits on its assumed superconducting hardware. Appendix A describes zero-knowledge size checks and point-addition tests on 9,024 pseudorandom inputs per circuit variant; these are not a demonstrated full key-recovery run. An [IonQ preprint](https://eprint.iacr.org/2026/1916) estimates 25.7 days with 19,397 physical qubits on its assumed trapped-ion design, at an estimated 63% success probability. These are resource estimates, not demonstrations. NIST's [transition report](https://csrc.nist.gov/pubs/ir/8547/final) notes that a cryptanalytically relevant quantum computer has not yet been built. The same Google paper argues that Grover-based attacks on mining are not practically relevant.

Bitcoin's response is still at the proposal stage. [BIP 360](https://github.com/bitcoin/bips/blob/master/bip-0360.mediawiki) (Pay-to-Merkle-Root) is a draft that would protect outputs against long-exposure attacks only, and [BIP 361](https://github.com/bitcoin/bips/blob/master/bip-0361.mediawiki), on migration and sunsetting legacy signatures, is also a draft. Neither is activated.

## What would change my mind

I would treat the risk as real if I saw any of these:

- a public classical algorithm for discrete logarithms on prime-order curves like secp256k1 with a concrete cost well below 2^128, demonstrated on growing parameter sizes and reviewed by cryptographers;
- a concrete advance against full SHA-256 preimage or collision resistance, rather than reduced-round results;
- quantum hardware demonstrating logical qubit counts and error rates on the path the estimates describe.

Until then, the practical advice is unglamorous. Use a reviewed wallet or library and its scheme-specific signing API, letting that implementation handle key and nonce generation; caller-selected nonces belong only in the teaching fixture. Also treat wallet entropy as a security boundary, avoid exposing public keys longer than necessary, and follow the BIP 360 and BIP 361 discussions. In my view, the likeliest way to lose bitcoin in 2026 is still a software or operational mistake.

### Further reading

- OpenAI, [The Exponential Time Hypothesis is False](https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf) and [Lean scope note](https://github.com/openai/math/blob/main/lean/docs/378.md)
- Anthropic, [formal-math/eth](https://github.com/anthropics/formal-math/tree/main/eth)
- Impagliazzo, Paturi and Williams, [open letter to the community](https://docs.google.com/document/d/1adB0IhJgLzsmbfCgoLrtoJTjnlPf74UnyjMo35P5JHo/edit) and the [community discussion blog](https://ethdiscussion.blog/)
- Related reporting: [The New York Times, November 6, 2026](https://www.nytimes.com/2026/11/06/science/ai-exponential-time-hypothesis.html). This report was unavailable during source checking; the technical discussion relies on the linked primary artifacts.
- [Runnable examples for this article](https://github.com/JamesTsetsekas/gblog/tree/main/examples/article-series/will-ai-break-bitcoin-cryptography)

**Review status:** The ETH result is an unreviewed preprint with machine-checked Lean proofs of formal statements. The bounds arithmetic and nonce-reuse demonstration are local, deterministic checks. Nothing here is a forecast of quantum timelines. Sources last checked November 18, 2026.
