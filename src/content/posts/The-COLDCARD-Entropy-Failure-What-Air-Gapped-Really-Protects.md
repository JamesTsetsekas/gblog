---
title: "The COLDCARD Entropy Failure: What Air-Gapped Really Protects"
description: "The 2026 COLDCARD incident did not defeat the air gap. It exposed a different boundary: whether the shipped firmware generated a seed with the entropy users expected."
pubDate: "2026-09-09 17:00:00"
category: ["bitcoin", "security", "technology"]
banner: "@images/banners/coldcard-entropy-failure.png"
tags: ["COLDCARD", "Hardware Wallets", "Entropy", "Bitcoin Security", "BIP39"]
oldViewCount: 0
selected: true
---

The 2026 COLDCARD incident is easy to describe badly.

The devices were not remotely taken over. The hardware random-number generator did not suddenly fail in the field. Bitcoin’s cryptography was not broken. Instead, affected firmware could generate seeds with dramatically less effective entropy than users reasonably believed they had.

That difference teaches a broader lesson: an air gap protects a communication boundary. It does not prove that the software on the isolated device generated a strong secret.

> **If you generated a seed on an affected COLDCARD, use the current [official security status and migration instructions](https://coldcard.com/security/status). Updating firmware alone does not repair an existing weak seed.**

## What Coinkite has confirmed

[Coinkite’s ongoing public record](https://blog.coinkite.com/adding-to-public-record/) says the weakness came from inherited platform behavior activated by a link-time error at a submodule boundary. In practical terms, the intended entropy composition did not survive the final build as expected.

The hardware true random-number generator itself did not fail at runtime. But a secure entropy source only helps when the software actually mixes its output into seed generation correctly.

The result was an offline attack opportunity. If an attacker can narrow the possible seed space enough, they can generate candidate keys, derive addresses, compare them with blockchain activity, and spend matching funds. They do not need to call the device, defeat its PIN, or cross its air gap.

The impact also varied by model and firmware generation. Coinkite describes older Mk2 and Mk3 devices as more severely weakened and lists fixed firmware and migration guidance for the affected model families. That guidance may change as the investigation develops, so I will not reproduce a version checklist that could go stale. Use the live official page.

## What an air gap does—and does not—promise

An air-gapped signer can substantially reduce exposure to malware on a daily-use laptop. Ideally, the host passes an unsigned transaction in, the device displays what it will authorize, and a signature comes back out. The private key never has to enter the networked computer.

That architecture can help against:

- remote extraction of a correctly generated private key;
- host malware that tries to read secret material directly;
- accidental cloud backup of a seed stored only on the signer and paper or metal;
- some classes of malicious transaction substitution, if the device display is verified.

It does not automatically protect against:

- weak seed generation inside the device;
- a malicious or incorrectly built firmware image;
- misleading transaction details on the trusted display;
- supply-chain tampering;
- physical coercion or recovery-phrase theft;
- unsafe backup and inheritance procedures.

Security properties do not become universal because the product sits offline.

## Why build boundaries matter

Developers tend to review source files as though the source tree were the product. It is not. The product is the binary produced after configuration, conditional compilation, dependency resolution, linking, optimization, and packaging.

This incident reportedly lived at exactly that seam. That suggests tests must exercise the shipped artifact, not merely the intended function in isolation.

For entropy-sensitive software, useful controls include:

- deterministic, reproducible builds that make unexpected changes visible;
- tests against the release binary and its exact build flags;
- assertions that every required entropy source contributes to the final seed path;
- fault-injection tests that disable or repeat one source and verify fail-closed behavior;
- independent derivation tests from recorded, non-secret test vectors;
- review of submodule and toolchain changes as first-class code changes;
- device-level statistical checks as a warning signal, not a proof of cryptographic quality.

No statistical test can certify that a small sample is cryptographically unpredictable. The strongest evidence comes from architecture, auditable code paths, controlled builds, and deterministic tests that prove the intended sources were used.

## Dice rolls: useful, but only when verified

COLDCARD supports user-supplied dice rolls as another entropy source. Its status page recommends at least 50 fair rolls for roughly 128 bits of entropy and 99 or more for roughly 256 bits.

That can be valuable because it adds a source the device manufacturer did not create. But “I rolled dice” is not the same as “the final seed incorporated the rolls correctly.” A robust workflow needs a way to verify the result independently and must use a fair physical die, accurate entry, and enough rolls.

A BIP39 passphrase creates a similar nuance. Coinkite says a strong passphrase can add a meaningful barrier. It does not retroactively make the original seed generation correct, and a weak or reused passphrase is not a rescue plan.

## If your seed may be affected

The recovery pattern is migration, not reassurance:

1. Read the current [COLDCARD security status](https://coldcard.com/security/status) and identify the device, firmware, and seed-generation circumstances.
2. Update devices using the vendor’s current verified procedure, but do not assume the update changes an existing seed.
3. Create a new wallet from independently strong entropy using fixed firmware and current official guidance.
4. Verify receive addresses on trusted displays and make a small test transfer if appropriate for your setup.
5. Move the full balance to the new wallet and treat the old seed as permanently compromised.
6. Review transaction history for anything you do not recognize.
7. Replace recovery backups and document which material is obsolete so it cannot be restored later by mistake.

Do not publish a seed, passphrase, extended public key, addresses tied to your identity, or device backup while asking for help.

## The right conclusion

Hardware signers remain an important security tool. Air gaps remain useful. The failure is in treating either term as a complete threat model.

A safer question is: **what evidence connects the physical entropy source, the reviewed code, the release build, the device behavior, and the seed I actually received?**

That question is harder than checking a product feature box. It is also the question the incident says we need to ask.

### Official sources

- [COLDCARD Security Status](https://coldcard.com/security/status)
- [Coinkite: Adding to the Public Record](https://blog.coinkite.com/adding-to-public-record/)

**Last verified:** September 9, 2026. Coinkite describes its status page as a living postmortem; revisit the official sources for updates.
