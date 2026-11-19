# A timeout does not mean a payment failed: simulated demo

Companion code for the article "A Timeout Does Not Mean a Payment Failed".

Everything here is synthetic. There is no network access, no real payment API, no credentials and no card data. The "provider" is a small in-process simulator written for this exercise. It models behaviour that real processors document (caller-supplied idempotency keys, a payload comparison, a key retention window, at-least-once webhooks) but it is not any vendor's implementation.

## Run it

Standard library only. Run and tested with Python 3.13 on Windows; other versions are untested. From the repository root:

```bash
python -m unittest discover -s examples/article-series/timeout-does-not-mean-payment-failed/tests -v
python examples/article-series/timeout-does-not-mean-payment-failed/demo.py
```

The tests take around ten seconds because they use a real SQLite file with a commit per state change.

Expected: `Ran 21 tests ... OK`, and a demo timeline. In the 500 order run (seed 20261119) the naive flow leaves 182 orders charged more than once, and the safe flow leaves none, with every order ending `PAID` and agreeing with the provider's records.

Those counts describe this simulator and its fault menu. They are not failure rates for any real system.

## What is modelled

| Piece | File | Notes |
| --- | --- | --- |
| Provider simulator | `payment_demo/provider.py` | Idempotency key table, payload fingerprint, 24 hour key retention, in-flight (409 style) conflict, mismatch (422 style) error, lookup by reference, duplicate webhooks. |
| Naive merchant | `payment_demo/naive.py` | Treats a timeout as failure and retries with a fresh key. Present only to be broken. |
| Durable merchant | `payment_demo/merchant.py` | Stores intent, key and payload in SQLite before sending, never fails an order on a timeout, reconciles by asking the provider, dedupes webhooks. |
| Fault schedules | `payment_demo/simulation.py` | Seeded and deterministic. Faults: request lost, response lost, provider still working. |

## What the tests check

- A lost response plus a fresh key charges twice (the bug), while the same key plus reconciliation charges once.
- A timeout leaves the order in `SENDING`, never in a failure state.
- A key reused with a different amount is rejected by the provider, and the merchant refuses to amend an order after a send.
- A restart reuses the stored key, while a `:memory:` store loses it and the retry charges again.
- After the key retention window, a blind retry with the old key charges again, while reconciliation finds the original charge.
- With no record after the window, the demo escalates to `NEEDS_REVIEW` instead of guessing.
- Webhook receipt and the conditional order transition commit together. A crash inside that transaction rolls it back so redelivery after a restart can apply the event. Duplicate deliveries fulfil an order once, and a second charge on a paid order is flagged.
- 500 seeded orders: no order is charged twice by the safe flow under the simulated faults.

## Limits you should keep in mind

- This is not exactly-once delivery. Messages here can be lost, duplicated and delayed. What the design gives is an at-most-one-charge outcome per order, and only because the provider honours the key while it remembers it, and because reconciliation closes the gaps.
- The SQLite file is a stand-in for durable storage. The demo does not test power loss, fsync behaviour, replication, concurrent workers, or multiple processes writing at once.
- The provider's reconciliation lookup is assumed authoritative and immediate. Real lookups and webhooks can lag or arrive out of order.
- The `NEEDS_REVIEW` paths (more than one charge, no record after the window) stand for refund, support or manual processes that this demo deliberately does not automate.
- There is no HTTP webhook endpoint or signature verification; a real receiver must authenticate events before processing them. Retry backoff, jitter, rate limits, partial captures, refunds and chargebacks are out of scope.
