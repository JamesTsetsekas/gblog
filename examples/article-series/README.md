# Article companion examples

These examples accompany the November 2026 articles about software correctness, security, and reliability. They use synthetic inputs and local resources. They do not contact payment processors, scan networks, or require credentials.

Run the commands below from the repository root. The examples were checked on Windows with Python 3.13.1. Each directory documents its input contract, expected behavior, and limitations.

| Example | What to inspect |
| --- | --- |
| [Timestamp window counts](ai-optimization-without-breaking-correctness/) | A clear scan oracle, an indexed alternative, a rejected boundary condition, and a benchmark that includes sorting cost. |
| [Security report triage](triaging-an-ai-security-report/) | A deliberately flawed toy library, claim reproduction, a limited reachability heuristic, a patch, and regression checks. |
| [Patch deployment](the-patch-is-out-users-still-vulnerable/) | An invented fleet that distinguishes successful deployment jobs from observed protection, with a canary, rollback, and interim mitigation. |
| [Payment recovery](timeout-does-not-mean-payment-failed/) | A simulated provider, SQLite-backed intent, idempotency keys, lost responses, reconciliation, and duplicate events. |
| [Executable specifications](passing-tests-is-not-a-proof/) | A payout invariant, bounded exhaustive checks, surviving mutants, and a vacuous property. |
| [Cryptographic claims](will-ai-break-bitcoin-cryptography/) | Throwaway-key nonce reuse and arithmetic on asymptotic bounds, with no claims of a practical cryptanalytic attack. |
| [Cryptographic inventory](post-quantum-migration-starts-with-an-inventory/) | Discovery, human annotations, and scenario-based ranking for a fictional application. |

```sh
python -B -m unittest discover -s examples/article-series/ai-optimization-without-breaking-correctness -v
python -B -m unittest discover -s examples/article-series/triaging-an-ai-security-report/tests -v
python -B -m unittest discover -s examples/article-series/the-patch-is-out-users-still-vulnerable/tests -v
python -B -m unittest discover -s examples/article-series/timeout-does-not-mean-payment-failed/tests -v
node --test examples/article-series/passing-tests-is-not-a-proof/split.test.js
python -I -B -m unittest discover -s examples/article-series/will-ai-break-bitcoin-cryptography -v
node --test examples/article-series/post-quantum-migration-starts-with-an-inventory/inventory.test.js
```

The timing experiment is a measurement of a small operation on synthetic data, not a production performance estimate or a measurement of AI productivity. Its optional plotting script requires matplotlib; the experiment itself uses only the Python standard library.

The triage example intentionally contains vulnerable behavior inside its temporary test directory. Its patched implementation and reachability checks are teaching examples with documented limits, not a general file-serving security boundary. The payment provider is also a model of selected behaviors, not an implementation of a real processor's contract.
