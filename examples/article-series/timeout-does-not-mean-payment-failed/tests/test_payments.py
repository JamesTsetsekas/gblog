import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from payment_demo.clock import SimClock
from payment_demo.merchant import Merchant, SimulatedCrash
from payment_demo.naive import NaiveMerchant
from payment_demo.provider import (IdempotencyMismatch, ProviderConflict, ProviderTimeout,
                                   SimulatedProvider)
from payment_demo.simulation import fault_schedule, run_naive, run_safe


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = os.path.join(self._tmp.name, "orders.sqlite3")
        self.clock = SimClock()
        self.provider = SimulatedProvider(self.clock)
        self.merchant = self.open_merchant()

    def open_merchant(self):
        m = Merchant(self.db_path, self.provider, self.clock)
        self.addCleanup(m.close)  # runs before the temp directory is removed
        return m


class NaiveRetryTests(Base):
    def test_lost_response_with_fresh_key_charges_twice(self):
        self.provider.script_faults("timeout_after", "ok")
        NaiveMerchant(self.provider).pay("order-1", 4999)
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 2)


class IdempotentRetryTests(Base):
    def test_lost_response_is_unknown_then_reconciled_to_one_charge(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_after")
        self.assertEqual(self.merchant.attempt_charge("order-1"), "SENDING")
        self.assertEqual(self.merchant.reconcile("order-1"), "PAID")
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 1)
        self.assertEqual(self.merchant.get("order-1")["fulfilled"], 1)

    def test_request_lost_before_provider_is_retried_with_same_key_once(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_before")
        key = self.merchant.get("order-1")["idempotency_key"]
        self.assertEqual(self.merchant.attempt_charge("order-1"), "SENDING")
        self.assertEqual(self.provider.find_by_reference("order-1"), [])
        self.assertEqual(self.merchant.reconcile("order-1"), "PAID")
        self.assertEqual(self.merchant.get("order-1")["idempotency_key"], key)
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 1)

    def test_timeout_never_becomes_a_failure_state(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_before")
        self.merchant.attempt_charge("order-1")
        self.assertEqual(self.merchant.get("order-1")["state"], "SENDING")

    def test_slow_request_conflicts_then_replays(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("slow")
        self.assertEqual(self.merchant.attempt_charge("order-1"), "SENDING")
        # Still executing at the provider: a same-key retry is rejected, not duplicated.
        key = self.merchant.get("order-1")["idempotency_key"]
        with self.assertRaises(ProviderConflict):
            self.provider.create_charge(key, 4999, "USD", "order-1")
        self.provider.settle()
        self.assertEqual(self.merchant.reconcile("order-1"), "PAID")
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 1)

    def test_definite_decline_is_final_and_replayed(self):
        self.provider.decline_reference("order-1")
        self.merchant.create_order("order-1", 4999)
        self.assertEqual(self.merchant.attempt_charge("order-1"), "DECLINED")
        self.assertEqual(self.provider.find_by_reference("order-1"), [])
        self.assertEqual(self.merchant.attempt_charge("order-1"), "DECLINED")


class PayloadBindingTests(Base):
    def test_provider_rejects_same_key_with_different_amount(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_after")
        self.merchant.attempt_charge("order-1")
        key = self.merchant.get("order-1")["idempotency_key"]
        with self.assertRaises(IdempotencyMismatch):
            self.provider.create_charge(key, 5999, "USD", "order-1")
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 1)

    def test_amount_cannot_be_amended_after_a_send(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_after")
        self.merchant.attempt_charge("order-1")
        with self.assertRaises(ValueError):
            self.merchant.amend_amount("order-1", 5999)

    def test_amend_before_any_send_rotates_key_and_charges_new_amount(self):
        self.merchant.create_order("order-1", 4999)
        old_key = self.merchant.get("order-1")["idempotency_key"]
        self.merchant.amend_amount("order-1", 5999)
        self.assertNotEqual(self.merchant.get("order-1")["idempotency_key"], old_key)
        self.merchant.attempt_charge("order-1")
        self.assertEqual(self.provider.find_by_reference("order-1")[0]["amount_minor"], 5999)


class DurabilityTests(Base):
    def test_restart_after_crash_reuses_the_stored_key(self):
        self.merchant.create_order("order-1", 4999)
        self.merchant.crash_after_provider_call = True
        with self.assertRaises(SimulatedCrash):
            self.merchant.attempt_charge("order-1")
        key = self.merchant.get("order-1")["idempotency_key"]
        self.merchant.close()
        # "Restart": a new process opens the same file.
        restarted = Merchant(self.db_path, self.provider, self.clock)
        self.addCleanup(restarted.close)
        self.assertEqual(restarted.get("order-1")["state"], "SENDING")
        self.assertEqual(restarted.get("order-1")["idempotency_key"], key)
        self.assertEqual(restarted.reconcile("order-1"), "PAID")
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 1)

    def test_in_memory_state_is_lost_on_restart_and_the_retry_can_double_charge(self):
        volatile = Merchant(":memory:", self.provider, self.clock)
        volatile.create_order("order-1", 4999)
        volatile.crash_after_provider_call = True
        with self.assertRaises(SimulatedCrash):
            volatile.attempt_charge("order-1")
        volatile.close()
        # The restarted process has no memory of the order, the key or the attempt.
        restarted = Merchant(":memory:", self.provider, self.clock)
        self.addCleanup(restarted.close)
        self.assertIsNone(restarted.get("order-1"))
        restarted.create_order("order-1", 4999)       # the checkout page is retried
        restarted.attempt_charge("order-1")           # new random key
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 2)


