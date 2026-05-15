#!/usr/bin/env python3
"""
Wi-Fi Network Simulation: Chain vs Cluster Topology — Dependency Graphs.

Reads sweep-results.csv (chain N=3..12 + cluster) and generates dependency
plots showing how metrics change as a function of hop count / topology.

Generated graphs:
  1. Throughput = f(hops)           — line graph
  2. Packet Loss = f(hops)         — line graph
  3. Delay = f(hops)               — line graph
  4. Jitter = f(hops)              — line graph
  5. Throughput vs Delay            — scatter / parametric
  6. Radar chart                    — multi-metric normalized comparison
  7. Combined dashboard (2x2)      — all dependency lines in one figure
"""

import csv
import sys
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


def load_sweep(path):
    chain_rows = []
    cluster_row = None

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry = {
                "topology":    row["topology"],
                "num_nodes":   int(row["num_nodes"]),
                "num_hops":    int(row["num_hops"]),
                "tx_packets":  int(row["tx_packets"]),
                "rx_packets":  int(row["rx_packets"]),
                "tx_bytes":    int(row["tx_bytes"]),
                "rx_bytes":    int(row["rx_bytes"]),
                "packet_loss": float(row["packet_loss_pct"]),
                "throughput":  float(row["throughput_mbps"]),
                "delay":       float(row["avg_delay_ms"]),
                "jitter":      float(row["avg_jitter_ms"]),
            }
            if row["topology"] == "chain":
                chain_rows.append(entry)
            else:
                cluster_row = entry

    chain_rows.sort(key=lambda r: r["num_hops"])
    return chain_rows, cluster_row


CHAIN_COLOR = "#E74C3C"
CLUSTER_COLOR = "#2ECC71"
CHAIN_MARKER = "o"
CLUSTER_MARKER = "D"


