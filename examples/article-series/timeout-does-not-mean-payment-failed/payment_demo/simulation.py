"""Deterministic fault-injection runs used by the tests and by demo.py.

The fault schedule comes from a tiny linear congruential generator so the same seed
gives the same schedule on every Python version. Counts printed from these runs
describe this simulator under these assumptions. They are not failure rates for any
real payment system.
"""
from __future__ import annotations

import os
import tempfile

from .clock import SimClock
from .merchant import Merchant
from .naive import NaiveMerchant
from .provider import SimulatedProvider


class Lcg:
    def __init__(self, seed: int):
        self.state = seed & 0x7FFFFFFF

    def next_int(self, bound: int) -> int:
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return (self.state >> 8) % bound


FAULT_MENU = [
    SimulatedProvider.OK, SimulatedProvider.OK, SimulatedProvider.OK,
    SimulatedProvider.TIMEOUT_BEFORE, SimulatedProvider.TIMEOUT_AFTER, SimulatedProvider.SLOW,
]


def fault_schedule(seed: int, n_orders: int) -> list[list[str]]:
    rng = Lcg(seed)
    schedule = []
    for _ in range(n_orders):
        length = 1 + rng.next_int(3)
        schedule.append([FAULT_MENU[rng.next_int(len(FAULT_MENU))] for _ in range(length)])
    return schedule


def run_naive(seed: int, n_orders: int) -> dict:
    clock = SimClock()
    provider = SimulatedProvider(clock)
    naive = NaiveMerchant(provider)
    for i, faults in enumerate(fault_schedule(seed, n_orders)):
        provider.script_faults(*faults)
        naive.pay(f"order-{i}", 1000 + i)
        provider.settle()
    return summarize(provider, n_orders)


def run_safe(seed: int, n_orders: int, db_dir: str | None = None) -> dict:
    clock = SimClock()
    provider = SimulatedProvider(clock)
    cleanup = None
    if db_dir is None:
        cleanup = tempfile.TemporaryDirectory()
        db_dir = cleanup.name
    merchant = Merchant(os.path.join(db_dir, "orders.sqlite3"), provider, clock)
    try:
        for i, faults in enumerate(fault_schedule(seed, n_orders)):
            order_id = f"order-{i}"
            merchant.create_order(order_id, 1000 + i)
            provider.script_faults(*faults)
            state = merchant.attempt_charge(order_id)
            rounds = 0
            while state == "SENDING" and rounds < 10:
                provider.settle()          # slow requests finish in the background
                clock.advance(60)
                state = merchant.reconcile(order_id)
                rounds += 1
        summary = summarize(provider, n_orders)
        states: dict[str, int] = {}
        for row in merchant.db.execute("SELECT state, COUNT(*) c FROM orders GROUP BY state"):
            states[row["state"]] = row["c"]
        summary["merchant_states"] = states
        summary["merchant_paid_matches_provider"] = all(
            (merchant.get(f"order-{i}")["state"] == "PAID") == bool(provider.find_by_reference(f"order-{i}"))
            for i in range(n_orders))
        return summary
    finally:
        merchant.close()
        if cleanup:
            cleanup.cleanup()


def summarize(provider: SimulatedProvider, n_orders: int) -> dict:
    per_order: dict[str, int] = {}
    for charge in provider.charges.values():
        per_order[charge["reference"]] = per_order.get(charge["reference"], 0) + 1
    return {
        "orders": n_orders,
        "orders_charged": len(per_order),
        "orders_charged_more_than_once": sum(1 for c in per_order.values() if c > 1),
        "total_charges": len(provider.charges),
        "max_charges_for_one_order": max(per_order.values(), default=0),
    }
