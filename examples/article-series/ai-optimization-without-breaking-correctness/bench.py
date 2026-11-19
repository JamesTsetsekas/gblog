"""Time complete batches, including index construction, after a correctness check."""

import platform
from statistics import median
from time import perf_counter_ns

from window_counts import indexed_counts, scan_counts, workloads


def sample_microseconds(run, workload):
    start = perf_counter_ns()
    for _ in range(workload.batches):
        run(workload.events, workload.windows)
    return (perf_counter_ns() - start) / workload.batches / 1000


def main():
    methods = (scan_counts, indexed_counts)
    print(f"{platform.python_implementation()} {platform.python_version()} | "
          f"{platform.platform()}")
    print("Microseconds per complete batch | median [min, max], 9 samples")
    for workload in workloads():
        expected = scan_counts(workload.events, workload.windows)
        if indexed_counts(workload.events, workload.windows) != expected:
            raise RuntimeError(f"Candidate failed the oracle for {workload.name}")

        for method in methods:
            sample_microseconds(method, workload)

        samples = {method: [] for method in methods}
        for round_number in range(9):
            order = methods if round_number % 2 == 0 else methods[::-1]
            for method in order:
                samples[method].append(sample_microseconds(method, workload))

        print(f"{workload.name}: {len(workload.events):,} events, "
              f"{len(workload.windows)} windows, {workload.batches} batches/sample")
        for method, values in samples.items():
            print(f"  {method.__name__:14} {median(values):8.1f} "
                  f"[{min(values):.1f}, {max(values):.1f}]")


if __name__ == "__main__":
    main()
