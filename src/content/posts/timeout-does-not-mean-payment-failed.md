---
title: "A Timeout Does Not Mean a Payment Failed"
description: "When a payment request times out, the outcome is unknown, not failed. Idempotency keys, payload binding, durable state and reconciliation, shown with a simulated processor you can run and break."
pubDate: "2026-11-19 00:00:00"
category: ["software-engineering", "security"]
banner: "@images/banners/article-series/timeout-does-not-mean-payment-failed.webp"
bannerAlt: "A single orange token reaches its tray while an acknowledgement channel stops at a frosted partition."
ogImage: "@images/banners/article-series/timeout-does-not-mean-payment-failed-social.png"
tags: ["Payments", "Idempotency", "Reliability", "Reconciliation", "API Design"]
selected: false
---

A customer taps Pay. The spinner runs for thirty seconds and your server logs a gateway timeout from the payment provider. The tempting handler says "payment failed, please try again," and the tempting retry creates a new charge.

The customer may now be charged twice, and nothing in your logs will say so. A timeout reports that your client stopped waiting. It does not report what the provider did.

## Three worlds, one symptom

From the client's side, a timeout is compatible with at least three realities:

1. The request never reached the provider, and nothing happened.
2. The provider processed it, the charge succeeded, and the response was lost on the way back.
3. The provider is still working on it, and the charge will land after you gave up.

The client sees the same thing in all three. HTTP's own semantics say as much: the HTTP specification [advises clients not to automatically retry a request with a non-idempotent method such as POST](https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods) unless they know the request is actually idempotent or can detect that the original was never applied. Creating a charge is the textbook case of a request that needs one of those two properties before anyone retries it.

Stripe's documentation for its v1 API is blunt about this. [Restoring connectivity does not tell you whether the original request succeeded](https://docs.stripe.com/error-low-level), and a 500 response should be treated as indeterminate, since the operation might have produced side effects. That is one vendor's guidance, but the IETF draft and AWS design guidance below converge on the same ideas, providing a common vocabulary rather than a universal API contract.

## Idempotency keys make a retry safe to send

