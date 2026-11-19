# Passing tests is not a proof: a tiny invariant example

Companion code for the article "Passing Tests Is Not a Proof: What AI Verification Means for Developers."

The function under test splits an integer amount (think satoshis) across recipients in proportion to positive integer weights. The point is not the function. The point is the difference between three kinds of evidence:

1. **Example tests**: a handful of hand-picked inputs.
2. **A bounded exhaustive check**: every input in a small, explicitly defined domain.
3. **A specification**: the properties every output must satisfy, which can itself be too weak.

## Run it

From the repository root, with Node.js 20 or newer and no installs:

```bash
node --test examples/article-series/passing-tests-is-not-a-proof/split.test.js
```

Expected result: `# tests 13`, `# pass 13`, `# fail 0`. Recorded on Node v22.12.0 (Windows 11). Every check is deterministic.

## What the tests show

| Check | Result |
| --- | --- |
| Three example tests | Pass for both the rounded draft and the largest-remainder version |
| Bounded exhaustive check (15,738 inputs: totals 0 to 60, one to three weights from 1 to 6) | Rounded draft fails first at `total = 1, weights = [1, 1]`, returning `[1, 1]`: one unit created from nothing |
| A realistic failure | Splitting 100 three ways with the draft returns `[33, 33, 33]`: one unit lost |
| Largest-remainder version on the same domain | No counterexample to the strong specification or the apportionment rule |
| Weak specification ("right length, no part exceeds the total") | Accepts the broken draft and all four mutants |
| Strong specification (shape, non-negative integers, conservation, proportionality) | Rejects three of four mutants |
| Surviving mutant | Caught only after adding an explicit largest-remainder rule |
| Property behind an impossible guard | Accepts a function that always returns `[999]`; a witness count of zero exposes it |

## Assumptions and limits

- The bounded check covers only the stated domain. It is evidence about those 15,738 inputs, not a proof for all integers. A proof would quantify over every total and every weight vector, and would still be only as good as the specification it proves.
- The "Bitcoin-scale" test checks three extra inputs near 2.1 quadrillion units. It is a spot check, not coverage.
- Whether the surviving mutant is a bug depends on the requirement. If any floor-or-ceiling split is acceptable, it is correct. If the business rule is "largest remainder wins", it is wrong. The specification has to say which.
- The specification functions use `BigInt` so the checker is not fooled by floating-point rounding. The implementations accept only safe integers.
- Nothing here was formally verified. No proof assistant is involved.

## Files

- `split.js`: the rounded draft, the largest-remainder version and four deliberately broken mutants.
- `spec.js`: properties, a weak specification, a vacuous property, the bounded domain enumerator and the checker.
- `split.test.js`: the tests above, using Node's built-in test runner.
