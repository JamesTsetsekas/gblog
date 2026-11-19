class SimClock:
    """A logical clock in seconds so tests never sleep and never depend on wall time."""

    def __init__(self, now: int = 0):
        self.now = now

    def advance(self, seconds: int) -> None:
        self.now += seconds