The standard tool is a caller-supplied idempotency key. The client generates a unique value for one logical operation and sends it with every attempt; the server remembers the first result for that key and returns it on repeats. Stripe [saves the status code and body of the first request made with a key](https://docs.stripe.com/api/idempotent_requests) once execution starts and replays it on retries, including errors. An [IETF Internet-Draft](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/) is working to standardize an `Idempotency-Key` header; its latest revision is dated October 2026 and, being a draft, is work in progress and not a standard. Amazon's engineers explain [why they prefer a caller-provided client request identifier](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) to deriving a token from the request parameters: two identical requests from the same caller can be intentional, and an explicit identifier lets the caller state intent.

Where the key comes from matters more than people expect. Stripe notes that if your application retries across separate calls or process restarts, you need to [generate and persist a key for the operation and supply it to every attempt](https://docs.stripe.com/error-low-level). A key generated fresh inside the retry loop is just a new charge with extra steps.

## Bind the payload to the key

A key says "this is the same operation." It is only meaningful if the payload is also the same. What happens if the amount changes between attempts?

Providers defend against this. Stripe compares incoming parameters with the original request and errors on a mismatch. The IETF draft says a reused key with a different payload should get a 422, a concurrent duplicate a 409, and it describes an optional fingerprint of the request. AWS describes returning a validation error for a parameter mismatch and storing the original parameters alongside the identifier to support that check.

You should enforce the same thing on your side, before the provider has to. In the demo, the order row stores the amount, currency and key together when the order is created. The send path reads them from storage and never from the caller, so a retry cannot drift. Changing the amount is allowed only while the order has never been sent. After a send, the original may have succeeded, so a new key with a new amount could charge twice. Stripe's guidance says the same thing: if the parameters must change, first establish that the original did not succeed and is not still running, and [reconcile it](https://docs.stripe.com/error-low-level) if the outcome is unknown.

## State must outlive the process

The key and payload have to be stored before the first attempt, in storage that survives a restart. That sounds obvious until you look at where the "pending payment" often lives: in a variable, a session, a queue message with no record behind it.

The demo uses a small state machine in SQLite:

- `CREATED`: intent, key and payload stored, nothing sent.
- `SENDING`: a request may have reached the provider. The outcome is unknown.
- `PAID` and `DECLINED`: the provider gave a definite answer.
- `NEEDS_REVIEW`: the demo cannot decide safely.

The rule that matters is that a timeout never moves an order to a failure state. It leaves the order in `SENDING`. The write to `SENDING` happens before the network call, so a crash between "provider charged" and "we recorded it" leaves a record that says "we may have sent this, with this key."

To see why this matters, one test runs the same crash against an in-memory store. After the restart there is no order, no key and no memory of the attempt. The checkout page is retried and a new random key is generated. The provider now holds two charges for the order.

## Reconcile, and respect the retention window

An order stuck in `SENDING` needs a resolver. The demo's reconcile step asks the provider what exists for this order. One charge means mark it paid. More than one means flag it for review. No charge found does not rule out an in-flight request. The demo may retry with the same key only inside its retry window, relying on the provider to serialize an in-flight duplicate and replay a completed request. An empty lookup alone is never permission to send a new key.

That last condition is real. Stripe retains v1 keys for at least 24 hours and may remove them afterward; reusing a removed key [can execute a new request](https://docs.stripe.com/api/idempotent_requests). Its guidance is to limit retries of an unresolved operation to that window, then stop and reconcile by retrieving the relevant object, checking the dashboard and using webhook events. The demo keeps one hour of margin, and its tests include the unpleasant case: a blind retry with the old key after the window creates a second charge, while reconciliation finds the first.

Stripe also asks integrators to include a local identifier in object metadata so that objects arriving via webhook, including ones created during the provider's own recovery, can be matched to local records. Reconciliation depends on having something to look up by, so choose that reference before the first request, not after the incident.

If there is no record and the window has passed, the demo does not guess. It sets `NEEDS_REVIEW`, because lookups can lag and a wrong automatic retry costs a customer money. What review means is a business decision: a person, a second check after a delay, or a refund path.

## This is not exactly-once delivery

Nothing here makes a message arrive exactly once. Requests can be lost, responses can be lost, and webhooks can be delivered more than once. What the design aims for is a single effect per order: at-least-once attempts combined with an idempotent receiver, with reconciliation covering the gaps. That depends on the provider honouring the key for as long as it remembers it, and on the lookup being trustworthy.

The same discipline applies to your own handlers. The demo records the processed event ID and applies the conditional order transition in the same SQLite transaction. A crash between receipt and state application rolls the transaction back; redelivery can then retry it. The conditional transition to `PAID` also prevents a duplicate webhook from fulfilling an order twice, and a second charge on an already-paid order is flagged and not silently absorbed. If marking an order paid also has to trigger an email or a shipment, write that intent in the same transaction and publish it afterwards. That is the [transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html) pattern, and it is the same lesson applied one step downstream.

## Run the demo

The code is standard-library Python with a simulated provider: no network, no real payment API, no credentials. From the repository root:

```bash
python -m unittest discover -s examples/article-series/timeout-does-not-mean-payment-failed/tests -v
python examples/article-series/timeout-does-not-mean-payment-failed/demo.py
```

In the recorded local run on Windows with Python 3.13, all 21 tests passed in about ten seconds. The slowest part is a real SQLite commit per state change. The demo also runs 500 orders through a deterministic, seeded schedule of lost requests, lost responses and slow providers. In that simulation the naive flow, which treats a timeout as failure and retries with a fresh key, left 182 of the 500 orders charged more than once. The safe flow charged none twice, and all 500 ended `PAID` and matched the provider's records.

Read those numbers as properties of the simulator and its fault menu. They are not failure rates for any real payment system, and the fault mix was chosen to exercise the failure modes.

## What the demo does not cover

There is no webhook endpoint or signature verification in this in-process exercise. A real receiver must authenticate events using its provider's documented mechanism before durable processing.

The SQLite file stands in for durable storage. The demo does not test power loss, replication, concurrent workers or multiple processes, and its provider's lookup is assumed to be immediate and authoritative. It has no backoff or jitter, and refunds, partial captures and chargebacks are out of scope. The `NEEDS_REVIEW` states stand for processes the demo does not automate. If you adapt anything here, test it against your provider's documented behaviour, and read their retention and replay rules for the API version you use.

## A short checklist

- Persist the intent, key and payload before the first attempt.
- Send from storage, and refuse to change the payload after a send.
- Treat a timeout as unknown, not failed.
- Retry with the same key and payload, only while the provider remembers it.
- Reconcile through a lookup you can key on, and plan for duplicate and late webhooks.
- Decide ahead of time what happens when reconciliation cannot decide.

## Further reading

- IETF HTTPAPI working group, [The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/) (Internet-Draft, work in progress).
- Stripe, [Idempotent requests](https://docs.stripe.com/api/idempotent_requests) and [Advanced error handling](https://docs.stripe.com/error-low-level).
- Amazon Builders' Library, [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).
- RFC 9110, [Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods).
- Chris Richardson, [Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html).
