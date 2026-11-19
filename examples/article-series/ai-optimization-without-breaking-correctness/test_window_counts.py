import unittest
from itertools import combinations_with_replacement, product

from window_counts import indexed_counts, rejected_counts, scan_counts, workloads


class WindowCountsTests(unittest.TestCase):
    def test_literal_expected_counts(self):
        events = (10, 8, 10, 15)
        windows = ((8, 10), (10, 15), (15, 15), (15, 16), (-5, 0))
        self.assertEqual(scan_counts(events, windows), [1, 2, 0, 1, 0])
        self.assertEqual(indexed_counts(events, windows), [1, 2, 0, 1, 0])
        self.assertEqual(indexed_counts(events, ()), [])

    def test_exhaustive_small_inputs_against_scan(self):
        windows = tuple(combinations_with_replacement(range(-2, 3), 2))
        for length in range(5):
            for events in product(range(-1, 2), repeat=length):
                with self.subTest(events=events):
                    self.assertEqual(indexed_counts(events, windows),
                                     scan_counts(events, windows))

    def test_benchmark_workloads_against_scan(self):
        for workload in workloads():
            with self.subTest(workload=workload.name):
                self.assertEqual(indexed_counts(workload.events, workload.windows),
                                 scan_counts(workload.events, workload.windows))

    def test_rejected_candidate_exposes_upper_boundary_bug(self):
        events = (10, 8, 10, 15)
        windows = ((8, 10), (15, 15))
        self.assertEqual(scan_counts(events, windows), [1, 0])
        self.assertEqual(rejected_counts(events, windows), [3, 1])


if __name__ == "__main__":
    unittest.main()
