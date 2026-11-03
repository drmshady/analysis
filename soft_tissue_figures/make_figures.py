"""Figures for Tables 1-7 of 'Statistical Methodology and Results'
(2D vs 3D soft-tissue prediction, Dolphin 3D).

All values are transcribed from the tables in the manuscript; no raw
patient-level prediction errors are needed. Run:  python make_figures.py
Outputs 300-dpi PNG + vector PDF for each figure into ./figures/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)

# Style matched to the existing Figures 1-2 of the manuscript
C2D, C3D = "#2a78d6", "#e8683f"
INK, MUTED, GRID = "#222222", "#5b5b5b", "#e3e3e3"
plt.rcParams.update({
    "font.family": "Inter", "font.size": 10, "text.color": INK,
    "axes.edgecolor": "#444444", "axes.labelcolor": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 11, "axes.titleweight": "medium",
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.8,
    "legend.frameon": False, "savefig.dpi": 300, "savefig.bbox": "tight",
})

LM = ["Upper lip", "Lower lip", "Soft-tissue\npogonion"]
LM4 = LM + ["Overall\n(patient mean)"]


def save(fig, name):
    fig.savefig(OUT / f"{name}.png")
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)


def method_legend(fig, y=1.02, extra=()):
    h = [Patch(color=C2D, label="2D planning"), Patch(color=C3D, label="3D planning"), *extra]
    fig.legend(handles=h, loc="upper center", ncol=len(h), bbox_to_anchor=(0.5, y))


def p_txt(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


# ---------------------------------------------------------------- Table 1
def fig_table1():
    pts = [f"P{i:02d}" for i in range(1, 11)]
    sex = ["F", "F", "F", "M", "F", "F", "M", "M", "M", "F"]
    age = [19, 18, 18, 20, 21, 19, 20, 39, 22, 21]
    mx = [6, 8, 5, 5, 6, 10, 6, 10, 6, 6]
    md = [4, 4, 9, 7, 6, 3, 4, 0, 4, 4]       # 0 = not performed
    gn = [4, 6, 0, 4, 5, 0, 6, 0, 4, 5]
    series = [("Maxillary advancement", mx, "#2a78d6", "6.8 ± 1.9 mm (n = 10)"),
              ("Mandibular setback", md, "#e8683f", "5.0 ± 1.9 mm (n = 9)"),
              ("Genioplasty advancement", gn, "#3fa66b", "4.9 ± 0.9 mm (n = 7)")]

    fig, ax = plt.subplots(figsize=(10, 4.2))
    x = np.arange(10)
    w = 0.26
    for k, (lab, v, c, summ) in enumerate(series):
        xs = x + (k - 1) * w
        v = np.array(v, float)
        ax.bar(xs[v > 0], v[v > 0], w * 0.92, color=c, label=f"{lab}  ·  {summ}", zorder=3)
        for xi in xs[v == 0]:
            ax.text(xi, 0.15, "—", ha="center", va="bottom", color=MUTED, fontsize=9)
    ax.set_xticks(x, [f"{p}\n{s}, {a} y" for p, s, a in zip(pts, sex, age)], fontsize=9)
    ax.set_ylabel("Planned movement (mm)")
    ax.set_ylim(0, 11)
    ax.yaxis.grid(True, zorder=0)
    ax.tick_params(axis="x", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3, fontsize=9,
              handlelength=1.2)
    ax.text(1.0, -0.2, "Sex: F 6 / M 4  ·  Age 21.7 ± 6.2 y (18–39)  ·  — = movement not performed",
            transform=ax.transAxes, ha="right", fontsize=8.5, color=MUTED)
    save(fig, "Figure_T1_patient_characteristics")


# ---------------------------------------------------------------- Table 2
def fig_table2():
    # mean, ci_lo, ci_hi, median, q1, q3, min, max
    d2 = [(3.00, 2.14, 3.85, 2.95, 2.63, 3.34, 1.10, 5.50),
          (4.43, 2.96, 5.90, 4.85, 3.58, 5.63, 0.00, 7.30),
          (4.89, 2.07, 7.71, 4.90, 1.65, 6.15, 0.00, 12.10),
          (4.11, 2.69, 5.52, 4.11, 2.97, 5.68, 0.87, 6.97)]
    d3 = [(1.63, 1.08, 2.18, 1.85, 1.28, 2.04, 0.00, 2.68),
          (2.33, 0.66, 3.99, 1.52, 0.84, 3.47, 0.00, 6.59),
          (4.90, 1.47, 8.34, 3.87, 0.65, 8.31, 0.00, 12.09),
          (2.95, 1.23, 4.67, 2.50, 0.95, 5.21, 0.00, 6.30)]
    sd2 = [1.20, 2.06, 3.94, 1.98]
    sd3 = [0.77, 2.33, 4.80, 2.40]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    x = np.arange(4)
    for off, d, sds, c in [(-0.17, d2, sd2, C2D), (0.17, d3, sd3, C3D)]:
        for i, (m, lo, hi, med, q1, q3, mn, mxv) in enumerate(d):
            xi = x[i] + off
            ax.vlines(xi, mn, mxv, color=c, lw=1, alpha=0.45, zorder=2)            # range
            ax.add_patch(plt.Rectangle((xi - 0.075, q1), 0.15, q3 - q1, fc=c,
                                       alpha=0.18, ec=c, lw=0.8, zorder=2))           # IQR
            ax.hlines(med, xi - 0.075, xi + 0.075, color=c, lw=1.2, zorder=3)        # median
            ax.vlines(xi, lo, hi, color=c, lw=2.6, zorder=4)                          # 95% CI
            ax.plot(xi, m, "o", ms=7, mfc=c, mec="white", mew=1.2, zorder=5)       # mean
            ax.text(xi + 0.03, mxv + 0.25, f"{m:.2f}\n±{sds[i]:.2f}", ha="center",
                    va="bottom", fontsize=7.5, color=c, linespacing=0.95)
    ax.axhline(2, ls="--", color="#444", lw=1, zorder=1)
    ax.text(3.55, 2, "2 mm", va="center", fontsize=8.5, color=MUTED)
    ax.axvline(2.5, color=GRID, lw=1)
    ax.set_xticks(x, LM4)
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylim(-0.3, 14.5)
    ax.set_ylabel("Prediction error (mm)")
    ax.yaxis.grid(True, zorder=0)
    ax.tick_params(axis="x", length=0)
    key = [Line2D([], [], marker="o", ls="", mfc="#777", mec="white", ms=7, label="Mean"),
           Line2D([], [], color="#777", lw=2.6, label="95% CI"),
           Patch(fc="#777", alpha=0.25, ec="#777", label="Median (IQR)"),
           Line2D([], [], color="#777", lw=1, alpha=0.6, label="Min–max")]
    method_legend(fig, y=0.99, extra=key)
    save(fig, "Figure_T2_descriptive_prediction_error")


# ---------------------------------------------------------------- Table 3
def fig_table3():
    rows = [  # mean diff, lo, hi, p, holm, wilcoxon, dz
        ("Upper lip", 1.37, 0.40, 2.34, 0.011, 0.022, 0.010, 1.01),
        ("Lower lip", 2.10, 1.05, 3.16, 0.001, 0.004, 0.008, 1.43),
        ("Soft-tissue pogonion", -0.01, -3.93, 3.90, 0.994, 0.994, 0.910, 0.00),
        ("Overall (patient mean)", 1.15, -0.45, 2.76, 0.139, None, 0.084, 0.51),
    ]
    fig, ax = plt.subplots(figsize=(10, 3.6))
    y = np.arange(len(rows))[::-1]
    for yi, (lab, m, lo, hi, p, holm, wx, dz) in zip(y, rows):
        sig = p < 0.05
        c = C3D if sig else "#8a8a8a"
        ax.hlines(yi, lo, hi, color=c, lw=2.4)
        ax.plot(m, yi, "D" if lab.startswith("Overall") else "o", ms=8, mfc=c,
                mec="white", mew=1.2, zorder=3)
        ax.text(4.8, yi, f"{m:.2f} ({lo:.2f} to {hi:.2f})".replace("-", "\u2212"), va="center", fontsize=9)
        ax.text(7.9, yi, f"{p:.3f}{'*' if sig else ''}", va="center", fontsize=9,
                fontweight="bold" if sig else "normal")
        ax.text(9.1, yi, "—" if holm is None else f"{holm:.3f}{'*' if holm < .05 else ''}",
                va="center", fontsize=9, fontweight="bold" if holm and holm < .05 else "normal")
        ax.text(10.3, yi, f"{dz:.2f}", va="center", fontsize=9)
    hy = len(rows) - 0.35
    for xh, t in [(4.8, "Mean diff. (95% CI), mm"), (7.9, "p"), (9.1, "Holm p"), (10.3, "dz")]:
        ax.text(xh, hy, t, fontsize=9, fontweight="semibold", color=MUTED)
    ax.axvline(0, color="#444", lw=1)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(-4.5, 10.9)
    ax.set_ylim(-0.6, len(rows) - 0.1)
    ax.set_xticks(np.arange(-4, 5, 1))
    ax.spines["bottom"].set_bounds(-4, 4)
    ax.xaxis.grid(True)
    ax.set_xlabel("Mean difference, 2D − 3D (mm)", x=0.31)
    ax.text(-0.15, hy, "◀ 2D more accurate", ha="right", fontsize=8.5, color=MUTED)
    ax.text(0.15, hy, "3D more accurate ▶", ha="left", fontsize=8.5, color=MUTED)
    ax.text(1.0, -0.2, "*p < 0.05 (paired t-test)", transform=ax.transAxes, ha="right",
            fontsize=8, color=MUTED)
    save(fig, "Figure_T3_mean_difference_forest")


# ---------------------------------------------------------------- Table 4
def fig_table4():
    r = [0.10, 0.78, 0.23, 0.49]
    pr = [0.773, 0.008, 0.529, 0.151]
    rho = [0.05, 0.92, 0.51, 0.47]
    prho = [0.881, 0.0005, 0.132, 0.174]
    _corr_bars(LM4, r, pr, rho, prho, ("Pearson r", "Spearman ρ"), ("#2a78d6", "#8fb8ea"),
               "Correlation coefficient (2D vs 3D error)", "Figure_T4_correlation_2D_3D",
               sep_after=2)


def _corr_bars(labels, a, pa, b, pb, names, cols, ylab, fname, sep_after=None):
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    x = np.arange(len(labels))
    w = 0.34
    ax.axhspan(0, 0.3, color="#f4f4f4", zorder=0)
    ax.axhspan(0.3, 0.7, color="#ebebeb", zorder=0)
    ax.axhspan(0.7, 1.0, color="#e0e0e0", zorder=0)
    for yb, t in [(0.15, "Weak"), (0.5, "Moderate"), (0.85, "Strong")]:
        ax.text(1.01, yb, t, va="center", ha="left", fontsize=8, color=MUTED,
                style="italic", transform=ax.get_yaxis_transform())
    for k, (vals, ps, name, c) in enumerate([(a, pa, names[0], cols[0]), (b, pb, names[1], cols[1])]):
        xs = x + (k - 0.5) * w
        ax.bar(xs, vals, w * 0.92, color=c, label=name, zorder=3)
        for xi, v, p in zip(xs, vals, ps):
            ax.text(xi, v + 0.02, f"{v:.2f}{'*' if p < 0.05 else ''}\n{p_txt(p)}", ha="center",
                    va="bottom", fontsize=7.5, fontweight="bold" if p < 0.05 else "normal",
                    linespacing=1.0)
    if sep_after is not None:
        ax.axvline(sep_after + 0.5, color="white", lw=2, zorder=1)
    ax.set_xticks(x, labels)
    ax.set_xlim(-0.55, len(labels) - 0.45)
    ax.set_ylim(0, 1.1)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_ylabel(ylab)
    ax.tick_params(axis="x", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2)
    ax.text(1.0, -0.17, "*p < 0.05", transform=ax.transAxes, ha="right", fontsize=8, color=MUTED)
    save(fig, fname)


# ---------------------------------------------------------------- Table 5
def fig_table5():
    n2 = [2, 1, 3, 6]
    n3 = [7, 6, 5, 18]
    N = [10, 10, 10, 30]
    pm = [0.125, 0.063, 0.625, None]
    labels = LM + ["All predictions†\n(pooled, n = 30)"]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    x = np.arange(4)
    w = 0.34
    for k, (vals, c) in enumerate([(n2, C2D), (n3, C3D)]):
        xs = x + (k - 0.5) * w
        pct = [100 * v / n for v, n in zip(vals, N)]
        ax.bar(xs, pct, w * 0.92, color=c, zorder=3)
        for xi, pc, v, n in zip(xs, pct, vals, N):
            ax.text(xi, pc + 1.5, f"{pc:.0f}%\n{v}/{n}", ha="center", va="bottom", fontsize=8,
                    linespacing=1.0)
    for xi, p in zip(x, pm):
        ax.text(xi, 92, "McNemar\n" + (f"p = {p:.3f}" if p else "not tested"), ha="center",
                va="center", fontsize=8, color=MUTED, linespacing=1.1)
    ax.axvline(2.5, color=GRID, lw=1)
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Predictions within ≤ 2 mm (%)")
    ax.yaxis.grid(True, zorder=0)
    ax.tick_params(axis="x", length=0)
    method_legend(fig, y=1.04)
    ax.text(1.0, -0.2, "†Descriptive only: the three landmarks of a patient are not independent.",
            transform=ax.transAxes, ha="right", fontsize=8, color=MUTED)
    save(fig, "Figure_T5_clinical_acceptability")


# ---------------------------------------------------------------- Table 6
def fig_table6():
    med = {"2D": [(2.95, 2.63, 3.34), (4.85, 3.58, 5.63), (4.90, 1.65, 6.15)],
           "3D": [(1.85, 1.28, 2.04), (1.52, 0.84, 3.47), (3.87, 0.65, 8.31)]}
    fr = {"2D": (4.67, 0.097), "3D": (5.71, 0.058)}
    pw = {"2D": [0.146, 0.697, 1.000], "3D": [1.000, 0.223, 0.070]}  # UL-LL, UL-Pog, LL-Pog
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, m, c in zip(axes, ["2D", "3D"], [C2D, C3D]):
        x = np.arange(3)
        for xi, (md, q1, q3) in zip(x, med[m]):
            ax.add_patch(plt.Rectangle((xi - 0.22, q1), 0.44, q3 - q1, fc=c, alpha=0.22,
                                       ec=c, lw=1, zorder=2))
            ax.hlines(md, xi - 0.22, xi + 0.22, color=c, lw=2.5, zorder=3)
            ax.text(xi + 0.27, md, f"{md:.2f}", va="center", fontsize=8.5, color=c)
        # pairwise brackets
        pairs = [(0, 1), (0, 2), (1, 2)]
        ys = [9.6, 11.4, 10.5]
        for (i, j), yb, p in zip(pairs, ys, pw[m]):
            ax.plot([i, i, j, j], [yb - 0.2, yb, yb, yb - 0.2], color="#888", lw=0.8)
            ax.text((i + j) / 2, yb + 0.1, f"p = {p:.3f}", ha="center", va="bottom", fontsize=7.5,
                    color=MUTED)
        chi, p = fr[m]
        ax.set_title(f"{m} planning\nFriedman χ²(2) = {chi:.2f}, p = {p:.3f}", color=c,
                     fontsize=10.5)
        ax.axhline(2, ls="--", color="#444", lw=1, zorder=1)
        ax.set_xticks(x, LM)
        ax.set_xlim(-0.5, 2.6)
        ax.set_ylim(0, 12.5)
        ax.yaxis.grid(True, zorder=0)
        ax.tick_params(axis="x", length=0)
    axes[0].set_ylabel("Prediction error (mm), median (IQR)")
    axes[1].text(2.62, 2, "2 mm", va="center", fontsize=8.5, color=MUTED)
    fig.text(0.99, -0.03, "Brackets: Bonferroni-adjusted pairwise Wilcoxon p values",
             ha="right", fontsize=8, color=MUTED)
    save(fig, "Figure_T6_landmark_comparison_friedman")


# ---------------------------------------------------------------- Table 7
def fig_table7():
    labels = ["Upper lip\n(maxillary advancement)", "Lower lip\n(mandibular setback)",
              "Soft-tissue pogonion\n(genioplasty advancement)"]
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    x = np.arange(3)
    w = 0.34
    for k, (v, p, c) in enumerate([([0.25, 0.05, 0.06], [0.479, 0.901, 0.877], C2D),
                                   ([0.01, 0.25, 0.11], [0.972, 0.481, 0.769], C3D)]):
        xs = x + (k - 0.5) * w
        ax.bar(xs, v, w * 0.92, color=c, zorder=3)
        for xi, vi, pi in zip(xs, v, p):
            ax.text(xi, vi + 0.02, f"ρ = {vi:.2f}\np = {pi:.3f}", ha="center", va="bottom",
                    fontsize=8, linespacing=1.0)
    ax.axhspan(0, 0.3, color="#f4f4f4", zorder=0)
    ax.text(1.01, 0.15, "Weak", ha="left", va="center", fontsize=8, color=MUTED, style="italic",
            transform=ax.get_yaxis_transform())
    ax.set_xticks(x, labels)
    ax.set_xlim(-0.5, 2.6)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Spearman ρ (planned movement\nvs prediction error)")
    ax.yaxis.grid(True, zorder=0)
    ax.tick_params(axis="x", length=0)
    method_legend(fig, y=1.04)
    ax.text(1.0, -0.24, "Exploratory; a movement not performed was entered as 0 mm. "
            "No correlation was significant.", transform=ax.transAxes, ha="right",
            fontsize=8, color=MUTED)
    save(fig, "Figure_T7_movement_vs_error")


if __name__ == "__main__":
    for f in [fig_table1, fig_table2, fig_table3, fig_table4, fig_table5, fig_table6, fig_table7]:
        f()
    print("Saved to", OUT)
