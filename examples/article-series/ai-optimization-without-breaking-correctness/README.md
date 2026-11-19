# Counting event timestamps in windows

The example accompanying *Can AI Make Code Faster Without Making It Wrong?* uses the Python standard library. Run from the blog repository root with Python 3.10 or newer.

```sh
cd examples/article-series/ai-optimization-without-breaking-correctness
python -B -m unittest -v
python -B bench.py
```

The input is a fixed, reusable sequence of integer timestamps, which can be unsorted and contain duplicates. Queries are half-open intervals with integer endpoints and `start <= stop`. Return one count per query in input order. Validation of input types or reversed intervals is outside the example's contract.

- `scan_counts` is the direct reference and the correctness oracle.
- `indexed_counts` sorts a copy and uses two left insertion positions per query.
- `rejected_counts` uses a right insertion position for the upper bound. The tests demonstrate its failure on repeated upper-bound timestamps and empty windows. The benchmark only times candidates that pass the workload checks.

Four tests passed on CPython 3.13.1. They cover literal expected answers, 1,815 sequence/window combinations in the exhaustive small domain, all three workloads, and the rejected candidate's counterexample.

## Timing

One sample averages 100 complete batches for the single-lookup workload and three for each of the other workloads. There are nine samples per method, preceded by warmup, with implementation order alternating each round. Workload generation and correctness checks are outside the timed operations. Result allocation and index construction are inside.

A local run on Windows 11 build 26200 with an Intel Core i7-8700K and CPython 3.13.1 produced these per-batch times. Brackets contain min and max observed sample averages.

| Workload | Events / windows | Scan, µs | Sort and bisect, µs |
| --- | ---: | ---: | ---: |
| Single lookup | 4,096 / 1 | 195.8 [162.4, 274.1] | 468.9 [390.4, 508.4] |
| Dashboard batch | 4,096 / 128 | 25,298.4 [18,886.2, 30,441.0] | 449.8 [422.8, 479.0] |
| Clustered events | 16,384 / 32 | 25,847.3 [21,214.9, 32,864.6] | 1,298.0 [1,203.6, 1,597.1] |

The machine was shared. Timings measure a warmed synthetic operation with inputs already in memory. These runs do not estimate memory consumption, data loading, cold-start behavior, the crossover point, or end-to-end performance. There is no remote service or model invocation in the experiment.

`measured-run.json` archives the table's summary statistics. Individual timing samples were not archived. To reproduce the article's figure from that summary, install matplotlib in your own plotting environment and run `python -B plot.py`. Plotting is optional; the experiment and tests require only the Python standard library.
