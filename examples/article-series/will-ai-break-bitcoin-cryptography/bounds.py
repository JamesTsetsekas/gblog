"""Arithmetic on the growth terms in the claimed ETH refutation.

The OpenAI manuscript "The Exponential Time Hypothesis is False" (revised
25 October 2026) gives bounds with an exponential factor 2^(O(f(n))),
multiplied by a polynomial in the formula variables and clauses for each
fixed clause width. Here n counts variables and natural logarithms are used:

  general formulas (Theorem 1.1):          f(n) = n * ln ln n / sqrt(ln n)
  formulas with m <= D*n clauses:          f(n) = n / sqrt(ln n)
  bound formalized in Lean (runtimeScale): f(n) = n * (ln ln(n+16))^2 / sqrt(ln(n+16))

Here n counts every variable of the formula, including the auxiliary variables
an encoding introduces. It is not the bit length of a key.

The O(.) hides constants that the theorems do not state. Lean's statement is
existential: some constant A > 0 exists. Everything below therefore treats the
constant A as an unknown and shows what different values would imply. None of
this is a statement about the algorithm's real running time on any input.
The arithmetic compares exponential factors only; it omits the additional
constant and polynomial in the full bound.

Run: python -I bounds.py
"""

from __future__ import annotations

import math


def lean_scale(n: float) -> float:
    """runtimeScale from openai/math lean/ComparatorChallenges/SubexponentialSAT.lean."""
    big_l = math.log(n + 16)
    return n * math.log(big_l) ** 2 / math.sqrt(big_l)


def paper_general_scale(n: float) -> float:
    return n * math.log(math.log(n)) / math.sqrt(math.log(n))


def paper_sparse_scale(n: float) -> float:
    return n / math.sqrt(math.log(n))


def lean_ratio_from_log(big_l: float) -> float:
    """lean_scale(n) / n written in terms of L = ln(n + 16), so huge n is fine."""
    return math.log(big_l) ** 2 / math.sqrt(big_l)


def _bisect(f, lo: float, hi: float, iterations: int = 200) -> float:
    flo = f(lo)
    for _ in range(iterations):
        mid = (lo + hi) / 2
        fmid = f(mid)
        if (fmid < 0) == (flo < 0):
            lo, flo = mid, fmid
        else:
            hi = mid
    return (lo + hi) / 2


def lean_ratio_crossings() -> dict[str, float]:
    """Where lean_scale(n) / n equals 1, i.e. where 2^(lean_scale(n)) meets 2^n.

    With L = ln(n+16), the ratio is (ln L)^2 / sqrt(L). Setting it to 1 gives
    ln L = L^(1/4). Writing u = ln L turns that into u = exp(u / 4), which has
    two positive roots. The ratio peaks at L = e^4 with value 16 / e^2.
    """

    def g(u: float) -> float:
        return u - math.exp(u / 4)

    u_low = _bisect(g, 1.0, 2.0)
    u_high = _bisect(g, 8.0, 9.0)
    l_low, l_high = math.exp(u_low), math.exp(u_high)
    return {
        "n_low": math.exp(l_low) - 16,
        "log10_n_high": l_high / math.log(10),  # n + 16 = e^L; the 16 is negligible here
        "peak_ratio": lean_ratio_from_log(math.exp(4)),
        "peak_log_n_plus_16": math.exp(4),
    }


def constant_needed(scale: float, target_bits: float = 128.0) -> float:
    """Largest A with A * scale <= target_bits, ignoring polynomial factors."""
    return target_bits / scale


def table(ns=(10_000, 1_000_000, 100_000_000)) -> list[dict[str, float]]:
    rows = []
    for n in ns:
        sparse = paper_sparse_scale(n)
        rows.append(
            {
                "n": n,
                "lean_scale": lean_scale(n),
                "paper_general_scale": paper_general_scale(n),
                "paper_sparse_scale": sparse,
                "A_needed_sparse_128": constant_needed(sparse),
            }
        )
    return rows


def main() -> None:
    c = lean_ratio_crossings()
    print("Exponential factor only, A = 1, compared with 2^n:")
    print(f"  exceeds 2^n from n = {c['n_low']:.6f}")
    print(f"  until n is about 10^{c['log10_n_high']:.2f}")
    print(f"  peak ratio {c['peak_ratio']:.6f} (16/e^2 = {16 / math.e ** 2:.6f})")
    print()
    print("Growth terms f(n) in bits (multiply by the unknown constant A):")
    print(f"{'n':>12} {'lean':>14} {'paper general':>14} {'paper sparse':>14} {'A for <=128 (sparse)':>22}")
    for row in table():
        print(
            f"{row['n']:>12,} {row['lean_scale']:>14,.1f} {row['paper_general_scale']:>14,.1f} "
            f"{row['paper_sparse_scale']:>14,.1f} {row['A_needed_sparse_128']:>22.3g}"
        )


if __name__ == "__main__":
    main()
