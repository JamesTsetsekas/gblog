---
title: "Can AI Make Code Faster Without Making It Wrong?"
description: "A runnable Python experiment uses an exact reference and three workloads to decide when sorting timestamps is worth the cost."
pubDate: "2026-11-19 00:00:00"
category: ["software-engineering", "ai", "python"]
banner: "@images/banners/article-series/ai-optimization-without-breaking-correctness.webp"
bannerAlt: "Two mechanical routes deliver identical rows of spheres beside a shared orange calibration rail."
ogImage: "@images/banners/article-series/ai-optimization-without-breaking-correctness-social.png"
tags: ["AI", "Performance", "Benchmarking", "Testing", "Python"]
selected: false
---

Suppose a dashboard loads a day's event timestamps and draws counts for a set of time windows. Its first implementation scans the event list for each window. A coding agent could propose sorting the timestamps once and finding the start and end of each window with binary search. That sounds promising. An off-by-one at the upper boundary would still put an event in the wrong bucket, and sorting might cost more than it saves if the caller only asks one question.

This is the kind of optimization I want to hand to an agent. The behavior fits in a few lines. I can keep a clear reference, test candidates against it, and time the whole operation callers pay for. The agent can explore. The evaluator decides which ideas earn a closer look.

## Give the agent an evaluator

Google DeepMind's AlphaEvolve provides a much larger example of that division of work. Its 2025 white paper describes a loop in which language models propose code changes, evaluators score the resulting programs, and promising programs feed later proposals. For a graph construction, an evaluator might check the required property before scoring the size of the graph. The evaluation function is part of how the researchers define the task. [AlphaEvolve white paper](https://arxiv.org/abs/2506.13131)

The metric needs to match the claim. The paper reports a construction for multiplying two 4 × 4 complex matrices using 48 scalar multiplications. That count is a property of the construction. The execution time of a matrix library would depend on further details such as additions, memory traffic, and numerical behavior. DeepMind's repository publishes verification notebooks for its tensor decompositions. In a separate 2026 infrastructure update, DeepMind reported a 20% reduction in write amplification from Spanner compaction changes. That is a developer-reported result for the storage metric they measured. [Verification artifacts](https://github.com/google-deepmind/alphaevolve), [DeepMind's May 2026 update](https://deepmind.google/blog/alphaevolve-impact/)

The timestamp experiment below borrows the idea of automated evaluation. It uses a fixed set of alternatives and has no model calls or evolutionary search. The measurements compare implementations of the same operation and say nothing about how much time AI saves while writing them.

## Make the boundary executable

The input is a reusable sequence of integer timestamps in any order, possibly with duplicates. Every window has `start <= stop`. The output is one count per window in the original query order. A timestamp counts when `start <= timestamp < stop`. Adjacent windows can share a boundary without counting its events twice, and an empty window always returns zero.

The reference loops over each window and counts matching events. Its code closely follows the rule, which makes it a useful correctness oracle. The indexed candidate sorts a copy, then subtracts the start insertion position from the stop insertion position for each query.

```python
ordered = sorted(events)
counts = [
    bisect_left(ordered, stop) - bisect_left(ordered, start)
    for start, stop in windows
]
```

Each insertion position splits the sorted list into values strictly below the requested bound and values at or above it. Their difference counts exactly the entries between the two split points, including duplicates inside the window. Using `bisect_right(ordered, stop)` instead moves the second split past every event equal to `stop`. [Python's bisection documentation](https://docs.python.org/3.13/library/bisect.html)

The rejected candidate keeps that mistake in executable form. With events `(10, 8, 10, 15)`, the window `[8, 10)` contains one event. The rejected candidate returns three. It also returns one for `[15, 15)`, which must be empty. A large random dataset can make these failures look rare if query boundaries seldom land on repeated event values. Choosing that boundary deliberately exposes the error in four integers.

The tests check literal expected counts, compare the indexed implementation with the scan across all 121 ordered event sequences of length zero through four drawn from three values, and verify all 15 valid windows formed from five bounds for each sequence. They also compare full output lists on the timing workloads. The split-point argument explains why the candidate works for the stated domain. The tests check the implementation against that argument and the separate reference.

## Charge the sort to the batch

A sort takes work up front. The scan makes a pass through the events for every query. The index sorts once for each batch and uses two binary searches per query. To measure the tradeoff, keep the sort inside the timed call and vary how many queries can share it.

A documented local run of [the dependency-free example](https://github.com/JamesTsetsekas/gblog/tree/main/examples/article-series/ai-optimization-without-breaking-correctness) used CPython 3.13.1, Windows 11 build 26200, and an Intel Core i7-8700K. The harness builds seeded inputs before timing and checks identical results first. It warms both methods, then alternates which runs first over nine samples. Each sample runs several complete batches and divides elapsed time by the batch count. Both methods allocate their result lists, and the indexed method creates its sorted copy on every batch. [Python's performance counter documentation](https://docs.python.org/3.13/library/time.html#time.perf_counter_ns)

| Workload | Events / windows | Scan, µs | Sort and bisect, µs |
| --- | ---: | ---: | ---: |
| Single lookup | 4,096 / 1 | 195.8 [162.4, 274.1] | 468.9 [390.4, 508.4] |
| Dashboard batch, same events | 4,096 / 128 | 25,298.4 [18,886.2, 30,441.0] | 449.8 [422.8, 479.0] |
| Clustered timestamps with many repeats | 16,384 / 32 | 25,847.3 [21,214.9, 32,864.6] | 1,298.0 [1,203.6, 1,597.1] |

Values are median [min, max] microseconds per complete batch in one local run. The ranges are observed sample ranges. The machine was shared and the process was warmed, so background work, caching, and runtime behavior can affect the numbers. Both invocations gave the same ordering for all three cases with different timings.

![Measured batch timings on a logarithmic millisecond scale. Sorting costs more for one lookup and less for the two larger batches; whiskers show the observed sample ranges.](@images/posts/ai-optimization-without-breaking-correctness/batch-timings.png)

*The plot uses the same local measurements as the table. The [archived summary and plotting script](https://github.com/JamesTsetsekas/gblog/tree/main/examples/article-series/ai-optimization-without-breaking-correctness) reproduce the figure. Whiskers are observed ranges, not confidence intervals.*

The indexed method cost more for a single window and less for the two larger batches. It also needs a sorted copy, whose memory cost this run did not measure. These synthetic inputs isolate one hot operation. They say little about total dashboard latency, which might be dominated by reading data or drawing the chart. They also leave the crossover point open. Event ordering, batch size, and how often the data changes would affect where it falls.

Run the checks and timings from the blog checkout with these commands.

```sh
cd examples/article-series/ai-optimization-without-breaking-correctness
python -B -m unittest -v
python -B bench.py
```

## Decide what makes the patch worth keeping

For a real dashboard I would check how often one snapshot serves multiple windows and where this function sits in the latency profile. If it really does spend most of its time repeating scans over the same snapshot, the indexed version gives me a specific patch to try. If the common request is one window on fresh data, the scan is a better starting point. Keeping an index across requests would be a different design that needs a policy for invalidation and a measurement that includes it.

An agent can offer more ideas, such as exploiting already-sorted input or processing a batch of ordered boundaries in one pass. Each idea needs to preserve the same boundary semantics and earn its place on the workload the application actually serves. In this example the most valuable artifact is the small harness that can tell me when to keep an approach, when to reject it, and which question to measure next.
