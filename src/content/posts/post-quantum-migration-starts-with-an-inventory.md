---
title: "Post-Quantum Migration Starts With an Inventory"
description: "NIST's post-quantum standards are final and its transition timeline is set. Before swapping algorithms, application teams need to know where cryptography lives, what it protects, for how long, and who can change it."
pubDate: "2026-11-19 00:00:00"
category: ["security", "technology"]
banner: "@images/banners/ZUZkJL1ik3SrCe2b1rf8obtmXlNnpEi7loouJ6mv.jpeg"
tags: ["Post-Quantum Cryptography", "ML-KEM", "ML-DSA", "Cryptographic Inventory", "NIST", "Migration"]
selected: false
---

The first question teams usually ask about post-quantum cryptography is which algorithm to use. For most applications the standards already answer it in a sentence: ML-KEM for key establishment, ML-DSA or SLH-DSA for signatures.

The harder question is the one nobody can answer from a standards document: where does your application use public-key cryptography, what is each use protecting, for how long, and who is able to change it? Until you can answer that, you do not have a migration plan. You have a shopping list.

## Where the standards stand

As of November 2026:

- **The core algorithms are final.** The Secretary of Commerce approved [FIPS 203, 204 and 205](https://csrc.nist.gov/projects/post-quantum-cryptography/news) in August 2024. FIPS 203 specifies ML-KEM, FIPS 204 specifies ML-DSA and FIPS 205 specifies the hash-based SLH-DSA.
- **The transition timeline is published.** NIST finalized [IR 8547, Transition to Post-Quantum Cryptography Standards](https://csrc.nist.gov/pubs/ir/8547/final), in October 2026. It says NIST will deprecate quantum-vulnerable public-key algorithms (RSA, ECDSA, EdDSA, finite-field and elliptic-curve Diffie-Hellman) after 2030 and disallow them under NIST standards after 2035. It recommends ML-KEM-768 as the default parameter set.
- **More is coming, but not yet final.** NIST selected HQC in March 2025 as an alternative KEM, and IR 8547 says a FIPS for it is under development. A FIPS for a signature algorithm derived from FALCON is also under development. Stateful hash-based signatures (LMS and XMSS, in SP 800-208) are approved but, as IR 8547 notes, demand strict state management, which suits firmware signing more than general use.
- **Protocols are catching up.** [RFC 10024](https://www.rfc-editor.org/rfc/rfc10024.html), published in August 2026, defines hybrid TLS 1.3 key agreement groups such as X25519MLKEM768 that combine ML-KEM with classical ECDHE.
- **US federal deadlines are tight.** [Executive Order 14412](https://www.govinfo.gov/content/pkg/DCPD-202600417/pdf/DCPD-202600417.pdf) sets December 31, 2030 for post-quantum key establishment and December 31, 2031 for post-quantum signatures on covered federal high value assets and high-impact systems. OMB memorandum [M-26-15](https://www.whitehouse.gov/wp-content/uploads/2026/06/M-26-15-Execution-of-the-Migration-to-Post-Quantum-Cryptography.pdf) implements the migration plan. Its first phase, covering 2026 and 2027, centers on inventory and prioritizes the covered sensitive and vulnerable systems.

These dates concern the covered federal agency systems; national security systems have a separate scope. Suppliers should check applicable procurement terms and their own contracts. A proposed procurement rule is not automatically a requirement on every vendor. The dates provide planning context for the example below, not a universal compliance deadline.

## Why inventory comes first

Different uses of public-key cryptography face different risks, on different clocks.

**Confidentiality has a head start problem.** IR 8547 calls out "harvest now, decrypt later": an adversary can record encrypted traffic or steal encrypted archives today and decrypt them once a capable quantum computer exists. Data that must stay secret for years is already exposed if the key exchange or key wrap protecting it is quantum-vulnerable. Nothing you do later fixes ciphertext someone has already copied.

**Signatures mostly fail forward.** A forged signature requires the quantum computer to exist at forging time. The exception is anything whose signatures must stay trustworthy for a long time, such as firmware, software updates, long-lived certificates and signed records. Devices in the field also need post-quantum verifiers before you can switch signers, which can take years by itself.

**Symmetric cryptography is mostly fine.** IR 8547 says approved symmetric primitives with at least 128 bits of classical security are believed to meet at least its lowest post-quantum security category. AES-256-GCM and HMAC-SHA256 do not need replacing.

**You do not control most of it.** TLS often terminates at a load balancer you rent. Keys sit in a cloud KMS. Tokens come from an identity provider. SDKs encrypt internally. For each of those, the migration step is a question to a vendor, with a date attached.

The useful framing for prioritization is simple. If the time your data must stay protected, plus the time it will take you to migrate, is longer than the time until a cryptographically relevant quantum computer arrives, that use is already late. Michele Mosca made a version of this argument early, [noting](https://eprint.iacr.org/2015/1075) that systems needing long-term confidentiality should migrate sooner. Nobody knows the last term. Treat it as a scenario, not a prediction.

## What an inventory record needs

A finding from a scanner is a location and an algorithm name. A useful inventory record needs more:

| Field | Example |
| --- | --- |
| Location | `src/backup.js:11`, a load balancer listener, a KMS key ID |
| Primitive and parameters | RSA-OAEP key wrap, ECDH P-256, Ed25519 |
| Purpose | confidentiality, signature, authentication, integrity, none |
| Protection lifetime | backups retained seven years, tokens valid 15 minutes |
| Owner | a named team, not "platform" in the abstract |
| Who controls the change | us, a vendor, a protocol standard |
| Migration path and estimated time | provider-supported PQ envelope, about four years including archives |

Formats exist for exchanging this. CycloneDX includes a [cryptography bill of materials](https://cyclonedx.org/capabilities/cbom/) (CBOM), and M-26-15 tells agencies to populate a central CBOM from software composition analysis, code scanning and network scanners. The format matters less than the purpose, lifetime and owner columns, which no tool fills in for you.

## A worked example

The accompanying [small inventory pipeline](https://github.com/JamesTsetsekas/gblog/tree/main/examples/article-series/post-quantum-migration-starts-with-an-inventory) runs against a fictional application. It is a teaching example, not a product. A scanner finds Node `crypto` calls with literal algorithm names, a JSON file holds human annotations, and a ranking step combines both under an assumed scenario.

The scanner found nine uses: RSA-signed session tokens, an RSA key wrap for seven-year backups, AES-256-GCM for the backups themselves, HMAC-SHA256 for webhooks, Ed25519 firmware signing keys, ECDH with a partner system, a signing call whose algorithm comes from configuration, MD5 for cache keys and a TLS configuration offering X25519 and P-256.

With an assumed ten-year scenario, the ranking came out like this:

1. **Backup key wrap (P1).** Seven years of confidentiality plus four years of migration exceeds ten. This is the harvest-now risk.
2. **Firmware signing (P2).** Devices verify updates for ten years and migration takes two.
3. **Partner ECDH and the configurable signer (review).** One has no owner yet. The other's algorithm is unknown until someone checks every environment. Neither is ever ranked as safe by default.
4. **TLS and session tokens (P3).** Five years of confidentiality and a one-year vendor migration fit inside ten. The token row assumes the issuer key is retired, and every verifier rejects it, within one year; short token expiry alone cannot prevent an attacker forging fresh tokens. Those are scenario assumptions, not observed vendor commitments.
5. **AES, HMAC (keep) and MD5 cache keys (document as non-security).**

Every finding needs an owner. For recognized quantum-vulnerable uses, the tool routes incomplete purpose, relevant lifetime or retirement annotations to review instead of assuming zero. Recognized symmetric primitives are classified by algorithm after the owner check without requiring lifetime fields; that does not establish that their implementation is safe. A TLS configuration that merely offers a hybrid group also remains a review item: the connection may negotiate a classical fallback, especially when TLS 1.2 is still permitted. Verify the minimum protocol and fallback policies, plus negotiated groups on representative connections.

Change the scenario and the plan changes. At five years, the TLS traffic becomes P1. At fifteen, nothing is P1 or P2, but the two review items stay where they are. That sensitivity is the honest part: the ranking is only as good as its assumptions, so the assumptions belong in the plan where people can argue with them.

The scanner's blind spots are tested too. It misses a third-party SDK that encrypts internally, a one-shot `sign()` call and anything configured outside the repository. Automated discovery finds candidates. People still have to find the rest.

## An honest migration plan for that example

- **Now:** finish the inventory, assign the missing owner, replace the configurable algorithm with an allowlist, and ask the load balancer vendor for a supported TLS 1.3 hybrid profile, an enforced minimum policy, and a date. Confirm negotiated groups; advertising a group does not establish its use.
- **Backups:** use a provider-supported post-quantum envelope or a reviewed hybrid profile whose recovery policy still protects the data key if the classical component fails. ML-KEM establishes a fresh shared secret; it does not directly encrypt an existing data key. Two independently usable wrappers for the same key leave an RSA-only recovery path. Inventory all recovery copies and rehearse restores before retiring legacy wrapping. Tie any FIPS claim to the actual module, mode and combiner, not an algorithm name. Already-copied archives remain subject to their old protection. [FIPS 203](https://csrc.nist.gov/pubs/fips/203/final), [NIST SP 800-227](https://csrc.nist.gov/pubs/sp/800/227/final).
- **Firmware:** stage post-quantum-capable verifiers by device cohort. Upgraded devices must require both signatures during a reviewed hybrid phase, then enforce the chosen post-quantum policy; accepting either signature retains the classical forgery path. Make the minimum acceptance policy resistant to rollback, and explicitly track cohorts still accepting legacy-only updates. Select algorithms and state handling with the device constraints in view.
- **Tokens:** follow the identity provider's roadmap, inventory issuer key lifetimes and every verifier, and specify when classical signing and verification end. Short token lifetimes help with replay; they do not compensate for a compromised signing key.
- **Agility:** route cryptographic calls through one small module and record the algorithm identifier next to every wrapped key and signature, so the next change is a configuration and data migration, not an archaeology project.

Plan for size and performance. Per FIPS 203, an ML-KEM-768 encapsulation key is 1,184 bytes and its ciphertext 1,088 bytes. Per FIPS 204, an ML-DSA-65 public key is 1,952 bytes and a signature 3,309 bytes, compared with 64 bytes for an Ed25519 signature ([RFC 8032](https://www.rfc-editor.org/rfc/rfc8032.html)). Those sizes affect packet budgets, database columns and constrained devices. Check library support as well. Node's documentation lists ML-KEM keys from v24.7.0 and ML-DSA keys from v24.6.0, both requiring OpenSSL 3.5 or newer. The example was checked with Node v22.12.0, which does not expose ML-KEM.

## Limits of this approach

Inventory does not remove uncertainty about when, or whether, large quantum computers arrive. Hybrid deployments add complexity, which IR 8547 acknowledges, and they are expected to be temporary. A ranking rule this simple ignores exposure, data volume and dependencies between systems. Treat it as a way to start a conversation with owners, not a substitute for one.

What the inventory does is turn a vague industry deadline into a list of decisions with names next to them. Every later step in the migration reads from that list, which is why it comes first.

### Sources

- NIST, [Post-Quantum Cryptography project news](https://csrc.nist.gov/projects/post-quantum-cryptography/news), including FIPS 203/204/205 approval, the HQC selection and SP 800-227
- NIST, [IR 8547: Transition to Post-Quantum Cryptography Standards](https://csrc.nist.gov/pubs/ir/8547/final) (October 2026)
- NIST, [FIPS 203](https://csrc.nist.gov/pubs/fips/203/final) and [FIPS 204](https://csrc.nist.gov/pubs/fips/204/final)
- OMB, [M-26-15: Execution of the Migration to Post-Quantum Cryptography](https://www.whitehouse.gov/wp-content/uploads/2026/06/M-26-15-Execution-of-the-Migration-to-Post-Quantum-Cryptography.pdf) (June 2026)
- IETF, [RFC 10024: Post-Quantum Traditional Hybrid Key Agreement Mechanisms for TLS 1.3](https://www.rfc-editor.org/rfc/rfc10024.html) (August 2026)
- CycloneDX, [Cryptography Bill of Materials](https://cyclonedx.org/capabilities/cbom/)
- Michele Mosca, [Cybersecurity in an era with quantum computers: will we be ready?](https://eprint.iacr.org/2015/1075)
- Node.js, [crypto documentation](https://nodejs.org/api/crypto.html)
- [Runnable example for this article](https://github.com/JamesTsetsekas/gblog/tree/main/examples/article-series/post-quantum-migration-starts-with-an-inventory)

**Review status:** Standards status checked against NIST, OMB and IETF pages on November 18, 2026. The example application is fictional and its ranking rule is a teaching simplification, not a standard.
