# A toy cryptographic inventory and migration ranking

Companion code for the article "Post-Quantum Migration Starts With an Inventory."

The fixture under `fixtures/sample-app/` is a fictional application. It is not code from any real system. The pipeline has three steps, and the split between them is the point:

1. **Discovery** (`scanDirectory`): find cryptographic calls in source and one config shape. Automated, cheap, incomplete.
2. **Annotation** (`annotations.json`): a human records each use's owner, purpose, how long its data or signatures must stay trustworthy, how long migration would take and who controls the change. A scanner cannot know these.
3. **Ranking** (`prioritize`): combine both under an assumed number of years until a cryptographically relevant quantum computer. That number is an input you choose, not a forecast.

## Run it

From the repository root, with Node.js 20 or newer and no installs:

```bash
node --test examples/article-series/post-quantum-migration-starts-with-an-inventory/inventory.test.js
node examples/article-series/post-quantum-migration-starts-with-an-inventory/run.js 10
```

Expected: `# tests 13`, `# pass 13`, `# fail 0`. Recorded on Node v22.12.0 (Windows 11). The second command prints a Markdown table. Try `5` and `15` as the argument to see the ranking move.

## Output with an assumed 10-year scenario

| Priority | Location | Primitive | Owner |
| --- | --- | --- | --- |
| P1: harvest now, decrypt later | src/backup.js:11 | RSA public-key encryption | platform team |
| P2: long-lived signatures | src/release.js:5 | ed25519 | device team |
| Review: no owner annotation | src/partner.js:6 | ECDH prime256v1 | (none) |
| Review: algorithm unknown | src/plugins.js:5 | unknown (non-literal algorithm) | platform team |
| P3: schedule with normal upgrades | config/tls.json:1 | TLS groups: X25519, P-256 | infrastructure team |
| P3: schedule with normal upgrades | src/auth.js:5 | RSA-SHA256 | identity team |
| Keep: symmetric, 128-bit or stronger | src/backup.js:9 | aes-256-gcm | platform team |
| Keep: symmetric, 128-bit or stronger | src/webhooks.js:6 | HMAC-sha256 | integrations team |
| Document: not a security control | src/cache.js:5 | md5 | web team |

With `5`, the TLS row moves to P1 because five years of confidentiality plus one year of vendor migration exceeds the scenario. With `15`, nothing is P1 or P2, but the two review rows stay put: an unknown is never ranked as safe.

## The ranking rule

A quantum-vulnerable use is urgent when the time its protection must last, plus the time needed to migrate it, exceeds the assumed scenario:

- confidentiality uses: `confidentialityYears + migrationYears > scenarioYears` gives P1;
- signatures: `signatureTrustYears + migrationYears > scenarioYears` gives P2; authentication also includes the issuer key lifetime. A classical-verification retirement date beyond the scenario is P2 as well;
- a recognized quantum-vulnerable use with complete required annotations that falls below those urgency thresholds is P3; missing purpose, relevant lifetimes or retirement policy gives Review.

Symmetric primitives at 128 bits or more are kept, following NIST IR 8547's statement that approved symmetric primitives with at least 128 bits of classical security are believed to meet at least security Category 1. MD5 and SHA-1 are flagged as classically weak unless an owner records that the use is not a security control.

This rule is a simplification for teaching. A real program would also weigh exposure, data volume, regulatory deadlines and dependencies between systems.

## Known blind spots (tested)

- `src/storage.js` calls a third-party SDK that encrypts internally. The scanner sees nothing. Dependencies and services need an SBOM review and vendor questions.
- `src/release.js` signs with the one-shot `sign(null, ...)` API. Only the key generation on line 5 is detected.
- `src/plugins.js` picks its algorithm from configuration. The scanner reports it as unknown rather than skipping it.
- Anything not written as Node `crypto` calls with literal algorithm names, or not in the one JSON shape it reads, is invisible: TLS settings in a load balancer console, HSM policies, certificates, database encryption, protocol libraries in other languages.

## Notes

- Node v22.12.0, used here, does not expose ML-KEM. Node's documentation lists ML-KEM key support from v24.7.0 and ML-DSA from v24.6.0 when built with OpenSSL 3.5 or newer. The example does not need either.
- The record fields are loosely inspired by cryptographic bill of materials ideas (algorithm, location, purpose, owner). They are not a CycloneDX CBOM document and make no conformance claim.

The token example assumes one-year issuer-key retirement and verifier-policy migration; the fifteen-minute token lifetime is not its protection against forged new tokens. Every use requires an owner. The recognized quantum-vulnerable branches additionally require a purpose, migration duration, and the relevant confidentiality or signature lifetime; signing uses require classical-verification retirement, and authentication also requires issuer key lifetime. Missing fields in those branches give Review. Recognized symmetric primitives are classified Keep after the owner check without lifetime fields; that classification concerns the primitive, not an audit of its implementation. TLS groups in configuration are advertised capabilities, not observed negotiation: even a hybrid-only list stays in review until the protocol, fallback and negotiated behavior are examined.

The backup action calls for a supported PQ envelope or reviewed hybrid profile, never two independently usable RSA/PQ wrappers for the same data key. Firmware cohorts need a rollback-resistant acceptance policy that requires both signatures during the hybrid phase, not either signature. These are migration requirements to investigate, not cryptographic implementations supplied by this example.
