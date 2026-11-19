"""A simulated payment processor.

This is a teaching model of behaviour that real processors document (for example a
caller supplied idempotency key, a payload comparison, a retention window and
webhooks). It is not any vendor's implementation. Its state lives in ordinary Python
dicts, so it is only as durable as this process, which is fine for a simulator and
exactly what you must not copy into the merchant side of a real system.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import deque

from .clock import SimClock


class ProviderTimeout(Exception):
    """The caller gave up waiting. The outcome at the provider is unknown."""


class ProviderConflict(Exception):
    """Another request with this key is still executing (HTTP 409 style)."""


class IdempotencyMismatch(Exception):
    """The key was reused with a different payload (HTTP 422 style)."""


def fingerprint(amount_minor: int, currency: str, reference: str) -> str:
    body = json.dumps(
        {"amount_minor": amount_minor, "currency": currency, "reference": reference},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(body.encode()).hexdigest()


class SimulatedProvider:
    # Fault names for script_faults(); anything else raises ValueError.
    OK = "ok"
    TIMEOUT_BEFORE = "timeout_before"  # request lost, nothing happened
    TIMEOUT_AFTER = "timeout_after"    # charge happened, response lost
    SLOW = "slow"                      # still executing when the client gives up

    def __init__(self, clock: SimClock, key_ttl_seconds: int = 24 * 3600):
        self.clock = clock
        self.key_ttl = key_ttl_seconds
        self.charges: dict[str, dict] = {}
        self.events: list[dict] = []
        self._keys: dict[str, dict] = {}
        self._faults: deque[str] = deque()
        self._declined_references: set[str] = set()
        self._next_id = 1
        self.requests_seen = 0

    # ---- test controls -------------------------------------------------
    def script_faults(self, *faults: str) -> None:
        for fault in faults:
            if fault not in (self.OK, self.TIMEOUT_BEFORE, self.TIMEOUT_AFTER, self.SLOW):
                raise ValueError(f"unknown fault {fault!r}")
        self._faults = deque(faults)

    def decline_reference(self, reference: str) -> None:
        self._declined_references.add(reference)

    def settle(self) -> None:
        """Let slow in-flight requests finish."""
        for key, record in self._keys.items():
            if record["state"] == "in_flight":
                record["response"] = self._execute(record["payload"])
                record["state"] = "done"

    # ---- API -----------------------------------------------------------
    def create_charge(self, idempotency_key: str, amount_minor: int, currency: str, reference: str) -> dict:
        self.requests_seen += 1
        self._expire_keys()
        fp = fingerprint(amount_minor, currency, reference)
        record = self._keys.get(idempotency_key)
        if record is not None:
            if record["fingerprint"] != fp:
                raise IdempotencyMismatch("key was used with different parameters")
            if record["state"] == "in_flight":
                raise ProviderConflict("original request is still executing")
            replay = copy.deepcopy(record["response"])
            replay["replayed"] = True
            return replay

        fault = self._faults.popleft() if self._faults else self.OK
        if fault == self.TIMEOUT_BEFORE:
            raise ProviderTimeout("request never reached the provider")

        payload = {"amount_minor": amount_minor, "currency": currency, "reference": reference}
        record = {"fingerprint": fp, "payload": payload, "stored_at": self.clock.now}
        self._keys[idempotency_key] = record
        if fault == self.SLOW:
            record["state"] = "in_flight"
            raise ProviderTimeout("client gave up while the provider was still working")

        record["response"] = self._execute(payload)
        record["state"] = "done"
        if fault == self.TIMEOUT_AFTER:
            raise ProviderTimeout("response lost after the charge was made")
        return copy.deepcopy(record["response"])

    def find_by_reference(self, reference: str) -> list[dict]:
        """Reconciliation lookup. Assumed authoritative here; real lookups can lag."""
        return [copy.deepcopy(c) for c in self.charges.values() if c["reference"] == reference]

    def drain_events(self, duplicate: bool = False) -> list[dict]:
        """Webhook delivery is at-least-once: optionally deliver every event twice."""
        out: list[dict] = []
        for event in self.events:
            out.append(copy.deepcopy(event))
            if duplicate:
                out.append(copy.deepcopy(event))
        self.events = []
        return out

    # ---- internals -----------------------------------------------------
    def _execute(self, payload: dict) -> dict:
        if payload["reference"] in self._declined_references:
            return {"status": "declined", "reason": "card_declined", "replayed": False}
        charge_id = f"ch_{self._next_id:04d}"
        self._next_id += 1
        self.charges[charge_id] = dict(payload, charge_id=charge_id, created_at=self.clock.now)
        self.events.append(
            {"event_id": f"evt_{charge_id}", "type": "charge.succeeded", "charge_id": charge_id,
             "reference": payload["reference"]}
        )
        return {"status": "succeeded", "charge_id": charge_id, "replayed": False}

    def _expire_keys(self) -> None:
        expired = [k for k, r in self._keys.items()
                   if r["state"] == "done" and self.clock.now - r["stored_at"] >= self.key_ttl]
        for key in expired:
            del self._keys[key]
