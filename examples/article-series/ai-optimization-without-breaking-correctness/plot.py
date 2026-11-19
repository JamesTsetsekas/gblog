"""Render the archived summary; plotting is optional and requires matplotlib."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


def main():
    example = Path(__file__).resolve().parent
    result = json.loads((example / "measured-run.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(10, 5.6), layout="constrained")
    fig.set_facecolor("white")
    ax.set_facecolor("white")
    colors = {"scan": "#4d4d4d", "indexed": "#b65b00"}
    labels = {"scan": "Scan reference", "indexed": "Sort and bisect (sort included)"}
    for method, offset in [("scan", -0.14), ("indexed", 0.14)]:
        rows = [row[method] for row in result["workloads"]]
        medians = [row[0] / 1000 for row in rows]
        lower = [(row[0] - row[1]) / 1000 for row in rows]
        upper = [(row[2] - row[0]) / 1000 for row in rows]
        ys = [index + offset for index in range(len(rows))]
        ax.errorbar(medians, ys, xerr=[lower, upper], fmt="o", capsize=4,
                    color=colors[method], label=labels[method], markersize=6)
        for median, y, row in zip(medians, ys, rows):
            ax.annotate(f"{median:.3f} ms", (row[2] / 1000, y),
                        xytext=(8, 0), textcoords="offset points", va="center", fontsize=9)
    ax.set_yticks(range(3), [
        f"{row['name']}\n{row['events']:,} events / {row['windows']} "
        f"{'window' if row['windows'] == 1 else 'windows'}"
        for row in result["workloads"]
    ])
    ax.set_xscale("log")
    ax.set_xticks([0.1, 0.3, 1, 3, 10, 30, 100])
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.set_xlim(0.1, 100)
    ax.set_ylim(2.6, -0.7)
    ax.set_xlabel("Milliseconds per complete batch (logarithmic scale; lower is faster)")
    ax.set_title("The query batch changes which implementation is faster", loc="left", pad=18)
    ax.grid(axis="x", which="major", color="#dddddd", linewidth=0.7)
    ax.set_axisbelow(True)
    for edge in ["top", "right", "left"]:
        ax.spines[edge].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=12)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    fig.supxlabel("One local run, nine sample averages per method. Whiskers show observed min/max, not confidence intervals.\n"
                  "CPython 3.13.1 on a shared Windows machine. Synthetic in-memory workloads.", fontsize=9)
    output = example.parents[2] / "src/images/posts/ai-optimization-without-breaking-correctness"
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "batch-timings.png", dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