def plot_dependency(ax, chain_rows, cluster_row, metric_key, ylabel, title,
                    higher_better=True, show_legend=True):
    """Line plot: metric vs number of hops. Chain as line, Cluster as horizontal ref."""

    hops = [r["num_hops"] for r in chain_rows]
    vals = [r[metric_key] for r in chain_rows]

    ax.plot(hops, vals, color=CHAIN_COLOR, marker=CHAIN_MARKER, markersize=7,
            linewidth=2.2, label="Chain (single channel)", zorder=5)

    for h, v in zip(hops, vals):
        fmt = f"{v:.2f}" if v >= 1 else f"{v:.3f}"
        ax.annotate(fmt, (h, v), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=7.5, color=CHAIN_COLOR, fontweight="bold")

    if cluster_row:
        cl_val = cluster_row[metric_key]
        cl_hops = cluster_row["num_hops"]
        ax.axhline(y=cl_val, color=CLUSTER_COLOR, linestyle="--", linewidth=1.8,
                   alpha=0.7, zorder=3)
        ax.plot(cl_hops, cl_val, color=CLUSTER_COLOR, marker=CLUSTER_MARKER,
                markersize=10, zorder=6, label="Cluster (3 freq. channels)")

        fmt = f"{cl_val:.2f}" if cl_val >= 1 else f"{cl_val:.4f}"
        ax.annotate(fmt, (cl_hops, cl_val), textcoords="offset points",
                    xytext=(30, -15), ha="center", fontsize=8.5,
                    color=CLUSTER_COLOR, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=CLUSTER_COLOR,
                                   lw=1.2))

    ax.set_xlabel("Number of hops", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)

    ax.set_xticks(hops)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    direction = "higher = better" if higher_better else "lower = better"
    ax.text(0.98, 0.95 if higher_better else 0.05, direction,
            transform=ax.transAxes, ha="right",
            va="top" if higher_better else "bottom",
            fontsize=8, fontstyle="italic", color="#888",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    if show_legend:
        ax.legend(fontsize=9, loc="best")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sweep_path = os.path.join(script_dir, "sweep-results.csv")

    if not os.path.exists(sweep_path):
        print(f"ERROR: {sweep_path} not found. Run simulation with --mode=sweep first.")
        sys.exit(1)

    chain, cluster = load_sweep(sweep_path)
    if not chain:
        print("ERROR: no chain data in sweep-results.csv")
        sys.exit(1)

    # =========================================================
    # 1. Throughput = f(hops)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_dependency(ax, chain, cluster, "throughput",
                    "Throughput (Mbps)",
                    "Throughput dependency on number of hops",
                    higher_better=True)
    ax.set_ylim(bottom=0)
    ax.text(0.5, -0.12,
            "As the number of hops increases, throughput degrades because each hop\n"
            "reuses the same radio channel, causing contention and collisions (CSMA/CA).\n"
            "The cluster topology with frequency separation maintains near-ideal throughput.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = os.path.join(script_dir, "throughput_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 2. Packet Loss = f(hops)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_dependency(ax, chain, cluster, "packet_loss",
                    "Packet Loss (%)",
                    "Packet loss dependency on number of hops",
                    higher_better=False)
    ax.set_ylim(bottom=-0.5)
    ax.text(0.5, -0.12,
            "Packet loss grows with hop count: each intermediate node introduces\n"
            "collision risk, queue overflow, and retry exhaustion.\n"
            "Cluster routing (3 hops on separate frequencies) virtually eliminates losses.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = os.path.join(script_dir, "packet_loss_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 3. Delay = f(hops)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_dependency(ax, chain, cluster, "delay",
                    "Average Delay (ms)",
                    "Average delay dependency on number of hops",
                    higher_better=False)
    ax.set_ylim(bottom=0)
    ax.text(0.5, -0.12,
            "Delay grows approximately linearly with hop count. Each hop adds\n"
            "CSMA/CA backoff, transmission, and queuing delays (~0.5 ms/hop).\n"
            "Cluster topology at 3 hops keeps delay at 1.19 ms vs 5.40 ms for 11-hop chain.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = os.path.join(script_dir, "delay_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 4. Jitter = f(hops)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_dependency(ax, chain, cluster, "jitter",
                    "Average Jitter (ms)",
                    "Average jitter dependency on number of hops",
                    higher_better=False)
    ax.set_ylim(bottom=0)
    ax.text(0.5, -0.12,
            "Jitter (delay variation) increases with hop count due to accumulating\n"
            "random CSMA/CA backoff intervals and variable queue lengths.\n"
            "Cluster topology keeps jitter at 0.015 ms — suitable for real-time apps.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = os.path.join(script_dir, "jitter_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 5. Throughput vs Delay (parametric scatter)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))

    chain_thr = [r["throughput"] for r in chain]
    chain_del = [r["delay"] for r in chain]
    chain_hops = [r["num_hops"] for r in chain]

    scatter = ax.scatter(chain_del, chain_thr, c=chain_hops, cmap="YlOrRd",
                         s=120, edgecolors="black", linewidth=0.8, zorder=5,
                         vmin=2, vmax=12)

    for d, t, h in zip(chain_del, chain_thr, chain_hops):
        ax.annotate(f"{h} hops", (d, t), textcoords="offset points",
                    xytext=(12, 5), fontsize=8, color="#555")

    ax.plot(chain_del, chain_thr, color=CHAIN_COLOR, linewidth=1.2,
            alpha=0.4, linestyle="--", zorder=3)

    if cluster:
        ax.scatter([cluster["delay"]], [cluster["throughput"]],
                   color=CLUSTER_COLOR, marker=CLUSTER_MARKER, s=180,
                   edgecolors="black", linewidth=1.2, zorder=6,
                   label="Cluster (3 hops, 3 freq.)")
        ax.annotate("Cluster\n3 hops", (cluster["delay"], cluster["throughput"]),
                    textcoords="offset points", xytext=(-50, -25),
                    fontsize=9, fontweight="bold", color=CLUSTER_COLOR,
                    arrowprops=dict(arrowstyle="->", color=CLUSTER_COLOR, lw=1.5))

    cbar = fig.colorbar(scatter, ax=ax, label="Number of hops (chain)", pad=0.02)
    cbar.ax.tick_params(labelsize=9)

    ax.set_xlabel("Average Delay (ms)", fontsize=11)
    ax.set_ylabel("Throughput (Mbps)", fontsize=11)
    ax.set_title("Throughput vs Delay: trade-off dependency",
                 fontsize=13, fontweight="bold", pad=10)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(fontsize=10, loc="lower left")

    ax.annotate("", xy=(0.3, 2.1), xytext=(5.5, 1.35),
                arrowprops=dict(arrowstyle="fancy", color="#2ECC71",
                                alpha=0.3, lw=3))
    ax.text(2.5, 1.85, "Better", fontsize=10, color="#2ECC71",
            fontweight="bold", alpha=0.5, rotation=10)

    ax.text(0.5, -0.1,
            "Each point is a chain topology with a different number of nodes/hops.\n"
            "As hops increase (warmer color), delay grows and throughput drops.\n"
            "The cluster point (green diamond) achieves the best trade-off.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")

    fig.tight_layout(rect=[0, 0.05, 1, 1])
    out = os.path.join(script_dir, "throughput_vs_delay.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 6. Radar chart — normalized comparison (chain-12 vs cluster)
    # =========================================================
    chain12 = [r for r in chain if r["num_hops"] == 11]
    if chain12 and cluster:
        chain12 = chain12[0]

        categories = ["Throughput", "1 / Packet Loss",
                       "1 / Delay", "1 / Jitter",
                       "Delivery Ratio"]

        c12_delivery = chain12["rx_packets"] / chain12["tx_packets"] * 100
        cl_delivery = cluster["rx_packets"] / cluster["tx_packets"] * 100

        raw_chain = [
            chain12["throughput"],
            1.0 / max(chain12["packet_loss"], 0.001),
            1.0 / chain12["delay"],
            1.0 / chain12["jitter"],
            c12_delivery,
        ]
        raw_cluster = [
            cluster["throughput"],
            1.0 / max(cluster["packet_loss"], 0.001),
            1.0 / cluster["delay"],
            1.0 / cluster["jitter"],
            cl_delivery,
        ]

        max_vals = [max(a, b) for a, b in zip(raw_chain, raw_cluster)]
        norm_chain = [v / m if m > 0 else 0 for v, m in zip(raw_chain, max_vals)]
        norm_cluster = [v / m if m > 0 else 0 for v, m in zip(raw_cluster, max_vals)]

        N = len(categories)
        angles = [n / float(N) * 2 * math.pi for n in range(N)]
        angles += angles[:1]

        norm_chain += norm_chain[:1]
        norm_cluster += norm_cluster[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

        ax.plot(angles, norm_chain, color=CHAIN_COLOR, linewidth=2.2,
                marker=CHAIN_MARKER, markersize=7, label="Chain (11 hops)")
        ax.fill(angles, norm_chain, color=CHAIN_COLOR, alpha=0.12)

        ax.plot(angles, norm_cluster, color=CLUSTER_COLOR, linewidth=2.2,
                marker=CLUSTER_MARKER, markersize=7, label="Cluster (3 hops)")
        ax.fill(angles, norm_cluster, color=CLUSTER_COLOR, alpha=0.12)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylim(0, 1.15)
        ax.set_title("Normalized performance comparison\n(Chain 12 nodes vs Cluster 12 nodes)",
                      fontsize=13, fontweight="bold", pad=20)
        ax.legend(fontsize=10, loc="upper right", bbox_to_anchor=(1.25, 1.12))

        fig.tight_layout()
        out = os.path.join(script_dir, "radar_comparison.png")
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")

    # =========================================================
    # 7. Dashboard — 4 dependency plots in one figure
    # =========================================================
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.suptitle(
        "Wi-Fi Simulation: metric dependencies on hop count\n"
        "Chain (single channel, 3-12 nodes)  vs  Cluster (3 freq. channels, 12 nodes)\n"
        "802.11n  |  OLSR  |  2 Mbps offered rate",
        fontsize=14, fontweight="bold", y=0.99)

    metrics_dash = [
        (axes[0, 0], "throughput", "Throughput (Mbps)",
         "Throughput = f(hops)", True),
        (axes[0, 1], "packet_loss", "Packet Loss (%)",
         "Packet Loss = f(hops)", False),
        (axes[1, 0], "delay", "Average Delay (ms)",
         "Average Delay = f(hops)", False),
        (axes[1, 1], "jitter", "Average Jitter (ms)",
         "Average Jitter = f(hops)", False),
    ]

    for ax, key, ylabel, title, hb in metrics_dash:
        plot_dependency(ax, chain, cluster, key, ylabel, title,
                        higher_better=hb, show_legend=False)
        ax.set_ylim(bottom=0 if key != "packet_loss" else -0.5)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2,
               fontsize=11, bbox_to_anchor=(0.5, 0.01))

    if chain12 and cluster:
        summary = (
            f"At 12 nodes: Chain (11 hops) vs Cluster (3 hops)  —  "
            f"Throughput: {chain12['throughput']:.2f} vs {cluster['throughput']:.2f} Mbps  |  "
            f"Loss: {chain12['packet_loss']:.1f}% vs {cluster['packet_loss']:.3f}%  |  "
            f"Delay: {chain12['delay']:.1f} vs {cluster['delay']:.1f} ms")
        fig.text(0.5, 0.04, summary, ha="center", fontsize=10,
                 fontweight="bold", color="#333",
                 bbox=dict(boxstyle="round,pad=0.4",
                           facecolor="#F0F0F0", alpha=0.9))

    fig.tight_layout(rect=[0, 0.07, 1, 0.94])
    out = os.path.join(script_dir, "dashboard_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 8. Load: Delivered vs Lost packets (area-style)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))

    hops = [r["num_hops"] for r in chain]
    delivered = [r["rx_packets"] for r in chain]
    lost = [r["tx_packets"] - r["rx_packets"] for r in chain]

    ax.fill_between(hops, 0, delivered, alpha=0.4, color="#2ECC71",
                    label="Delivered packets", zorder=3)
    ax.fill_between(hops, delivered,
                    [d + l for d, l in zip(delivered, lost)],
                    alpha=0.4, color="#E74C3C", label="Lost packets", zorder=3)

    ax.plot(hops, delivered, color="#27AE60", linewidth=2, marker="o",
            markersize=6, zorder=5)
    ax.plot(hops, [d + l for d, l in zip(delivered, lost)],
            color="#C0392B", linewidth=2, marker="s", markersize=6,
            zorder=5, label="Total Tx")

    if cluster:
        ax.scatter([cluster["num_hops"]], [cluster["rx_packets"]],
                   color=CLUSTER_COLOR, marker=CLUSTER_MARKER, s=160,
                   edgecolors="black", linewidth=1.2, zorder=7,
                   label=f"Cluster Rx ({cluster['rx_packets']})")

    for h, d, l in zip(hops, delivered, lost):
        if l > 200:
            ax.annotate(f"lost: {l}", (h, d + l), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=7.5,
                        color="#C0392B", fontweight="bold")

    ax.set_xlabel("Number of hops", fontsize=11)
    ax.set_ylabel("Packets", fontsize=11)
    ax.set_title("Delivered vs Lost packets dependency on hop count",
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_xticks(hops)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc="best")

    ax.text(0.5, -0.1,
            "Green area = successfully delivered packets. Red area = lost packets.\n"
            "As hops increase, the loss zone expands due to cumulative collision probability.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    out = os.path.join(script_dir, "load_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # Print summary table
    # =========================================================
    print("\n" + "=" * 80)
    print("  SWEEP RESULTS TABLE")
    print("=" * 80)
    print(f"{'Topology':<10} {'Nodes':>6} {'Hops':>5} {'Throughput':>12} "
          f"{'Loss %':>10} {'Delay ms':>10} {'Jitter ms':>10}")
    print("-" * 80)

    for r in chain:
        print(f"{'chain':<10} {r['num_nodes']:>6} {r['num_hops']:>5} "
              f"{r['throughput']:>12.4f} {r['packet_loss']:>10.4f} "
              f"{r['delay']:>10.4f} {r['jitter']:>10.4f}")

    if cluster:
        print(f"{'cluster':<10} {cluster['num_nodes']:>6} {cluster['num_hops']:>5} "
              f"{cluster['throughput']:>12.4f} {cluster['packet_loss']:>10.4f} "
              f"{cluster['delay']:>10.4f} {cluster['jitter']:>10.4f}")

    print("=" * 80)
    print("Done. All graphs saved.")


if __name__ == "__main__":
    main()
