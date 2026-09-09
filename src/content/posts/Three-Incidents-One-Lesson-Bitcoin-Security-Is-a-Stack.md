---
title: "Three Incidents, One Lesson: Bitcoin Security Is a Stack"
description: "COLDCARD, BTCPay Server, and Liquid failed at different layers. Together they show why Bitcoin security must cover entropy, credentials, software boundaries, bridges, and operations."
pubDate: "2026-09-09 18:00:00"
category: ["bitcoin", "lightning", "security", "technology"]
banner: "@images/banners/bitcoin-security-stack.png"
tags: ["Bitcoin Security", "COLDCARD", "BTCPay Server", "Liquid", "Threat Modeling"]
oldViewCount: 0
selected: true
---

Three major Bitcoin-adjacent security stories in 2026 looked unrelated at first glance.

A firmware bug weakened seed generation on some COLDCARD devices. A BTCPay Server vulnerability exposed LND macaroon credentials. A software flaw reportedly allowed invalid L-BTC to reach Liquid’s peg-out process, prompting a network pause after roughly 4,000 BTC was withdrawn.

These were not three versions of the same exploit. The Bitcoin base layer did not fail in any of them. What connects them is more useful: **Bitcoin security is a stack, and a failure at one boundary can bypass the assurances of every layer below it.**

> **Information cutoff:** September 9, 2026. The COLDCARD and BTCPay disclosures are based on official advisories. Liquid had not yet published a final technical postmortem, so its root-cause details remain provisional.

![Five-layer model of Bitcoin security from key generation through operations](@images/posts/security-stack/security-stack.svg)

*Conceptual model by James Tsetsekas, based on the incidents and sources linked below.*

## The incidents were fundamentally different

| Incident | Boundary that failed | What the attacker gained | What did not fail |
| --- | --- | --- | --- |
| COLDCARD | Build and seed-generation path | The ability to search a drastically weakened key space offline | Bitcoin signatures and the device’s hardware random-number generator at runtime |
| BTCPay Server | Web application to LND credential storage | LND macaroon files that could authorize node actions and movement of funds | Bitcoin’s consensus rules and the LND seed-generation process |
| Liquid | Sidechain issuance and peg-out controls | A route from allegedly invalid L-BTC to real BTC held by the federation | Bitcoin base-layer consensus |

That distinction matters. “Bitcoin was hacked” is a tempting headline, but it collapses a complex system into one word. Bitcoin can be operating exactly as designed while an application hands out a bearer credential, a wallet derives keys from weak randomness, or a federation authorizes an invalid withdrawal.

## Layer one: key generation

A hardware signer can keep keys away from an internet-connected computer and still generate a weak key.

