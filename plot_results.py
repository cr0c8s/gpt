#!/usr/bin/env python3
"""
Симуляция Wi-Fi сети: графики зависимостей Chain vs Cluster.

Читает sweep-results.csv и строит графики зависимостей метрик
от числа хопов для цепочечной и кластерной топологий.

Генерируемые графики:
  1. Пропускная способность = f(хопы)
  2. Потери пакетов = f(хопы)
  3. Задержка = f(хопы)
  4. Джиттер = f(хопы)
  5. Пропускная способность vs Задержка (параметрическая диаграмма)
  6. Радарная диаграмма нормированного сравнения
  7. Сводная панель (2x2)
  8. Доставленные vs потерянные пакеты (area)
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
    hops = [r["num_hops"] for r in chain_rows]
    vals = [r[metric_key] for r in chain_rows]

    ax.plot(hops, vals, color=CHAIN_COLOR, marker=CHAIN_MARKER, markersize=7,
            linewidth=2.2, label=u"Цепочка (один канал)", zorder=5)

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
                markersize=10, zorder=6, label=u"Кластер (3 частотных канала)")

        fmt = f"{cl_val:.2f}" if cl_val >= 1 else f"{cl_val:.4f}"
        ax.annotate(fmt, (cl_hops, cl_val), textcoords="offset points",
                    xytext=(30, -15), ha="center", fontsize=8.5,
                    color=CLUSTER_COLOR, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=CLUSTER_COLOR,
                                   lw=1.2))

    ax.set_xlabel(u"Количество хопов", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)

    ax.set_xticks(hops)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    direction = u"\u25b2 больше = лучше" if higher_better else u"\u25bc меньше = лучше"
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
    # 1. Пропускная способность = f(хопы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_dependency(ax, chain, cluster, "throughput",
                    u"Пропускная способность (Мбит/с)",
                    u"Зависимость пропускной способности от количества хопов",
                    higher_better=True)
    ax.set_ylim(bottom=0)
    ax.text(0.5, -0.12,
            u"С увеличением числа хопов пропускная способность снижается, т.к. каждый хоп\n"
            u"повторно использует один радиоканал, вызывая конкуренцию и коллизии (CSMA/CA).\n"
            u"Кластерная топология с разделением частот сохраняет близкую к идеальной скорость.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = os.path.join(script_dir, "throughput_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 2. Потери пакетов = f(хопы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_dependency(ax, chain, cluster, "packet_loss",
                    u"Потери пакетов (%)",
                    u"Зависимость потерь пакетов от количества хопов",
                    higher_better=False)
    ax.set_ylim(bottom=-0.5)
    ax.text(0.5, -0.12,
            u"Потери растут с увеличением числа хопов: каждый промежуточный узел вносит\n"
            u"риск коллизий, переполнения очередей и исчерпания попыток передачи.\n"
            u"Кластерная маршрутизация (3 хопа на раздельных частотах) практически устраняет потери.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = os.path.join(script_dir, "packet_loss_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 3. Задержка = f(хопы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_dependency(ax, chain, cluster, "delay",
                    u"Средняя задержка (мс)",
                    u"Зависимость средней задержки от количества хопов",
                    higher_better=False)
    ax.set_ylim(bottom=0)
    ax.text(0.5, -0.12,
            u"Задержка растёт приблизительно линейно с числом хопов. Каждый хоп добавляет\n"
            u"задержку CSMA/CA backoff, передачи кадра и ожидания в очереди (~0.5 мс/хоп).\n"
            u"Кластер при 3 хопах: 1.19 мс против 5.40 мс у цепочки с 11 хопами.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = os.path.join(script_dir, "delay_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 4. Джиттер = f(хопы)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_dependency(ax, chain, cluster, "jitter",
                    u"Средний джиттер (мс)",
                    u"Зависимость среднего джиттера от количества хопов",
                    higher_better=False)
    ax.set_ylim(bottom=0)
    ax.text(0.5, -0.12,
            u"Джиттер (вариация задержки) увеличивается с числом хопов из-за накопления\n"
            u"случайных интервалов CSMA/CA backoff и переменной длины очередей.\n"
            u"Кластерная топология обеспечивает джиттер 0.015 мс — подходит для приложений реального времени.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = os.path.join(script_dir, "jitter_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # =========================================================
    # 5. Пропускная способность vs Задержка (параметрическая)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))

    chain_thr = [r["throughput"] for r in chain]
    chain_del = [r["delay"] for r in chain]
    chain_hops = [r["num_hops"] for r in chain]

    scatter = ax.scatter(chain_del, chain_thr, c=chain_hops, cmap="YlOrRd",
                         s=120, edgecolors="black", linewidth=0.8, zorder=5,
                         vmin=2, vmax=12)

    for d, t, h in zip(chain_del, chain_thr, chain_hops):
        ax.annotate(f"{h} хопов", (d, t), textcoords="offset points",
                    xytext=(12, 5), fontsize=8, color="#555")

    ax.plot(chain_del, chain_thr, color=CHAIN_COLOR, linewidth=1.2,
            alpha=0.4, linestyle="--", zorder=3)

    if cluster:
        ax.scatter([cluster["delay"]], [cluster["throughput"]],
                   color=CLUSTER_COLOR, marker=CLUSTER_MARKER, s=180,
                   edgecolors="black", linewidth=1.2, zorder=6,
                   label=u"Кластер (3 хопа, 3 частоты)")
        ax.annotate(u"Кластер\n3 хопа", (cluster["delay"], cluster["throughput"]),
                    textcoords="offset points", xytext=(-55, -25),
                    fontsize=9, fontweight="bold", color=CLUSTER_COLOR,
                    arrowprops=dict(arrowstyle="->", color=CLUSTER_COLOR, lw=1.5))

    cbar = fig.colorbar(scatter, ax=ax, label=u"Количество хопов (цепочка)", pad=0.02)
    cbar.ax.tick_params(labelsize=9)

    ax.set_xlabel(u"Средняя задержка (мс)", fontsize=11)
    ax.set_ylabel(u"Пропускная способность (Мбит/с)", fontsize=11)
    ax.set_title(u"Зависимость пропускной способности от задержки",
                 fontsize=13, fontweight="bold", pad=10)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(fontsize=10, loc="lower left")

    ax.annotate("", xy=(0.3, 2.1), xytext=(5.5, 1.35),
                arrowprops=dict(arrowstyle="fancy", color="#2ECC71",
                                alpha=0.3, lw=3))
    ax.text(2.5, 1.85, u"Лучше", fontsize=10, color="#2ECC71",
            fontweight="bold", alpha=0.5, rotation=10)

    ax.text(0.5, -0.1,
            u"Каждая точка — цепочечная топология с разным количеством узлов/хопов.\n"
            u"С ростом хопов (тёплые цвета) задержка растёт, а пропускная способность падает.\n"
            u"Точка кластера (зелёный ромб) достигает наилучшего соотношения метрик.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")

    fig.tight_layout(rect=[0, 0.05, 1, 1])
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
            u"Пропускная\nспособность",
            u"1 / Потери\nпакетов",
            u"1 / Задержка",
            u"1 / Джиттер",
            u"Доля\nдоставленных"
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

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

        ax.plot(angles, norm_chain, color=CHAIN_COLOR, linewidth=2.2,
                marker=CHAIN_MARKER, markersize=7, label=u"Цепочка (11 хопов)")
        ax.fill(angles, norm_chain, color=CHAIN_COLOR, alpha=0.12)

        ax.plot(angles, norm_cluster, color=CLUSTER_COLOR, linewidth=2.2,
                marker=CLUSTER_MARKER, markersize=7, label=u"Кластер (3 хопа)")
        ax.fill(angles, norm_cluster, color=CLUSTER_COLOR, alpha=0.12)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylim(0, 1.15)
        ax.set_title(u"Нормированное сравнение производительности\n"
                     u"(Цепочка 12 узлов vs Кластер 12 узлов)",
                     fontsize=13, fontweight="bold", pad=20)
        ax.legend(fontsize=10, loc="upper right", bbox_to_anchor=(1.25, 1.12))

        fig.tight_layout()
        out = os.path.join(script_dir, "radar_comparison.png")
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")

    # =========================================================
    # 7. Сводная панель — 4 графика зависимостей
    # =========================================================
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.suptitle(
        u"Симуляция Wi-Fi: зависимости метрик от количества хопов\n"
        u"Цепочка (один канал, 3\u201312 узлов)  vs  Кластер (3 частотных канала, 12 узлов)\n"
        u"802.11n  |  OLSR  |  предлагаемая скорость 2 Мбит/с",
        fontsize=14, fontweight="bold", y=0.99)

    metrics_dash = [
        (axes[0, 0], "throughput", u"Пропускная способность (Мбит/с)",
         u"Пропускная способность = f(хопы)", True),
        (axes[0, 1], "packet_loss", u"Потери пакетов (%)",
         u"Потери пакетов = f(хопы)", False),
        (axes[1, 0], "delay", u"Средняя задержка (мс)",
         u"Средняя задержка = f(хопы)", False),
        (axes[1, 1], "jitter", u"Средний джиттер (мс)",
         u"Средний джиттер = f(хопы)", False),
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
            u"При 12 узлах: Цепочка (11 хопов) vs Кластер (3 хопа)  \u2014  "
            f"Пропускная способность: {chain12['throughput']:.2f} vs {cluster['throughput']:.2f} Мбит/с  |  "
            f"Потери: {chain12['packet_loss']:.1f}% vs {cluster['packet_loss']:.3f}%  |  "
            f"Задержка: {chain12['delay']:.1f} vs {cluster['delay']:.1f} мс")
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
    # 8. Доставленные vs потерянные пакеты (area)
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 6))

    hops = [r["num_hops"] for r in chain]
    delivered = [r["rx_packets"] for r in chain]
    lost = [r["tx_packets"] - r["rx_packets"] for r in chain]

    ax.fill_between(hops, 0, delivered, alpha=0.4, color="#2ECC71",
                    label=u"Доставленные пакеты", zorder=3)
    ax.fill_between(hops, delivered,
                    [d + l for d, l in zip(delivered, lost)],
                    alpha=0.4, color="#E74C3C", label=u"Потерянные пакеты", zorder=3)

    ax.plot(hops, delivered, color="#27AE60", linewidth=2, marker="o",
            markersize=6, zorder=5)
    ax.plot(hops, [d + l for d, l in zip(delivered, lost)],
            color="#C0392B", linewidth=2, marker="s", markersize=6,
            zorder=5, label=u"Всего отправлено (Tx)")

    if cluster:
        ax.scatter([cluster["num_hops"]], [cluster["rx_packets"]],
                   color=CLUSTER_COLOR, marker=CLUSTER_MARKER, s=160,
                   edgecolors="black", linewidth=1.2, zorder=7,
                   label=u"Кластер Rx ({})".format(cluster["rx_packets"]))

    for h, d, l in zip(hops, delivered, lost):
        if l > 200:
            ax.annotate(u"потеряно: {}".format(l), (h, d + l),
                        textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=7.5,
                        color="#C0392B", fontweight="bold")

    ax.set_xlabel(u"Количество хопов", fontsize=11)
    ax.set_ylabel(u"Пакеты", fontsize=11)
    ax.set_title(u"Зависимость доставленных и потерянных пакетов от количества хопов",
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_xticks(hops)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc="best")

    ax.text(0.5, -0.1,
            u"Зелёная область — успешно доставленные пакеты. Красная область — потерянные.\n"
            u"С увеличением хопов зона потерь расширяется из-за кумулятивной вероятности коллизий.",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic",
            color="#555")

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    out = os.path.join(script_dir, "load_comparison.png")
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
