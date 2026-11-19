"""The tempting version: a timeout means failure, so try again with a fresh key.

It is here only so the tests can show what goes wrong. Do not copy it.
"""
import uuid

from .provider import ProviderTimeout, SimulatedProvider


class NaiveMerchant:
    def __init__(self, provider: SimulatedProvider, max_attempts: int = 3):
        self.provider = provider
        self.max_attempts = max_attempts

    def pay(self, order_id: str, amount_minor: int, currency: str = "USD") -> str:
        for _ in range(self.max_attempts):
            try:
                response = self.provider.create_charge(str(uuid.uuid4()), amount_minor, currency, order_id)
                return response["status"]
            except ProviderTimeout:
                continue  # "it failed, try again" is the bug
        return "failed"
