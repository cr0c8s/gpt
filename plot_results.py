#!/usr/bin/env python3
"""
Wi-Fi Network Simulation: Chain vs Cluster Topology Comparison Plots.

Reads chain-results.csv and cluster-results.csv produced by the ns-3 simulation
and generates informative comparison bar charts for:
  1. Throughput (Mbps)
  2. Packet Loss (%)
  3. Average Delay (ms)
  4. Average Jitter (ms)
  5. Combined summary dashboard
"""

import csv
import sys
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load_csv(path):
    """Load CSV and return the primary data flow (largest tx_packets)."""
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        return None

    best = max(rows, key=lambda r: int(r["tx_packets"]))
    return {
        "topology":      best["topology"],
        "tx_packets":    int(best["tx_packets"]),
        "rx_packets":    int(best["rx_packets"]),
        "tx_bytes":      int(best["tx_bytes"]),
        "rx_bytes":      int(best["rx_bytes"]),
        "packet_loss":   float(best["packet_loss_pct"]),
        "throughput":    float(best["throughput_mbps"]),
        "delay":         float(best["avg_delay_ms"]),
        "jitter":        float(best["avg_jitter_ms"]),
    }


def make_single_bar(ax, labels, values, title, ylabel, colors, annotations=True):
    """Create a single bar chart on the given axes."""
    x = np.arange(len(labels))
    bars = ax.bar(x, values, width=0.5, color=colors, edgecolor="black",
                  linewidth=0.8, zorder=3)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    if annotations:
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f"{val:.4f}" if val < 1 else f"{val:.2f}",
                        ha="center", va="bottom", fontsize=10, fontweight="bold")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    chain_path = os.path.join(script_dir, "chain-results.csv")
    cluster_path = os.path.join(script_dir, "cluster-results.csv")

    if not os.path.exists(chain_path):
        print(f"ERROR: {chain_path} not found")
        sys.exit(1)
    if not os.path.exists(cluster_path):
        print(f"ERROR: {cluster_path} not found")
        sys.exit(1)

    chain = load_csv(chain_path)
    cluster = load_csv(cluster_path)

    if chain is None or cluster is None:
        print("ERROR: empty CSV data")
        sys.exit(1)

    labels = [
        "Chain\n(Sequential, 12 hops)",
        "Cluster\n(Grouped, 3 freq.)"
    ]
    colors = ["#E74C3C", "#2ECC71"]

    # --- Individual plots ---

    metrics = [
        ("throughput", "Throughput Comparison",
         "Throughput (Mbps)",
         "Higher is better: cluster routing reduces hop count,\n"
         "minimizing collisions and retransmissions.",
         "throughput_comparison.png"),

        ("packet_loss", "Packet Loss Comparison",
         "Packet Loss (%)",
         "Lower is better: fewer intermediate hops means\n"
         "fewer chances for packet drops.",
         "packet_loss_comparison.png"),

        ("delay", "Average End-to-End Delay Comparison",
         "Average Delay (ms)",
         "Lower is better: clustered topology reduces\n"
         "the number of forwarding hops.",
         "delay_comparison.png"),

        ("jitter", "Average Jitter Comparison",
         "Average Jitter (ms)",
         "Lower is better: fewer hops produce more\n"
         "consistent delivery timing.",
         "jitter_comparison.png"),
    ]

    for key, title, ylabel, explanation, filename in metrics:
        fig, ax = plt.subplots(figsize=(8, 5))
        vals = [chain[key], cluster[key]]
        make_single_bar(ax, labels, vals, title, ylabel, colors)

        ax.text(0.5, -0.18, explanation,
                transform=ax.transAxes, ha="center", va="top",
                fontsize=9, style="italic", color="#555555")

        fig.tight_layout(rect=[0, 0.05, 1, 1])
        out = os.path.join(script_dir, filename)
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")

    # --- Load metrics ---

    fig, ax = plt.subplots(figsize=(10, 6))

    bar_labels = [
        "Tx Packets", "Rx Packets", "Tx Bytes (KB)", "Rx Bytes (KB)"
    ]
    chain_load = [
        chain["tx_packets"], chain["rx_packets"],
        chain["tx_bytes"] / 1024, chain["rx_bytes"] / 1024
    ]
    cluster_load = [
        cluster["tx_packets"], cluster["rx_packets"],
        cluster["tx_bytes"] / 1024, cluster["rx_bytes"] / 1024
    ]

    x = np.arange(len(bar_labels))
    w = 0.35
    bars1 = ax.bar(x - w/2, chain_load, w, label="Chain", color=colors[0],
                   edgecolor="black", linewidth=0.8, zorder=3)
    bars2 = ax.bar(x + w/2, cluster_load, w, label="Cluster", color=colors[1],
                   edgecolor="black", linewidth=0.8, zorder=3)

    ax.set_title("Network Load Comparison", fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel("Value", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(bar_labels, fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    for bar in list(bars1) + list(bars2):
        val = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, val,
                f"{val:.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    fig.tight_layout()
    out = os.path.join(script_dir, "load_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # --- Combined dashboard ---

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Wi-Fi Simulation: Chain vs Cluster Topology\n"
        "12 nodes  |  802.11n  |  OLSR routing  |  2 Mbps offered rate",
        fontsize=15, fontweight="bold", y=0.98
    )

    dashboard = [
        (axes[0, 0], "throughput", "Throughput", "Mbps", "▲ Higher = Better"),
        (axes[0, 1], "packet_loss", "Packet Loss", "%", "▼ Lower = Better"),
        (axes[1, 0], "delay", "Avg Delay", "ms", "▼ Lower = Better"),
        (axes[1, 1], "jitter", "Avg Jitter", "ms", "▼ Lower = Better"),
    ]

    for ax, key, title, unit, note in dashboard:
        vals = [chain[key], cluster[key]]
        make_single_bar(ax, ["Chain", "Cluster"], vals,
                        f"{title} ({unit})", unit, colors)
        ax.text(0.98, 0.95, note, transform=ax.transAxes,
                ha="right", va="top", fontsize=9,
                color="#888", fontstyle="italic",
                bbox=dict(boxstyle="round,pad=0.3",
                          facecolor="white", alpha=0.8))

    if chain["throughput"] > 0 and cluster["throughput"] > 0:
        improvement = ((cluster["throughput"] - chain["throughput"]) /
                       chain["throughput"] * 100)
        sign = "+" if improvement > 0 else ""
        summary = (
            f"Throughput: {sign}{improvement:.1f}%  |  "
            f"Loss: {chain['packet_loss']:.1f}% → {cluster['packet_loss']:.1f}%  |  "
            f"Delay: {chain['delay']:.2f} → {cluster['delay']:.2f} ms"
        )
    else:
        summary = "One or both topologies had zero throughput — check simulation parameters."

    fig.text(0.5, 0.01, summary, ha="center", fontsize=11,
             fontweight="bold", color="#333",
             bbox=dict(boxstyle="round,pad=0.4",
                       facecolor="#F0F0F0", alpha=0.9))

    fig.tight_layout(rect=[0, 0.04, 1, 0.94])
    out = os.path.join(script_dir, "dashboard_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # --- Print summary table ---

    print("\n" + "=" * 60)
    print("  SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Metric':<25} {'Chain':>12} {'Cluster':>12} {'Delta':>12}")
    print("-" * 60)

    rows = [
        ("Tx Packets",      chain["tx_packets"],  cluster["tx_packets"],  ""),
        ("Rx Packets",      chain["rx_packets"],  cluster["rx_packets"],  ""),
        ("Packet Loss (%)", chain["packet_loss"], cluster["packet_loss"],
         f"{cluster['packet_loss'] - chain['packet_loss']:+.2f}"),
        ("Throughput (Mbps)", chain["throughput"], cluster["throughput"],
         f"{cluster['throughput'] - chain['throughput']:+.4f}"),
        ("Avg Delay (ms)",  chain["delay"],       cluster["delay"],
         f"{cluster['delay'] - chain['delay']:+.2f}"),
        ("Avg Jitter (ms)", chain["jitter"],      cluster["jitter"],
         f"{cluster['jitter'] - chain['jitter']:+.4f}"),
    ]

    for name, c, cl, delta in rows:
        if isinstance(c, int):
            print(f"{name:<25} {c:>12d} {cl:>12d} {delta:>12}")
        else:
            print(f"{name:<25} {c:>12.4f} {cl:>12.4f} {delta:>12}")

    print("=" * 60)
    print("Done. All graphs saved.")


if __name__ == "__main__":
    main()