class RetentionWindowTests(Base):
    def test_direct_merchant_retry_after_expiry_reconciles_before_sending(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_after")
        self.merchant.attempt_charge("order-1")
        self.clock.advance(25 * 3600)
        requests_before = self.provider.requests_seen
        self.assertEqual(self.merchant.attempt_charge("order-1"), "PAID")
        self.assertEqual(self.provider.requests_seen, requests_before)
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 1)

    def test_blind_retry_after_key_expiry_double_charges(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_after")
        self.merchant.attempt_charge("order-1")
        key = self.merchant.get("order-1")["idempotency_key"]
        self.clock.advance(25 * 3600)
        self.provider.create_charge(key, 4999, "USD", "order-1")  # key was pruned
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 2)

    def test_reconcile_after_window_finds_the_charge_instead_of_retrying(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_after")
        self.merchant.attempt_charge("order-1")
        self.clock.advance(25 * 3600)
        self.assertEqual(self.merchant.reconcile("order-1"), "PAID")
        self.assertEqual(len(self.provider.find_by_reference("order-1")), 1)

    def test_no_record_after_window_escalates_instead_of_guessing(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_before")
        self.merchant.attempt_charge("order-1")
        self.clock.advance(25 * 3600)
        self.assertEqual(self.merchant.reconcile("order-1"), "NEEDS_REVIEW")
        self.assertEqual(self.provider.find_by_reference("order-1"), [])


class WebhookTests(Base):
    def test_crash_during_inbox_transaction_is_recoverable_after_restart(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_after")
        self.merchant.attempt_charge("order-1")
        event = self.provider.drain_events()[0]
        self.merchant.crash_after_event_record = True
        with self.assertRaises(SimulatedCrash):
            self.merchant.handle_webhook(event)
        self.assertEqual(self.merchant.get("order-1")["state"], "SENDING")
        self.assertEqual(self.merchant.db.execute("SELECT COUNT(*) FROM processed_events").fetchone()[0], 0)
        self.merchant.close()
        restarted = Merchant(self.db_path, self.provider, self.clock)
        self.addCleanup(restarted.close)
        restarted.handle_webhook(event)
        restarted.handle_webhook(event)
        self.assertEqual(restarted.get("order-1")["state"], "PAID")
        self.assertEqual(restarted.get("order-1")["fulfilled"], 1)
        self.assertEqual(restarted.db.execute("SELECT COUNT(*) FROM processed_events").fetchone()[0], 1)

    def test_duplicate_webhook_does_not_double_fulfil(self):
        self.merchant.create_order("order-1", 4999)
        self.provider.script_faults("timeout_after")
        self.merchant.attempt_charge("order-1")
        for event in self.provider.drain_events(duplicate=True):
            self.merchant.handle_webhook(event)
        self.assertEqual(self.merchant.get("order-1")["state"], "PAID")
        self.assertEqual(self.merchant.get("order-1")["fulfilled"], 1)
        self.assertEqual(self.merchant.db.execute("SELECT COUNT(*) FROM processed_events").fetchone()[0], 1)

    def test_second_charge_for_a_paid_order_is_flagged_not_hidden(self):
        self.merchant.create_order("order-1", 4999)
        self.merchant.attempt_charge("order-1")
        self.merchant.handle_webhook({"event_id": "evt_x", "type": "charge.succeeded",
                                      "charge_id": "ch_9999", "reference": "order-1"})
        self.assertEqual(self.merchant.get("order-1")["state"], "NEEDS_REVIEW")


class SimulationInvariantTests(unittest.TestCase):
    N = 500
    SEED = 20261119

    def test_schedule_is_deterministic(self):
        self.assertEqual(fault_schedule(self.SEED, 20), fault_schedule(self.SEED, 20))

    def test_safe_flow_never_charges_an_order_twice_under_the_simulated_faults(self):
        summary = run_safe(self.SEED, self.N)
        self.assertEqual(summary["orders_charged_more_than_once"], 0)
        self.assertEqual(summary["max_charges_for_one_order"], 1)
        self.assertTrue(summary["merchant_paid_matches_provider"])
        self.assertNotIn("SENDING", summary["merchant_states"])

    def test_naive_flow_double_charges_in_the_same_schedule(self):
        summary = run_naive(self.SEED, self.N)
        self.assertGreater(summary["orders_charged_more_than_once"], 0)


if __name__ == "__main__":
    unittest.main()
