"""Count integer event timestamps in half-open windows over a fixed snapshot."""

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from random import Random


def scan_counts(events, windows):
    """Direct implementation of start <= timestamp < stop."""
    return [sum(1 for timestamp in events if start <= timestamp < stop)
            for start, stop in windows]


def indexed_counts(events, windows):
    ordered = sorted(events)
    return [bisect_left(ordered, stop) - bisect_left(ordered, start)
            for start, stop in windows]


def rejected_counts(events, windows):
    """Incorrect: includes events on the upper boundary."""
    ordered = sorted(events)
    return [bisect_right(ordered, stop) - bisect_left(ordered, start)
            for start, stop in windows]


@dataclass(frozen=True)
class Workload:
    name: str
    events: tuple
    windows: tuple
    batches: int


def workloads():
    rng = Random(731)
    spread = tuple(rng.randrange(8192) for _ in range(4096))
    windows = tuple((start, start + rng.choice((0, 5, 120, 1024)))
                    for start in (rng.randrange(-128, 8192) for _ in range(128)))
    bursty = tuple(rng.choice((100, 500, 2000)) + rng.randrange(-3, 4)
                   for _ in range(16384))
    burst_windows = tuple((start, start + width)
                          for start in (90, 100, 103, 490, 500, 503, 2000, 2003)
                          for width in (0, 1, 8, 100))
    return (
        Workload("single lookup", spread, ((100, 220),), 100),
        Workload("dashboard batch", spread, windows, 3),
        Workload("clustered events", bursty, burst_windows, 3),
    )
