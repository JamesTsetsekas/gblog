"""Textbook ECDSA over secp256k1, for teaching only.

This is NOT a wallet library. It is slow, it is not constant time, it does not
normalize signatures to Bitcoin's low-s form, and it lets the caller choose the
nonce so that the nonce-reuse failure can be demonstrated. Never use it with a
key that protects anything.

Curve parameters are from SEC 2 v2, section 2.4.1 (https://www.secg.org/sec2-v2.pdf).
"""

from __future__ import annotations

import hashlib

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
A = 0
B = 7
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (GX, GY)

Point = tuple[int, int] | None  # None is the point at infinity


def is_on_curve(pt: Point) -> bool:
    if pt is None:
        return True
    x, y = pt
    return (y * y - (x * x * x + A * x + B)) % P == 0


def point_add(p1: Point, p2: Point) -> Point:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        lam = (3 * x1 * x1 + A) * pow(2 * y1, -1, P) % P
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def scalar_mult(k: int, pt: Point = G) -> Point:
    result: Point = None
    addend = pt
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


def message_hash(message: bytes) -> int:
    return int.from_bytes(hashlib.sha256(message).digest(), "big")


def sign(private_key: int, message: bytes, nonce: int) -> tuple[int, int]:
    """Textbook ECDSA signing with a caller-supplied nonce (for demonstration)."""
    if not 1 <= private_key < N or not 1 <= nonce < N:
        raise ValueError("private key and nonce must be in [1, n-1]")
    z = message_hash(message)
    r = scalar_mult(nonce)[0] % N
    s = pow(nonce, -1, N) * (z + r * private_key) % N
    if r == 0 or s == 0:
        raise ValueError("degenerate signature; choose another nonce")
    return r, s


def verify(public_key: Point, message: bytes, signature: tuple[int, int]) -> bool:
    r, s = signature
    if not (1 <= r < N and 1 <= s < N):
        return False
    z = message_hash(message)
    w = pow(s, -1, N)
    pt = point_add(scalar_mult(z * w % N), scalar_mult(r * w % N, public_key))
    return pt is not None and pt[0] % N == r


def recover_key_from_reused_nonce(
    message1: bytes, sig1: tuple[int, int], message2: bytes, sig2: tuple[int, int]
) -> int:
    """Recover the private key from two signatures that share a nonce.

    s1 = k^-1 (z1 + r d) and s2 = k^-1 (z2 + r d) with the same k and r give
    k = (z1 - z2) / (s1 - s2) and d = (s1 k - z1) / r, all modulo n.
    No discrete logarithm is computed: the failure is in how the signer chose k.
    """
    r1, s1 = sig1
    r2, s2 = sig2
    if r1 != r2:
        raise ValueError("signatures do not share a nonce (r values differ)")
    z1, z2 = message_hash(message1), message_hash(message2)
    k = (z1 - z2) * pow(s1 - s2, -1, N) % N
    return (s1 * k - z1) * pow(r1, -1, N) % N