[Coinkite’s public incident record](https://blog.coinkite.com/adding-to-public-record/) says an inherited platform behavior, activated by a link-time error at a submodule boundary, weakened seed generation in affected firmware. The device’s hardware true random-number generator did not fail at runtime. The build delivered software that did not combine entropy as intended.

That is a sobering boundary failure: a secure component existed, but the compiled product did not use it correctly. An attacker did not need to communicate with a wallet. Once the seed space was weak enough, the search could happen offline.

The lesson is not that air gaps are useless. They meaningfully reduce remote attack surface. The lesson is that **air-gapped and well-seeded are different properties**. One cannot substitute for the other.

## Layer two: authorization

An LND macaroon is not a private key, but it is still a capability. Whoever holds a sufficiently privileged macaroon may be able to perform sensitive actions against the node.

The [BTCPay Server 2.4.2 advisory](https://blog.btcpayserver.org/security-advisory-btcpay-server-2-4-2/) disclosed an actively exploited vulnerability that could expose `.macaroon` files to an unauthenticated remote attacker. Updating closed the vulnerable path. Rotating LND’s macaroon root key invalidated credentials that might already have been copied.

This is the key distinction between patching and recovery:

- A patch prevents the vulnerable behavior from continuing.
- Credential rotation removes the authority of material that may already be outside your control.
- Transaction review looks for harm that occurred before either step.

For Umbrel operators, I published a separate, safety-first walkthrough: [How to Rotate LND Macaroons on Umbrel After the BTCPay Server 2.4.2 Advisory](/posts/rotate-lnd-macaroons-on-umbrel-after-btcpay-security-update).

## Layer three and four: applications, bridges, and federations

Liquid makes a different tradeoff. It is a federated Bitcoin sidechain: users can move value into L-BTC, transact with sidechain features, and later peg out through the federation. That system adds code, authorization rules, operators, and an asset-accounting boundary above Bitcoin.

According to [The Block’s September 6 report](https://www.theblock.co/news/defi/2026-09-06-liquid-network-pauses-after-purported-white-hat-hackers-withdraw-320-million-in-bitcoin-413626), roughly 4,000 BTC was withdrawn and the network was paused. A [September 7 follow-up](https://www.theblock.co/news/defi/2026-09-07-liquid-network-attacker-says-they-will-return-most-of-4000-btc-after-bug-fix-413673) reported that about 3,400 BTC had been returned after bridge nodes were patched, with about 598.5 BTC still outstanding at that time.

The reported mechanism is more important than the label applied to the actors. SideSwap said its peg-out service received L-BTC, burned it through a valid authorization path, and the federation released BTC. Reporting attributed the creation of that L-BTC to an Elements software bug. Liquid said the SideSwap PAK key itself was not compromised.

Until a final postmortem explains the defect and the missing controls, the responsible conclusion is narrow: a sidechain accounting or validation failure appears to have crossed a peg boundary. It does not follow that Bitcoin created invalid coins or that base-layer consensus accepted them.

## The shared failure pattern

The incidents point to four recurring engineering problems.

### 1. Security claims are layer-specific

“Hardware wallet,” “self-hosted,” and “federated” describe architectures. They are not complete security proofs. Ask what property is protected, against which attacker, and at which boundary.

### 2. Valid components can compose into an invalid system

A working random-number generator can be excluded by a build. A valid macaroon can be disclosed by a web bug. A valid peg-out request can be backed by invalidly issued sidechain assets. Composition is where many assurances disappear.

### 3. Credentials are authority

Macaroons, signer permissions, federation keys, API tokens, and session cookies differ cryptographically, but operators should ask the same question: what can a person do if this value is copied?

### 4. Recovery is part of the design

The system needs a rehearsed answer for weak seeds, stolen capabilities, invalid assets, a bad binary, and an emergency pause. If the first time the team maps those dependencies is during an incident, the architecture is incomplete.

## A practical review checklist

For any Bitcoin application that can affect funds, review the entire path:

1. **Generation:** Where do keys and secrets come from? Can the final binary prove it used the intended entropy path?
2. **Storage:** Which processes can read them? Are bearer credentials scoped and short-lived where possible?
3. **Authorization:** Does each signature or token grant exactly the intended action?
4. **Validation:** Is externally supplied state checked again at the final trust boundary?
5. **Dependencies:** Are submodules, lockfiles, toolchains, and build flags reproducible and tested?
6. **Operations:** Can you patch, rotate, migrate, pause, and audit without inventing the procedure during the emergency?
7. **Communication:** Can users tell the difference between an affected seed, a stolen credential, and a network-level failure?

## The deeper lesson

Bitcoin minimizes the trust required to agree on ownership and settlement. It does not eliminate the engineering around how people generate keys, run nodes, use sidechains, or authorize software.

That is not a criticism of Bitcoin. It is a reason to be precise about what Bitcoin secures—and disciplined about everything we build around it.

### Sources

- [Coinkite: Adding to the Public Record](https://blog.coinkite.com/adding-to-public-record/)
- [COLDCARD Security Status](https://coldcard.com/security/status)
- [BTCPay Server 2.4.2 Security Advisory](https://blog.btcpayserver.org/security-advisory-btcpay-server-2-4-2/)
- [The Block: Liquid pauses after reported withdrawal](https://www.theblock.co/news/defi/2026-09-06-liquid-network-pauses-after-purported-white-hat-hackers-withdraw-320-million-in-bitcoin-413626)
- [The Block: partial return after Liquid bridge patch](https://www.theblock.co/news/defi/2026-09-07-liquid-network-attacker-says-they-will-return-most-of-4000-btc-after-bug-fix-413673)

**Last verified:** September 9, 2026.
