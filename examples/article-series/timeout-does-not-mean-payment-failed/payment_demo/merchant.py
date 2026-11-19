"""Merchant side order handling with durable intent and reconciliation.

State lives in SQLite. Pass a file path for state that survives a process restart;
":memory:" is accepted so the tests can show what is lost when you do not persist.
Even a file database is only as durable as your filesystem and commit settings,
and this demo does not test power loss.

Order states:
  CREATED       intent stored, nothing sent yet
  SENDING       a request may have reached the provider; the outcome is UNKNOWN
  PAID          provider confirmed one charge
  DECLINED      provider definitively refused (a real, final answer)
  NEEDS_REVIEW  the demo cannot safely decide; a person or a richer policy must
A timeout never moves an order to a failure state.
"""
from __future__ import annotations

import sqlite3
import uuid

from .clock import SimClock
from .provider import (IdempotencyMismatch, ProviderConflict, ProviderTimeout,
                       SimulatedProvider, fingerprint)


class SimulatedCrash(BaseException):
    """Raised by a test hook to model the process dying at a precise point."""


SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
  order_id TEXT PRIMARY KEY,
  amount_minor INTEGER NOT NULL,
  currency TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  state TEXT NOT NULL,
  charge_id TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  first_sent_at INTEGER,
  fulfilled INTEGER NOT NULL DEFAULT 0,
  note TEXT
);
CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT PRIMARY KEY);
"""


class Merchant:
    # Retry with the same key only while the provider is still expected to remember it.
    # One hour of margin under the simulated 24 hour retention window.
    RETRY_WINDOW_SECONDS = 23 * 3600

    def __init__(self, db_path: str, provider: SimulatedProvider, clock: SimClock):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.provider = provider
        self.clock = clock
        self.crash_after_provider_call = False  # test hook
        self.crash_after_event_record = False  # test hook, inside the inbox transaction

    def close(self) -> None:
        self.db.close()

    # ---- intent --------------------------------------------------------
    def create_order(self, order_id: str, amount_minor: int, currency: str = "USD") -> None:
        fp = fingerprint(amount_minor, currency, order_id)
        with self.db:
            self.db.execute(
                "INSERT INTO orders(order_id, amount_minor, currency, idempotency_key, fingerprint, state)"
                " VALUES (?,?,?,?,?, 'CREATED')",
                (order_id, amount_minor, currency, str(uuid.uuid4()), fp),
            )

    def amend_amount(self, order_id: str, amount_minor: int) -> None:
        """Changing the payload is only legal while nothing was ever sent.

        After a send, the original request may have succeeded, so a new key plus a new
        amount could charge twice. The caller must reconcile first.
        """
        order = self.get(order_id)
        if order["state"] != "CREATED":
            raise ValueError(f"cannot amend an order in state {order['state']}")
        fp = fingerprint(amount_minor, order["currency"], order_id)
        with self.db:
            self.db.execute(
                "UPDATE orders SET amount_minor=?, fingerprint=?, idempotency_key=? WHERE order_id=?",
                (amount_minor, fp, str(uuid.uuid4()), order_id),
            )

    def get(self, order_id: str) -> sqlite3.Row:
        return self.db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()

    # ---- sending -------------------------------------------------------
    def attempt_charge(self, order_id: str) -> str:
        """Send (or re-send) the stored request. Returns the resulting order state."""
        order = self.get(order_id)
        if order["state"] in ("PAID", "DECLINED", "NEEDS_REVIEW"):
            return order["state"]
        if (order["state"] == "SENDING" and order["first_sent_at"] is not None
                and self.clock.now - order["first_sent_at"] >= self.RETRY_WINDOW_SECONDS):
            return self.reconcile(order_id)
        # Write ahead: record that a request may be in flight BEFORE making the call.
        with self.db:
            self.db.execute(
                "UPDATE orders SET state='SENDING', attempts=attempts+1,"
                " first_sent_at=COALESCE(first_sent_at, ?) WHERE order_id=?",
                (self.clock.now, order_id),
            )
        # The payload comes from storage, never from the caller, so it cannot drift.
        try:
            response = self.provider.create_charge(
                order["idempotency_key"], order["amount_minor"], order["currency"], order_id)
        except ProviderTimeout:
            return "SENDING"            # unknown, NOT failed
        except ProviderConflict:
            return "SENDING"            # original still executing; retry later, same key
        except IdempotencyMismatch:
            self._set(order_id, "NEEDS_REVIEW", note="provider reported a payload mismatch")
            return "NEEDS_REVIEW"

        if self.crash_after_provider_call:
            raise SimulatedCrash("process died before recording the provider response")
        return self._apply_response(order_id, response)

    def _apply_response(self, order_id: str, response: dict) -> str:
        if response["status"] == "succeeded":
            self._mark_paid(order_id, response["charge_id"])
            return self.get(order_id)["state"]
        self._set(order_id, "DECLINED", note=response.get("reason"))
        return "DECLINED"

    # ---- reconciliation ------------------------------------------------
    def reconcile(self, order_id: str) -> str:
        """Resolve an order stuck in SENDING by asking the provider what actually happened."""
        order = self.get(order_id)
        if order["state"] != "SENDING":
            return order["state"]
        charges = self.provider.find_by_reference(order_id)
        if len(charges) == 1:
            self._mark_paid(order_id, charges[0]["charge_id"])
            return self.get(order_id)["state"]
        if len(charges) > 1:
            self._set(order_id, "NEEDS_REVIEW", note="more than one charge found: refund path")
            return "NEEDS_REVIEW"
        # No charge found. Retrying the same key is safe only while the provider remembers it.
        age = self.clock.now - order["first_sent_at"]
        if age < self.RETRY_WINDOW_SECONDS:
            return self.attempt_charge(order_id)
        self._set(order_id, "NEEDS_REVIEW",
                  note="no charge found but the key retention window has passed; "
                       "lookups can lag, so a person or a second check decides before any new key")
        return "NEEDS_REVIEW"

    # ---- webhooks ------------------------------------------------------
    def handle_webhook(self, event: dict) -> None:
        with self.db:
            seen = self.db.execute("SELECT 1 FROM processed_events WHERE event_id=?",
                                   (event["event_id"],)).fetchone()
            if seen:
                return
            if event["type"] != "charge.succeeded":
                return
            order = self.get(event["reference"])
            if order is None:
                return
            self.db.execute("INSERT INTO processed_events(event_id) VALUES (?)", (event["event_id"],))
            if self.crash_after_event_record:
                raise SimulatedCrash("process died before applying the webhook state transition")
            # Receipt and business state commit together. Do not call helpers that
            # open their own transaction contexts inside this transaction.
            if order["state"] == "PAID" and order["charge_id"] != event["charge_id"]:
                self.db.execute(
                    "UPDATE orders SET state='NEEDS_REVIEW', note=? WHERE order_id=?",
                    (f"second charge {event['charge_id']} for an order already paid", order["order_id"]))
            elif order["state"] in ("CREATED", "SENDING"):
                self.db.execute(
                    "UPDATE orders SET state='PAID', charge_id=?, fulfilled=1"
                    " WHERE order_id=? AND state IN ('CREATED','SENDING')",
                    (event["charge_id"], order["order_id"]))

    # ---- helpers -------------------------------------------------------
    def _mark_paid(self, order_id: str, charge_id: str) -> None:
        """Move to PAID and set the fulfilled flag in one local transaction.

        The WHERE clause makes the transition happen only once, so a duplicate webhook
        or a second reconcile cannot fulfil the order again.
        """
        with self.db:
            self.db.execute(
                "UPDATE orders SET state='PAID', charge_id=?, fulfilled=1"
                " WHERE order_id=? AND state IN ('CREATED','SENDING')", (charge_id, order_id))

    def _set(self, order_id: str, state: str, note: str | None = None) -> None:
        with self.db:
            self.db.execute("UPDATE orders SET state=?, note=? WHERE order_id=?", (state, note, order_id))
