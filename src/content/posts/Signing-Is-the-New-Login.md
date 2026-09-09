---
title: "Signing Is the New Login"
description: "Nostr replaces platform-issued accounts with portable keys—but a signature is an authorization, not just authentication. Good signer UX must make that distinction visible."
pubDate: "2026-09-09 12:00:00"
category: ["nostr", "security", "technology"]
banner: "@images/banners/signing-is-the-new-login.png"
tags: ["Nostr", "NIP-07", "NIP-46", "Digital Signatures", "Product Security"]
oldViewCount: 0
selected: true
---

“Sign in with Nostr” looks like a familiar login button. Underneath, the mental model is different.

A traditional website authenticates an account stored by that website. Nostr applications work with a portable public key, and users can authorize signed events that other clients and relays will also recognize. The app does not need to issue the identity—and, when the architecture is sound, it does not need to hold the private key.

That is powerful. It also means a signature can do more than prove who you are. It can publish a note, change a profile, list a product, send an encrypted order, or authorize another protocol action.

Signing may be the new login, but treating every signature like a harmless login is a security mistake.

![An application proposes an event, an external signer asks for meaningful consent, and relays receive the signed result](@images/posts/signing/signer-flow.svg)

*Conceptual NIP-07 and NIP-46 flow by James Tsetsekas. Sources are linked below.*

## Authentication and authorization are not the same

Authentication answers: **Which key controls this identity?**

Authorization answers: **Does that identity approve this exact action?**

A site can use a signed challenge to establish a session, which behaves much like login. But Nostr events are portable statements. A signature over an event binds the key to its kind, tags, content, and timestamp. Once published, other parties may act on it without asking the original application what it meant.

That makes signing closer to approving a structured transaction than entering a password.

## NIP-07: a signer in the browser

[NIP-07](https://github.com/nostr-protocol/nips/blob/master/07.md) defines an optional `window.nostr` interface that browser extensions can expose. An application can request the user’s public key and ask the extension to sign an event. Optional methods support NIP-44 encryption and decryption.

The key advantage is separation. The webpage proposes an event; the extension that holds or connects to the key decides whether to sign it. The site receives the signed event, not the user’s private key.

But the browser is a crowded security boundary. A signer must know which site made the request, display what the event will do, and apply permissions narrowly. If it shows only a hash or raw JSON, most users cannot give meaningful consent.

## NIP-46: a remote signer

[NIP-46](https://github.com/nostr-protocol/nips/blob/master/46.md) lets a client communicate with a remote signer through encrypted Nostr messages. This can keep durable keys on a separate device or service and expose them to fewer applications.

The split is useful across phones, desktops, and specialized signing devices. It also creates a protocol and availability dependency: the client and signer must pair securely, route requests, enforce permissions, and give the user enough context to approve or reject an action.

Remote does not automatically mean safer. A signer that approves every request silently has moved the key without improving the authorization boundary.

## What a good signing prompt should show

A meaningful consent screen should translate protocol fields into user intent:

- **Action:** Publish a product, update a profile, send an order, or authenticate a session.
- **Requester:** The application and origin asking for the signature.
- **Audience:** Public relays, a named recipient, or an encrypted conversation.
- **Material details:** Product, price, recipient, expiration, permissions, or other fields that affect the outcome.
- **Persistence:** Whether the event is replaceable, revocable only by convention, or effectively permanent once copied.
- **Frequency:** One signature, a limited session, or ongoing permission to sign a class of events.

The event kind alone is not enough for most users. “Approve kind 30402” is protocol-accurate but product-hostile. “Publish this product listing to three relays” is a decision a merchant can understand.

## Permission models need a middle ground

Asking about every low-risk event creates approval fatigue. Granting a client unlimited signing authority recreates the risk external signing was meant to reduce.

A better model is scoped permission:

- authorize specific event kinds;
- bind the grant to one application origin;
- limit recipients or relays where appropriate;
- set a clear expiration;
- require fresh confirmation for high-impact or unusual events;
- make permissions reviewable and revocable;
- show a receipt or history of what was signed.

The signer should also reject structurally invalid or unexpectedly large requests before asking the user. Consent is not input validation.

## Keys are portable; consequences are too

A password leak may compromise one service. A Nostr private key can control a portable identity across many applications. That improves user ownership and increases the cost of bad key handling.

Builders should therefore avoid:

- asking users to paste private keys into ordinary web forms;
- storing durable keys in application databases or analytics;
- logging unsigned or decrypted sensitive event content unnecessarily;
- using vague, reusable challenges that can be replayed as authentication;
- silently signing content assembled from untrusted remote data;
- presenting a publish action as though it were only a login.

Users should prefer reputable external signers, verify the requesting application, protect recovery material, and pause when a signer asks to approve an action they did not initiate.

## What this means for commerce

In a Nostr marketplace such as [Conduit](https://conduit.market/), one identity can publish a catalog, receive encrypted order messages, and participate through different compatible clients. The signer boundary is what allows the application to help without owning the identity.

Commerce also makes semantic prompts essential. A merchant needs to know whether they are updating inventory or publishing a new offer. A buyer needs to distinguish a private order message from a public post. The product must communicate the intent before the signer turns it into a portable fact.

## The next login button

Portable cryptographic identity is a genuine improvement over creating a new password and captive account on every platform. But the new login button carries more expressive power than the old one.

The winning signer experience will hide protocol trivia without hiding consequences. It will keep keys outside applications, make authorization specific, and let users understand the sentence their signature is about to say.

### Sources

- [NIP-07: `window.nostr` capability for web browsers](https://github.com/nostr-protocol/nips/blob/master/07.md)
- [NIP-46: Nostr Remote Signing](https://github.com/nostr-protocol/nips/blob/master/46.md)
- [NIP-17: Private Direct Messages](https://github.com/nostr-protocol/nips/blob/master/17.md)
- [Conduit public monorepo](https://github.com/Conduit-BTC/conduit-mono)

**Last verified:** September 9, 2026.
