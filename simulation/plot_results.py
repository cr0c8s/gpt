#!/usr/bin/env python3
"""
Симуляция Wi-Fi сети: графики зависимостей Chain vs Cluster.

Читает sweep-results.csv и строит графики зависимостей метрик
от числа хопов для цепочечной и кластерной топологий.

Генерируемые графики:
  1.  Пропускная способность = f(хопы)
  2.  Потери пакетов = f(хопы)
  3.  Задержка = f(хопы)
  4.  Джиттер = f(хопы)
  5.  Пропускная способность vs Задержка (параметрическая диаграмма)
  6.  Радарная диаграмма нормированного сравнения
  7.  Сводная панель (2x2)
  8.  Доставленные vs потерянные пакеты (area)
  9.  КПД канала (эффективность использования полосы)
  10. Задержка на хоп (нормированная)
  11. Доля успешной доставки (PDR) = f(хопы)
  12. Скорость деградации метрик (производные)
  13. Столбчатая диаграмма: chain(12) vs cluster(12)
  14. Тепловая карта корреляции метрик
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
from matplotlib import rcParams

rcParams["font.family"] = "DejaVu Sans"
rcParams["font.size"] = 11
rcParams["axes.titlesize"] = 14
rcParams["axes.labelsize"] = 12
rcParams["xtick.labelsize"] = 10
rcParams["ytick.labelsize"] = 10


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
                    higher_better=True, show_legend=True, compact=False):
    hops = [r["num_hops"] for r in chain_rows]
    vals = [r[metric_key] for r in chain_rows]

    ax.plot(hops, vals, color=CHAIN_COLOR, marker=CHAIN_MARKER, markersize=6,
            linewidth=2.2, label="Цепочка (один канал)", zorder=5)

    if not compact:
        for i, (h, v) in enumerate(zip(hops, vals)):
            if i % 2 == 0:
                fmt = f"{v:.2f}" if v >= 1 else f"{v:.3f}"
                ax.annotate(fmt, (h, v), textcoords="offset points",
                            xytext=(0, 12), ha="center", fontsize=7,
                            color=CHAIN_COLOR, fontweight="bold")

    if cluster_row:
        cl_val = cluster_row[metric_key]
        cl_hops = cluster_row["num_hops"]
        ax.axhline(y=cl_val, color=CLUSTER_COLOR, linestyle="--", linewidth=1.8,
                   alpha=0.7, zorder=3)
        ax.plot(cl_hops, cl_val, color=CLUSTER_COLOR, marker=CLUSTER_MARKER,
                markersize=9, zorder=6, label="Кластер (3 частотных канала)")

        fmt = f"{cl_val:.2f}" if cl_val >= 1 else f"{cl_val:.4f}"
        ax.annotate(fmt, (cl_hops, cl_val), textcoords="offset points",
                    xytext=(40, -18), ha="center", fontsize=8,
                    color=CLUSTER_COLOR, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=CLUSTER_COLOR,
                                   lw=1.2))

    ax.set_xlabel("Количество хопов", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)

    ax.set_xticks(hops)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    direction = "\u25b2 больше = лучше" if higher_better else "\u25bc меньше = лучше"
    ax.text(0.98, 0.95 if higher_better else 0.05, direction,
            transform=ax.transAxes, ha="right",
            va="top" if higher_better else "bottom",
            fontsize=8, fontstyle="italic", color="#888",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    if show_legend:
        ax.legend(fontsize=9, loc="best", framealpha=0.9)


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
    # 1. Пропускная способность = f(хопы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 6.5))
    plot_dependency(ax, chain, cluster, "throughput",
                    "Пропускная способность (Мбит/с)",
                    "Зависимость пропускной способности от количества хопов",
                    higher_better=True)
    ax.set_ylim(bottom=0)

    caption = (
        "С увеличением числа хопов пропускная способность снижается, т.к. каждый хоп\n"
        "повторно использует один радиоканал, вызывая конкуренцию и коллизии (CSMA/CA).\n"
        "Кластерная топология с разделением частот сохраняет близкую к идеальной скорость."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=8.5, style="italic",
             color="#555", wrap=True)
    fig.subplots_adjust(bottom=0.20, top=0.92, left=0.10, right=0.95)
    out = os.path.join(script_dir, "throughput_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 2. Потери пакетов = f(хопы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 6.5))
    plot_dependency(ax, chain, cluster, "packet_loss",
                    "Потери пакетов (%)",
                    "Зависимость потерь пакетов от количества хопов",
                    higher_better=False)
    ax.set_ylim(bottom=-1)

    caption = (
        "Потери растут с увеличением числа хопов: каждый промежуточный узел вносит\n"
        "риск коллизий, переполнения очередей и исчерпания попыток передачи.\n"
        "Кластерная маршрутизация (3 хопа на раздельных частотах) практически устраняет потери."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=8.5, style="italic",
             color="#555", wrap=True)
    fig.subplots_adjust(bottom=0.20, top=0.92, left=0.10, right=0.95)
    out = os.path.join(script_dir, "packet_loss_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 3. Задержка = f(хопы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 6.5))
    plot_dependency(ax, chain, cluster, "delay",
                    "Средняя задержка (мс)",
                    "Зависимость средней задержки от количества хопов",
                    higher_better=False)
    ax.set_ylim(bottom=0)

    caption = (
        "Задержка растёт приблизительно линейно с числом хопов. Каждый хоп добавляет\n"
        "задержку CSMA/CA backoff, передачи кадра и ожидания в очереди (~0.5 мс/хоп).\n"
        "Кластер при 3 хопах: 1.19 мс против 5.40 мс у цепочки с 11 хопами."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=8.5, style="italic",
             color="#555", wrap=True)
    fig.subplots_adjust(bottom=0.20, top=0.92, left=0.10, right=0.95)
    out = os.path.join(script_dir, "delay_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 4. Джиттер = f(хопы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 6.5))
    plot_dependency(ax, chain, cluster, "jitter",
                    "Средний джиттер (мс)",
                    "Зависимость среднего джиттера от количества хопов",
                    higher_better=False)
    ax.set_ylim(bottom=0)

    caption = (
        "Джиттер (вариация задержки) увеличивается с числом хопов из-за накопления\n"
        "случайных интервалов CSMA/CA backoff и переменной длины очередей.\n"
        "Кластерная топология обеспечивает джиттер 0.015 мс — подходит для приложений реального времени."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=8.5, style="italic",
             color="#555", wrap=True)
    fig.subplots_adjust(bottom=0.20, top=0.92, left=0.10, right=0.95)
    out = os.path.join(script_dir, "jitter_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 5. Пропускная способность vs Задержка (параметрическая)
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 7))

    chain_thr = [r["throughput"] for r in chain]
    chain_del = [r["delay"] for r in chain]
    chain_hops = [r["num_hops"] for r in chain]

    scatter = ax.scatter(chain_del, chain_thr, c=chain_hops, cmap="YlOrRd",
                         s=120, edgecolors="black", linewidth=0.8, zorder=5,
                         vmin=2, vmax=12)

    for i, (d, t, h) in enumerate(zip(chain_del, chain_thr, chain_hops)):
        offset_y = 8 if i % 2 == 0 else -14
        ax.annotate(f"{h} хопов", (d, t), textcoords="offset points",
                    xytext=(14, offset_y), fontsize=7.5, color="#555")

    ax.plot(chain_del, chain_thr, color=CHAIN_COLOR, linewidth=1.2,
            alpha=0.4, linestyle="--", zorder=3)

    if cluster:
        ax.scatter([cluster["delay"]], [cluster["throughput"]],
                   color=CLUSTER_COLOR, marker=CLUSTER_MARKER, s=180,
                   edgecolors="black", linewidth=1.2, zorder=6,
                   label="Кластер (3 хопа, 3 частоты)")
        ax.annotate("Кластер\n3 хопа", (cluster["delay"], cluster["throughput"]),
                    textcoords="offset points", xytext=(-60, -30),
                    fontsize=9, fontweight="bold", color=CLUSTER_COLOR,
                    arrowprops=dict(arrowstyle="->", color=CLUSTER_COLOR, lw=1.5))

    cbar = fig.colorbar(scatter, ax=ax, label="Количество хопов (цепочка)", pad=0.02)
    cbar.ax.tick_params(labelsize=9)

    ax.set_xlabel("Средняя задержка (мс)", fontsize=11)
    ax.set_ylabel("Пропускная способность (Мбит/с)", fontsize=11)
    ax.set_title("Зависимость пропускной способности от задержки",
                 fontsize=13, fontweight="bold", pad=12)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.legend(fontsize=10, loc="lower left")

    ax.annotate("", xy=(0.3, 2.1), xytext=(5.5, 1.35),
                arrowprops=dict(arrowstyle="fancy", color="#2ECC71",
                                alpha=0.3, lw=3))
    ax.text(2.5, 1.85, "Лучше", fontsize=10, color="#2ECC71",
            fontweight="bold", alpha=0.5, rotation=10)

    caption = (
        "Каждая точка — цепочечная топология с разным количеством узлов/хопов.\n"
        "С ростом хопов (тёплые цвета) задержка растёт, а пропускная способность падает.\n"
        "Точка кластера (зелёный ромб) достигает наилучшего соотношения метрик."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=8.5, style="italic",
             color="#555", wrap=True)
    fig.subplots_adjust(bottom=0.18, top=0.92, left=0.10, right=0.92)
    out = os.path.join(script_dir, "throughput_vs_delay.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 6. Радарная диаграмма — нормированное сравнение
    # =========================================================
    chain12 = [r for r in chain if r["num_hops"] == 11]
    if chain12 and cluster:
        chain12 = chain12[0]

        categories = [
            "Пропускная\nспособность",
            "1 / Потери\nпакетов",
            "1 / Задержка",
            "1 / Джиттер",
            "Доля\nдоставленных"
        ]

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

        fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))

        ax.plot(angles, norm_chain, color=CHAIN_COLOR, linewidth=2.2,
                marker=CHAIN_MARKER, markersize=7, label="Цепочка (11 хопов)")
        ax.fill(angles, norm_chain, color=CHAIN_COLOR, alpha=0.12)

        ax.plot(angles, norm_cluster, color=CLUSTER_COLOR, linewidth=2.2,
                marker=CLUSTER_MARKER, markersize=7, label="Кластер (3 хопа)")
        ax.fill(angles, norm_cluster, color=CLUSTER_COLOR, alpha=0.12)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10, linespacing=1.2)
        ax.set_ylim(0, 1.15)
        ax.set_title("Нормированное сравнение производительности\n"
                     "(Цепочка 12 узлов vs Кластер 12 узлов)",
                     fontsize=13, fontweight="bold", pad=25)
        ax.legend(fontsize=10, loc="upper right", bbox_to_anchor=(1.30, 1.15))

        fig.tight_layout(pad=2.0)
        out = os.path.join(script_dir, "radar_comparison.png")
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")

    # =========================================================
    # 7. Сводная панель — 4 графика зависимостей
    # =========================================================
    fig, axes = plt.subplots(2, 2, figsize=(18, 13))
    fig.suptitle(
        "Симуляция Wi-Fi: зависимости метрик от количества хопов\n"
        "Цепочка (один канал, 3\u201312 узлов)  vs  Кластер (3 частотных канала, 12 узлов)\n"
        "802.11n  |  OLSR  |  предлагаемая скорость 2 Мбит/с",
        fontsize=13, fontweight="bold", y=0.98)

    metrics_dash = [
        (axes[0, 0], "throughput", "Пропускная способность (Мбит/с)",
         "Пропускная способность = f(хопы)", True),
        (axes[0, 1], "packet_loss", "Потери пакетов (%)",
         "Потери пакетов = f(хопы)", False),
        (axes[1, 0], "delay", "Средняя задержка (мс)",
         "Средняя задержка = f(хопы)", False),
        (axes[1, 1], "jitter", "Средний джиттер (мс)",
         "Средний джиттер = f(хопы)", False),
    ]

    for ax, key, ylabel, title, hb in metrics_dash:
        plot_dependency(ax, chain, cluster, key, ylabel, title,
                        higher_better=hb, show_legend=False, compact=True)
        ax.set_ylim(bottom=0 if key != "packet_loss" else -1)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2,
               fontsize=11, bbox_to_anchor=(0.5, 0.02), framealpha=0.9)

    if chain12 and cluster:
        summary = (
            f"При 12 узлах: Цепочка (11 хопов) vs Кластер (3 хопа)  —  "
            f"Пропускн.: {chain12['throughput']:.2f} vs {cluster['throughput']:.2f} Мбит/с  |  "
            f"Потери: {chain12['packet_loss']:.1f}% vs {cluster['packet_loss']:.3f}%  |  "
            f"Задержка: {chain12['delay']:.1f} vs {cluster['delay']:.1f} мс"
        )
        fig.text(0.5, 0.06, summary, ha="center", fontsize=9.5,
                 fontweight="bold", color="#333",
                 bbox=dict(boxstyle="round,pad=0.4",
                           facecolor="#F0F0F0", alpha=0.9))

    fig.tight_layout(rect=[0.02, 0.09, 0.98, 0.92])
    fig.subplots_adjust(hspace=0.35, wspace=0.30)
    out = os.path.join(script_dir, "dashboard_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 8. Доставленные vs потерянные пакеты (area)
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 6.5))

    hops = [r["num_hops"] for r in chain]
    delivered = [r["rx_packets"] for r in chain]
    lost = [r["tx_packets"] - r["rx_packets"] for r in chain]

    ax.fill_between(hops, 0, delivered, alpha=0.4, color="#2ECC71",
                    label="Доставленные пакеты", zorder=3)
    ax.fill_between(hops, delivered,
                    [d + l for d, l in zip(delivered, lost)],
                    alpha=0.4, color="#E74C3C", label="Потерянные пакеты", zorder=3)

    ax.plot(hops, delivered, color="#27AE60", linewidth=2, marker="o",
            markersize=5, zorder=5)
    ax.plot(hops, [d + l for d, l in zip(delivered, lost)],
            color="#C0392B", linewidth=2, marker="s", markersize=5,
            zorder=5, label="Всего отправлено (Tx)")

    if cluster:
        ax.scatter([cluster["num_hops"]], [cluster["rx_packets"]],
                   color=CLUSTER_COLOR, marker=CLUSTER_MARKER, s=140,
                   edgecolors="black", linewidth=1.2, zorder=7,
                   label=f"Кластер Rx ({cluster['rx_packets']})")

    for h, d, l in zip(hops, delivered, lost):
        if l > 500:
            ax.annotate(f"потеряно: {l}", (h, d + l),
                        textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=7,
                        color="#C0392B", fontweight="bold")

    ax.set_xlabel("Количество хопов", fontsize=11)
    ax.set_ylabel("Пакеты", fontsize=11)
    ax.set_title("Зависимость доставленных и потерянных пакетов от количества хопов",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(hops)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc="best", framealpha=0.9)

    caption = (
        "Зелёная область — успешно доставленные пакеты. Красная область — потерянные.\n"
        "С увеличением хопов зона потерь расширяется из-за кумулятивной вероятности коллизий."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=8.5, style="italic",
             color="#555", wrap=True)
    fig.subplots_adjust(bottom=0.18, top=0.92, left=0.10, right=0.95)
    out = os.path.join(script_dir, "load_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 9. КПД канала (эффективность использования полосы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 6.5))

    offered = float(offeredRate.replace("Mbps", "")) if "offeredRate" in dir() else 2.0
    offered = 2.0
    chain_eff = [r["throughput"] / offered * 100.0 for r in chain]
    hops = [r["num_hops"] for r in chain]

    bars = ax.bar(hops, chain_eff, width=0.6, color=CHAIN_COLOR, alpha=0.75,
                  edgecolor="#C0392B", linewidth=1.2, label="Цепочка", zorder=4)

    for bar, eff in zip(bars, chain_eff):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                f"{eff:.1f}%", ha="center", fontsize=8, fontweight="bold",
                color=CHAIN_COLOR)

    if cluster:
        cl_eff = cluster["throughput"] / offered * 100.0
        cl_bar = ax.bar([cluster["num_hops"] + 0.7], [cl_eff], width=0.6,
                        color=CLUSTER_COLOR, alpha=0.75, edgecolor="#27AE60",
                        linewidth=1.2, label="Кластер", zorder=4)
        ax.text(cluster["num_hops"] + 0.7, cl_eff + 1.2,
                f"{cl_eff:.1f}%", ha="center", fontsize=8, fontweight="bold",
                color=CLUSTER_COLOR)

    ax.axhline(y=100, color="#333", linestyle=":", linewidth=1.5, alpha=0.5,
               label="Идеальная эффективность (100%)")
    ax.set_xlabel("Количество хопов", fontsize=11)
    ax.set_ylabel("КПД канала (%)", fontsize=11)
    ax.set_title("Эффективность использования канала (throughput / offered rate)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_ylim(0, 115)
    ax.set_xticks(hops)
    ax.grid(True, alpha=0.3, linestyle="--", axis="y")
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9)

    caption = (
        "КПД канала показывает, какая доля предлагаемой скорости (2 Мбит/с) реально доставляется.\n"
        "При 11 хопах эффективность цепочки падает до 49%, кластер сохраняет 98%."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=8.5, style="italic",
             color="#555")
    fig.subplots_adjust(bottom=0.18, top=0.92, left=0.10, right=0.95)
    out = os.path.join(script_dir, "efficiency_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 10. Задержка на хоп (нормированная)
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 6.5))

    delay_per_hop = [r["delay"] / r["num_hops"] for r in chain]

    ax.plot(hops, delay_per_hop, color=CHAIN_COLOR, marker=CHAIN_MARKER,
            markersize=7, linewidth=2.2, label="Цепочка: задержка / хоп", zorder=5)
    ax.fill_between(hops, delay_per_hop, alpha=0.15, color=CHAIN_COLOR, zorder=3)

    for i, (h, d) in enumerate(zip(hops, delay_per_hop)):
        if i % 2 == 0:
            ax.annotate(f"{d:.3f}", (h, d), textcoords="offset points",
                        xytext=(0, 12), ha="center", fontsize=7.5,
                        color=CHAIN_COLOR, fontweight="bold")

    if cluster:
        cl_dph = cluster["delay"] / cluster["num_hops"]
        ax.plot(cluster["num_hops"], cl_dph, color=CLUSTER_COLOR,
                marker=CLUSTER_MARKER, markersize=10, zorder=6,
                label=f"Кластер: {cl_dph:.3f} мс/хоп")
        ax.axhline(y=cl_dph, color=CLUSTER_COLOR, linestyle="--",
                   linewidth=1.5, alpha=0.6)

    ax.set_xlabel("Количество хопов", fontsize=11)
    ax.set_ylabel("Задержка на хоп (мс/хоп)", fontsize=11)
    ax.set_title("Нормированная задержка: среднее время на один хоп",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(hops)
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc="best", framealpha=0.9)

    caption = (
        "В идеальной сети задержка на хоп должна быть постоянной. Рост этой метрики\n"
        "свидетельствует о нарастании конкуренции за среду и увеличении времени backoff.\n"
        "Кластер обеспечивает 0.397 мс/хоп — близко к значению цепочки при малом числе хопов."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=8.5, style="italic",
             color="#555")
    fig.subplots_adjust(bottom=0.20, top=0.92, left=0.10, right=0.95)
    out = os.path.join(script_dir, "delay_per_hop.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 11. PDR (Packet Delivery Ratio) = f(хопы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 6.5))

    pdr_chain = [r["rx_packets"] / r["tx_packets"] * 100.0 for r in chain]

    ax.plot(hops, pdr_chain, color=CHAIN_COLOR, marker=CHAIN_MARKER,
            markersize=7, linewidth=2.2, label="Цепочка (PDR)", zorder=5)
    ax.fill_between(hops, pdr_chain, 100, alpha=0.12, color="#E74C3C",
                    label="Зона потерь", zorder=2)
    ax.fill_between(hops, 0, pdr_chain, alpha=0.12, color="#2ECC71",
                    label="Зона доставки", zorder=2)

    for i, (h, p) in enumerate(zip(hops, pdr_chain)):
        ax.annotate(f"{p:.1f}%", (h, p), textcoords="offset points",
                    xytext=(0, -16 if i % 2 == 0 else 10),
                    ha="center", fontsize=7.5, color=CHAIN_COLOR, fontweight="bold")

    if cluster:
        cl_pdr = cluster["rx_packets"] / cluster["tx_packets"] * 100.0
        ax.plot(cluster["num_hops"], cl_pdr, color=CLUSTER_COLOR,
                marker=CLUSTER_MARKER, markersize=10, zorder=6,
                label=f"Кластер (PDR = {cl_pdr:.2f}%)")

    ax.axhline(y=95, color="#F39C12", linestyle=":", linewidth=1.5, alpha=0.7)
    ax.text(hops[-1], 95.5, "Порог надёжной доставки (95%)",
            fontsize=8, color="#F39C12", ha="right")

    ax.set_xlabel("Количество хопов", fontsize=11)
    ax.set_ylabel("Доля доставленных пакетов, PDR (%)", fontsize=11)
    ax.set_title("Коэффициент доставки пакетов (Packet Delivery Ratio)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(hops)
    ax.set_ylim(50, 102)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc="lower left", framealpha=0.9)

    caption = (
        "PDR — ключевой показатель надёжности сети. При превышении 5–6 хопов PDR цепочки\n"
        "опускается ниже 95%, что неприемлемо для большинства приложений.\n"
        "Кластер с PDR 99.97% гарантирует практически безошибочную доставку."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=8.5, style="italic",
             color="#555")
    fig.subplots_adjust(bottom=0.20, top=0.92, left=0.10, right=0.95)
    out = os.path.join(script_dir, "pdr_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 12. Скорость деградации метрик (производные)
    # =========================================================
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.suptitle(
        "Скорость деградации метрик: приращение на каждый дополнительный хоп",
        fontsize=14, fontweight="bold", y=0.98)

    metrics_deriv = [
        ("throughput", "ΔПропускная способность (Мбит/с)", "#E74C3C", "Деградация пропускной способности"),
        ("packet_loss", "ΔПотери пакетов (%)", "#E67E22", "Прирост потерь пакетов"),
        ("delay", "ΔЗадержка (мс)", "#3498DB", "Прирост задержки"),
        ("jitter", "ΔДжиттер (мс)", "#9B59B6", "Прирост джиттера"),
    ]

    for idx, (key, ylabel, color, title) in enumerate(metrics_deriv):
        ax = axes[idx // 2][idx % 2]
        vals = [r[key] for r in chain]
        deltas = [vals[i+1] - vals[i] for i in range(len(vals)-1)]
        mid_hops = [(hops[i] + hops[i+1]) / 2 for i in range(len(hops)-1)]

        ax.bar(mid_hops, deltas, width=0.7, color=color, alpha=0.7,
               edgecolor=color, linewidth=1.2, zorder=4)

        for mh, d in zip(mid_hops, deltas):
            sign = "+" if d > 0 else ""
            ax.text(mh, d + (0.003 if abs(d) < 0.1 else abs(d) * 0.08),
                    f"{sign}{d:.3f}", ha="center", fontsize=7,
                    color=color, fontweight="bold")

        ax.axhline(y=0, color="#333", linewidth=0.8)
        ax.set_xlabel("Хопы (середина интервала)", fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.3, linestyle="--", axis="y")
        ax.set_axisbelow(True)

    fig.tight_layout(rect=[0.02, 0.02, 0.98, 0.93])
    fig.subplots_adjust(hspace=0.35, wspace=0.30)
    out = os.path.join(script_dir, "degradation_rate.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 13. Столбчатая диаграмма: chain(12) vs cluster(12)
    # =========================================================
    if chain12 and cluster:
        fig, axes = plt.subplots(1, 4, figsize=(18, 6))
        fig.suptitle(
            "Прямое сравнение: Цепочка (12 узлов, 11 хопов) vs Кластер (12 узлов, 3 хопа)",
            fontsize=14, fontweight="bold", y=1.02)

        bar_data = [
            ("Пропускная\nспособность\n(Мбит/с)", chain12["throughput"], cluster["throughput"], True),
            ("Потери\nпакетов\n(%)", chain12["packet_loss"], cluster["packet_loss"], False),
            ("Средняя\nзадержка\n(мс)", chain12["delay"], cluster["delay"], False),
            ("Средний\nджиттер\n(мс)", chain12["jitter"], cluster["jitter"], False),
        ]

        for ax, (label, c_val, cl_val, higher_better) in zip(axes, bar_data):
            x = [0, 1]
            vals = [c_val, cl_val]
            colors = [CHAIN_COLOR, CLUSTER_COLOR]

            bars = ax.bar(x, vals, width=0.55, color=colors, alpha=0.8,
                          edgecolor=["#C0392B", "#27AE60"], linewidth=1.5, zorder=4)

            for bar, v in zip(bars, vals):
                fmt = f"{v:.4f}" if v < 0.1 else (f"{v:.2f}" if v < 10 else f"{v:.1f}")
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.05,
                        fmt, ha="center", fontsize=10, fontweight="bold")

            if higher_better:
                winner = 1 if cl_val > c_val else 0
            else:
                winner = 1 if cl_val < c_val else 0
            bars[winner].set_edgecolor("#FFD700")
            bars[winner].set_linewidth(3)

            ratio = max(c_val, cl_val) / max(min(c_val, cl_val), 0.0001)
            ax.text(0.5, -0.18, f"Разница: ×{ratio:.1f}",
                    transform=ax.transAxes, ha="center", fontsize=9,
                    fontweight="bold", color="#555")

            ax.set_xticks(x)
            ax.set_xticklabels(["Цепочка", "Кластер"], fontsize=10)
            ax.set_title(label, fontsize=11, fontweight="bold")
            ax.set_ylim(bottom=0)
            ax.grid(True, alpha=0.3, linestyle="--", axis="y")
            ax.set_axisbelow(True)

        fig.tight_layout(rect=[0, 0.05, 1, 0.95])
        out = os.path.join(script_dir, "bar_comparison.png")
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")

    # =========================================================
    # 14. Тепловая карта корреляции метрик (цепочка)
    # =========================================================
    fig, ax = plt.subplots(figsize=(9, 8))

    metric_names = ["Хопы", "Пропускн.", "Потери %", "Задержка", "Джиттер", "PDR %"]
    data_matrix = []
    for r in chain:
        pdr = r["rx_packets"] / r["tx_packets"] * 100.0
        data_matrix.append([r["num_hops"], r["throughput"], r["packet_loss"],
                            r["delay"], r["jitter"], pdr])

    data_np = np.array(data_matrix)
    n_metrics = len(metric_names)
    corr = np.corrcoef(data_np.T)

    im = ax.imshow(corr, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    cbar = fig.colorbar(im, ax=ax, label="Коэффициент корреляции Пирсона", pad=0.02)

    ax.set_xticks(range(n_metrics))
    ax.set_yticks(range(n_metrics))
    ax.set_xticklabels(metric_names, fontsize=10, rotation=45, ha="right")
    ax.set_yticklabels(metric_names, fontsize=10)

    for i in range(n_metrics):
        for j in range(n_metrics):
            val = corr[i, j]
            color = "white" if abs(val) > 0.6 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=9, fontweight="bold", color=color)

    ax.set_title("Корреляционная матрица метрик (цепочечная топология)",
                 fontsize=13, fontweight="bold", pad=15)

    caption = (
        "Матрица корреляции Пирсона показывает линейную зависимость между метриками.\n"
        "Пропускная способность и PDR имеют сильную отрицательную корреляцию с числом хопов,\n"
        "задержка, джиттер и потери — сильную положительную корреляцию."
    )
    fig.text(0.5, 0.01, caption, ha="center", fontsize=8.5, style="italic",
             color="#555")
    fig.subplots_adjust(bottom=0.18, top=0.92, left=0.15, right=0.95)
    out = os.path.join(script_dir, "correlation_heatmap.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # Сводная таблица
    # =========================================================
    print("\n" + "=" * 80)
    print("  ТАБЛИЦА РЕЗУЛЬТАТОВ")
    print("=" * 80)
    print(f"{'Топология':<12} {'Узлы':>6} {'Хопы':>5} {'Пропускн.':>12} "
          f"{'Потери %':>10} {'Задержка':>10} {'Джиттер':>10}")
    print("-" * 80)

    for r in chain:
        print(f"{'цепочка':<12} {r['num_nodes']:>6} {r['num_hops']:>5} "
              f"{r['throughput']:>12.4f} {r['packet_loss']:>10.4f} "
              f"{r['delay']:>10.4f} {r['jitter']:>10.4f}")

    if cluster:
        print(f"{'кластер':<12} {cluster['num_nodes']:>6} {cluster['num_hops']:>5} "
              f"{cluster['throughput']:>12.4f} {cluster['packet_loss']:>10.4f} "
              f"{cluster['delay']:>10.4f} {cluster['jitter']:>10.4f}")

    print("=" * 80)
    print("Готово. Все графики сохранены.")


if __name__ == "__main__":
    main()
