---
title: "Why We’re Building Commerce on Nostr"
description: "A product engineer’s view of why Conduit uses Nostr and Lightning for portable identity, open product discovery, encrypted orders, and direct payments—and where the hard work remains."
pubDate: "2026-09-09 13:00:00"
category: ["nostr", "bitcoin", "lightning", "technology"]
banner: "@images/banners/building-commerce-on-nostr.png"
tags: ["Conduit", "Nostr", "Lightning Network", "Decentralized Commerce", "Product Engineering"]
oldViewCount: 0
selected: true
---

I work on [Conduit](https://conduit.market/) as a Product Engineer. We are building commerce on Nostr and Bitcoin Lightning, which invites a fair question: why use an open event protocol for something as operationally messy as buying and selling physical goods?

The short answer is portability. A conventional marketplace owns the account, catalog, reputation surface, message history, payment rails, and customer relationship. Nostr lets us design those pieces as signed data that users can publish through shared relays and authorize with keys they control. Lightning lets payment move directly rather than through a balance held by Conduit.

That does not make trust disappear. It changes where trust lives and gives users a credible way to take their identity and public data elsewhere.

> The views here are my own. This article covers only Conduit’s public architecture and open specifications; it does not disclose private company, merchant, or customer information.

![Buyer and merchant exchanging Nostr events and a direct Lightning payment](@images/posts/conduit-commerce/commerce-flow.svg)

*Conceptual flow by James Tsetsekas, based on Conduit’s [public repository](https://github.com/Conduit-BTC/conduit-mono), the Gamma Market Specification, and the NIPs linked below.*

## The account is a key, not a database row

On most marketplaces, identity begins with an email address and a record in the platform’s database. The platform can restore access, but it also decides whether the account exists and where it works.

On Nostr, identity begins with a public/private key pair. Applications can request signatures through an external signer rather than holding the durable private key themselves. [NIP-07](https://github.com/nostr-protocol/nips/blob/master/07.md) defines a browser signing interface. [NIP-46](https://github.com/nostr-protocol/nips/blob/master/46.md) defines communication with a remote signer.

For Conduit, this makes the product boundary clearer: the application assembles the action a user wants to take; the signer authorizes it. The identity is usable in other Nostr applications because Conduit did not invent or exclusively issue it.

That is a meaningful property, not a slogan. It also gives us a harder UX problem. Users must understand what they are signing, recover their identity safely, and avoid granting a malicious application more authority than intended.

## Products are public events

Nostr relays store and distribute signed events. A merchant can publish product listings as addressable events and send them to multiple relays. A buyer can discover those events without a central marketplace API being the only source of truth.

Conduit follows public marketplace conventions, including product listing event kind `30402`. The [Gamma Market Specification](https://github.com/GammaMarkets/market-spec/blob/main/spec.md) expands the model for products, collections, merchant preferences, and order flows. [NIP-99](https://github.com/nostr-protocol/nips/blob/master/99.md) provides the broader classified-listing vocabulary.

An open event model provides several benefits:

- a merchant can publish through more than one client;
- a catalog can be replicated across independent relays;
- other applications can index compatible listings;
- a user can verify who signed a listing;
- an application can recover from a relay outage by reading another source.

It also introduces distributed-systems reality. Relays can disagree, reject events, go offline, retain stale versions, or apply different policies. Deletion is a request rather than a guarantee. The product has to reconcile versions, show useful pending states, retry safely, and avoid pretending eventual consistency is instant certainty.

## Orders should not be public listings

A product catalog benefits from public discovery. An order may contain quantities, addresses, contact details, and a conversation that does not belong on a public feed.

The [Gamma Market Specification](https://github.com/GammaMarkets/market-spec/blob/main/spec.md) uses the private messaging model around [NIP-17](https://github.com/nostr-protocol/nips/blob/master/17.md). NIP-17 combines NIP-44 encryption with NIP-59 gift wrapping to improve the confidentiality of message content and hide some routing metadata from casual observation.

“Encrypted” is not the same as “metadata-free.” Relay operators can still observe connections and timing, and endpoints still see the decrypted order. Applications must keep sensitive fields out of logs, analytics, crash reports, notifications, and URLs. Protocol privacy is only one layer of product privacy.

## Lightning makes the payment direct

Conduit is designed so that it does not need to custody user funds. A merchant can receive through Lightning mechanisms such as invoices, WebLN, or Nostr Wallet Connect, depending on the flow and wallet capabilities.

That removes a platform balance from the middle, but it does not remove commerce risk. A successful payment does not prove that a package was delivered. A signed listing does not guarantee product quality. A decentralized protocol does not automatically supply refunds, dispute resolution, tax handling, shipping logistics, or reputation.

The honest promise is not “trustless shopping.” It is **less platform custody, more portable identity and data, and more freedom to choose the services around the transaction.**

## Why not put everything on-chain?

Product edits, messages, inventory changes, and discovery queries do not need global Bitcoin consensus. Putting that workload on-chain would be expensive, slow, and terrible for privacy.

Nostr handles signed communication and discoverability. Lightning handles fast Bitcoin-denominated payment. Bitcoin provides the monetary settlement foundation. Each protocol has a narrower job, which is healthier than asking one ledger to become an account system, catalog database, private messenger, and checkout API.

## The product work is in the boundaries

Open protocols remove some central dependencies and expose new edges:

- **Signer boundary:** make the authorization understandable without taking custody of the key.
- **Relay boundary:** tolerate partial success and make synchronization state visible.
- **Message boundary:** validate liberal incoming events while emitting a strict canonical form.
- **Payment boundary:** connect invoices, proofs, orders, and merchant state without storing wallet secrets.
- **Privacy boundary:** keep order content and user identifiers out of telemetry and diagnostics.
- **Recovery boundary:** let users reconnect a signer, restore local state, or switch relays without creating duplicate orders or payments.

This is why building on a protocol is not the same as exposing a protocol. Most users should not need to know event kinds to buy an item. The application’s job is to turn those primitives into clear state, safe defaults, and recoverable actions without quietly recreating the lock-in the protocol was meant to avoid.

## What success looks like

I do not think success is every buyer becoming a relay expert. Success is a normal commerce experience with unusual exit rights:

- the merchant controls the identity that signed the catalog;
- the catalog can outlive one application or relay;
- the buyer authorizes actions through a signer they chose;
- sensitive order details are encrypted between the parties;
- payment goes to the merchant without Conduit holding the balance;
- compatible clients can build on the same public protocol.

Nostr gives us the substrate for that model. Lightning gives it a native payment rail. The remaining work is product engineering: making the guarantees legible, the failure modes survivable, and the experience good enough that decentralization feels like ownership rather than homework.

### Public sources

- [Conduit public monorepo](https://github.com/Conduit-BTC/conduit-mono)
- [Gamma Market Specification](https://github.com/GammaMarkets/market-spec/blob/main/spec.md)
- [NIP-07: Browser extension for signing](https://github.com/nostr-protocol/nips/blob/master/07.md)
- [NIP-17: Private Direct Messages](https://github.com/nostr-protocol/nips/blob/master/17.md)
- [NIP-46: Nostr Remote Signing](https://github.com/nostr-protocol/nips/blob/master/46.md)
- [NIP-99: Classified Listings](https://github.com/nostr-protocol/nips/blob/master/99.md)

**Last verified:** September 9, 2026.
