# Will AI break Bitcoin's cryptography? Two small checks

Companion code for the article "Will AI Break Bitcoin's Cryptography? How to Read the Claim."

Two separate, local, deterministic demonstrations:

1. **`toy_ecdsa.py`**: textbook ECDSA on the real secp256k1 parameters, used to show that reusing a signing nonce reveals the private key with a few lines of modular arithmetic. No discrete logarithm is computed and nothing about the curve is "broken". The failure is in how the signer chose the nonce.
2. **`bounds.py`**: arithmetic on the growth terms stated in the claimed refutation of the Exponential Time Hypothesis (ETH), showing why an asymptotic bound with an unstated constant says nothing about any particular input size.

## Run it

From the repository root, with Python 3.10 or newer and only the standard library:

```bash
python -I -m unittest discover -s examples/article-series/will-ai-break-bitcoin-cryptography -v
python -I examples/article-series/will-ai-break-bitcoin-cryptography/bounds.py
```

Expected: `Ran 9 tests ... OK`. Recorded with Python 3.13.1 on Windows 11. The second command prints:

```text
Exponential factor only, A = 1, compared with 2^n:
  exceeds 2^n from n = 49.175096
  until n is about 10^2390.21
  peak ratio 2.165365 (16/e^2 = 2.165365)

Growth terms f(n) in bits (multiply by the unknown constant A):
           n           lean  paper general   paper sparse   A for <=128 (sparse)
      10,000       16,245.2        7,316.1        3,295.1                 0.0388
   1,000,000    1,854,971.6      706,442.5      269,039.8               0.000476
 100,000,000  197,774,116.2   67,882,574.8   23,299,530.1               5.49e-06
```

## What the checks establish

- The curve constants match SEC 2 v2 section 2.4.1: the generator is on the curve and `n * G` is the point at infinity.
- Scalar multiplication reproduces the x-only public keys in rows 0 and 1 of BIP 340's published test vectors.
- Two signatures made with the same nonce let `recover_key_from_reused_nonce` return the exact private key. Two signatures with different nonces do not fit the formula.
- For the exponent growth term formalized in Lean, `f(n) = n (ln ln(n+16))^2 / sqrt(ln(n+16))`, the ratio `f(n) / n` peaks at `16/e^2` and equals 1 at `n ≈ 49.175` and again near `n ≈ 10^2390.21`. These values independently reproduce an arithmetic note posted to the community ETH discussion blog. With a coefficient of 1, this exponential factor sits above `2^n` across that range. A sufficiently small coefficient changes the crossings. The theorem does not specify the coefficient, and the full bound also contains an additional multiplier and a polynomial.
- The sparse-formula term `n / sqrt(ln n)` shows how small the constant would have to be before that exponent alone fell below 128, for a few hypothetical formula sizes. This does not bound a complete attack cost.

## Assumptions and limits

- `n` is the number of variables in a CNF formula, including every auxiliary variable an encoding adds. It is not the 256-bit key length. One schoolbook 256-by-256-bit multiplier has 65,536 partial-product AND gates. That illustrates one circuit construction; it establishes neither a minimum SAT variable count nor the number of field multiplications required by every scalar-multiplication implementation. The table's sizes are assumptions chosen for illustration, not measured encodings.
- The table ignores the polynomial factor in front of the exponential and treats the hidden constant as a free parameter. It compares bounds, not running times. An algorithm can run faster than its proven bound.
- `toy_ecdsa.py` is slow, not constant time, skips Bitcoin's low-s rule and lets the caller choose the nonce. It exists to demonstrate a failure. Do not reuse it.
- The private key in the tests is derived from a fixed label and protects nothing.

## Files

- `toy_ecdsa.py`: curve arithmetic, textbook ECDSA, nonce-reuse key recovery.
- `bounds.py`: growth terms, crossing points, the illustrative table.
- `test_examples.py`: the nine checks.

The crossing calculations omit the full theorem's additional constant and polynomial in encoded input length. They compare growth expressions, not measured runtime or a minimum attack cost. SAT bit operations and elliptic-curve group operations have different costs.
