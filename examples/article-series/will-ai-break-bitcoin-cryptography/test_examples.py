"""Deterministic checks for the Bitcoin cryptography article examples.

Run from the repository root:
    python -I -m unittest discover -s examples/article-series/will-ai-break-bitcoin-cryptography -v
"""

import hashlib
import math
import unittest

import bounds
import toy_ecdsa as ec


class CurveParameters(unittest.TestCase):
    def test_generator_is_on_curve_and_has_order_n(self):
        self.assertTrue(ec.is_on_curve(ec.G))
        self.assertIsNone(ec.scalar_mult(ec.N))
        self.assertEqual(ec.scalar_mult(ec.N - 1), (ec.GX, ec.P - ec.GY))

    def test_bip340_public_key_vectors(self):
        # x-only public keys from bitcoin/bips bip-0340/test-vectors.csv, rows 0 and 1.
        vectors = {
            0x3: 0xF9308A019258C31049344F85F89D5229B531C845836F99B08601F113BCE036F9,
            0xB7E151628AED2A6ABF7158809CF4F3C762E7160F38B4DA56A784D9045190CFEF:
                0xDFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659,
        }
        for secret, x_only in vectors.items():
            self.assertEqual(ec.scalar_mult(secret)[0], x_only)


class NonceReuse(unittest.TestCase):
    def setUp(self):
        # A throwaway teaching key derived from a fixed label. It protects nothing.
        self.d = int.from_bytes(hashlib.sha256(b"throwaway teaching key").digest(), "big") % ec.N
        self.pub = ec.scalar_mult(self.d)
        self.m1 = b"pay 1000 sats to alice"
        self.m2 = b"pay 2000 sats to bob"

    def test_signatures_verify_and_tampering_fails(self):
        sig = ec.sign(self.d, self.m1, nonce=0x1234567)
        self.assertTrue(ec.verify(self.pub, self.m1, sig))
        self.assertFalse(ec.verify(self.pub, self.m2, sig))

    def test_reused_nonce_reveals_private_key(self):
        k = int.from_bytes(hashlib.sha256(b"the same nonce, twice").digest(), "big") % ec.N
        sig1 = ec.sign(self.d, self.m1, nonce=k)
        sig2 = ec.sign(self.d, self.m2, nonce=k)
        self.assertTrue(ec.verify(self.pub, self.m1, sig1))
        self.assertTrue(ec.verify(self.pub, self.m2, sig2))
        recovered = ec.recover_key_from_reused_nonce(self.m1, sig1, self.m2, sig2)
        self.assertEqual(recovered, self.d)
        self.assertEqual(ec.scalar_mult(recovered), self.pub)

    def test_distinct_nonces_do_not_fit_the_formula(self):
        sig1 = ec.sign(self.d, self.m1, nonce=0xA1)
        sig2 = ec.sign(self.d, self.m2, nonce=0xB2)
        with self.assertRaises(ValueError):
            ec.recover_key_from_reused_nonce(self.m1, sig1, self.m2, sig2)


class AsymptoticBounds(unittest.TestCase):
    def test_crossings_of_lean_bound_with_brute_force(self):
        c = bounds.lean_ratio_crossings()
        self.assertAlmostEqual(c["n_low"], 49.1751, places=3)
        self.assertAlmostEqual(c["log10_n_high"], 2390.21, places=2)
        self.assertAlmostEqual(c["peak_ratio"], 16 / math.e ** 2, places=12)

    def test_lean_bound_with_unit_constant_is_above_n_between_the_crossings(self):
        for n in (50, 10_000, 1_000_000):
            self.assertGreater(bounds.lean_scale(n), n)
        self.assertLess(bounds.lean_scale(49), 49)

    def test_growth_terms_are_eventually_smaller_than_n(self):
        # Asymptotically every term is o(n); at n = 10^8 the sparse term is
        # already about a quarter of n, while the Lean term is still above n.
        n = 100_000_000
        self.assertLess(bounds.paper_sparse_scale(n), 0.25 * n)
        self.assertGreater(bounds.lean_scale(n), n)

    def test_constant_needed_for_128_bits_at_one_million_variables(self):
        need = bounds.constant_needed(bounds.paper_sparse_scale(1_000_000))
        self.assertLess(need, 5e-4)
        self.assertGreater(need, 4e-4)


if __name__ == "__main__":
    unittest.main()
