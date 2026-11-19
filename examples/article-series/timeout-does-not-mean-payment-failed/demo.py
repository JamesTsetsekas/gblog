"""Print a readable timeline for the scenarios in the article.

Run from this directory:  python demo.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from payment_demo.clock import SimClock
from payment_demo.merchant import Merchant
from payment_demo.naive import NaiveMerchant
from payment_demo.provider import SimulatedProvider
from payment_demo.simulation import run_naive, run_safe


def scenario_naive():
    print("1. Naive retry: the response is lost after the charge, the client retries with a new key")
    clock = SimClock()
    provider = SimulatedProvider(clock)
    provider.script_faults("timeout_after")
    result = NaiveMerchant(provider).pay("order-1", 4999)
    print(f"   client sees: {result!r}; provider holds {len(provider.charges)} charge(s) for order-1")


def scenario_safe():
    print("2. Durable intent + same key: same lost response, one charge")
    with tempfile.TemporaryDirectory() as tmp:
        clock = SimClock()
        provider = SimulatedProvider(clock)
        merchant = Merchant(os.path.join(tmp, "orders.sqlite3"), provider, clock)
        merchant.create_order("order-1", 4999)
        provider.script_faults("timeout_after")
        print(f"   first attempt  -> {merchant.attempt_charge('order-1')} (unknown, not failed)")
        print(f"   reconcile      -> {merchant.reconcile('order-1')}")
        print(f"   provider holds {len(provider.charges)} charge(s); fulfilled={merchant.get('order-1')['fulfilled']}")
        merchant.close()


def scenario_expired():
    print("3. Retention window passed: retrying the old key would charge again, reconcile instead")
    with tempfile.TemporaryDirectory() as tmp:
        clock = SimClock()
        provider = SimulatedProvider(clock)
        merchant = Merchant(os.path.join(tmp, "orders.sqlite3"), provider, clock)
        merchant.create_order("order-1", 4999)
        provider.script_faults("timeout_after")
        merchant.attempt_charge("order-1")
        clock.advance(25 * 3600)
        order = merchant.get("order-1")
        provider.create_charge(order["idempotency_key"], 4999, "USD", "order-1")
        print(f"   blind retry with the old key after 25h -> provider now holds {len(provider.charges)} charges")
        merchant.close()


def scenarios_random():
    print("4. 500 orders, deterministic fault schedule (seed 20261119)")
    print("   naive:", run_naive(20261119, 500))
    print("   safe: ", run_safe(20261119, 500))
    print("   (counts describe this simulator only, not real payment systems)")


if __name__ == "__main__":
    scenario_naive()
    scenario_safe()
    scenario_expired()
    scenarios_random()
