"""Table 9 p-value and figures for the CBCT study of fenestration, dehiscence
and maxillary sinus proximity in maxillary posterior teeth (Malaysian cohort).

No patient-level data are used. Every count below is copied from the
manuscript tables (24_10_FINAL_HMAA_Report, Tables 2, 5, 7 and 9, and the
Results text), so the figures and tests reproduce exactly what is reported.

Usage:
    python analysis.py <output_dir>

Writes to <output_dir>:
    results.json    every number used in the revision notes
    fig2_alveolar_by_tooth, fig3_alveolar_by_age,
    fig4_sinus_by_tooth, fig5_sinus_by_ethnicity  (.png/.tif at 600 dpi, .pdf vector)
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

# Keep text editable in the vector PDF figures.
plt.rcParams["pdf.fonttype"] = 42
# Liberation Sans is metric-compatible with Arial.
plt.rcParams["font.family"] = ["Liberation Sans", "DejaVu Sans"]
import numpy as np
from scipy import stats
from scipy.special import gammaln
from statsmodels.stats.proportion import proportion_confint

FIG_DPI = 600
MC_SIMULATIONS = 100_000
MC_SEED = 20261026

# ---------- counts copied from the manuscript ----------
TOOTH_GROUPS = ["First premolars", "Second premolars", "First molars", "Second molars"]
ETHNICITIES = ["Malay", "Chinese", "Indian"]
SINUS_TYPES = ["Type 0", "Type 1", "Type 2", "Type 3"]
SINUS_LABELS = ["Type 0 (no contact)", "Type 1 (contact)", "Type 2 (lateral projection)",
                "Type 3 (apical protrusion)"]
AGE_GROUPS = ["<20", "21–30", "31–40", "41–50", ">50"]

# Results text and Tables 2/5 (teeth examined for alveolar defects).
TEETH_BY_TOOTH = [172, 115, 57, 33]
RF_BY_TOOTH = [46, 15, 11, 4]
DEH_BY_TOOTH = [73, 26, 24, 5]
P_RF_BY_TOOTH = 0.024  # as reported (Results, root fenestration)
P_DEH_BY_TOOTH = "<0.001"  # as reported (Results, dehiscence)

# Tables 2 and 5, "Total" rows.
TEETH_BY_AGE = [88, 125, 51, 43, 70]
RF_BY_AGE = [17, 24, 9, 10, 16]
DEH_BY_AGE = [7, 42, 22, 20, 37]

# Table 7 as published (rows = tooth group, columns = Type 0-3).
TABLE7 = {
    "First premolars": [194, 22, 20, 7],
    "Second premolars": [59, 34, 35, 25],
    "First molars": [51, 38, 56, 62],
    "Second molars": [35, 33, 16, 24],
}
P_TABLE7 = "<0.001"

# Table 9 (rows = ethnicity, columns = Type 0-3), with the SPSS
# column-proportion letters and the reported exact p-value per tooth group.
TABLE9 = {
    "First premolars": {
        "counts": [[84, 12, 12, 2], [93, 9, 8, 4], [17, 0, 0, 1]],
        "letters": [["a", "a", "a", "a"], ["a", "a", "a", "a"], ["a", "a", "a", "a"]],
        "p_reported": 0.366,
    },
    "Second premolars": {
        "counts": [[18, 20, 14, 15], [35, 14, 17, 7], [6, 0, 4, 3]],
        "letters": [["a", "a", "a", "a"], ["b", "ab", "a", "b"], ["ab", "b", "a", "ab"]],
        "p_reported": 0.019,
    },
    "First molars": {
        "counts": [[22, 22, 21, 35], [28, 14, 29, 21], [0, 2, 6, 6]],
        "letters": [["ab", "a", "a", "a"], ["b", "a", "a", "a"], ["a", "a", "a", "a"]],
        "p_reported": 0.027,
    },
    "Second molars": {
        "counts": [[15, 13, 13, 12], [12, 18, 2, 11], [8, 4, 1, 1]],
        # Chinese Type 0 is "a" in the SPSS output (Final_2); the manuscript
        # table printed "b" by mistake.
        "letters": [["a", "a", "a", "a"], ["a", "a", "b", "a"], ["b", "a", "ab", "a"]],
        "p_reported": 0.032,
    },
}

# ---------- chart tokens (light surface, print) ----------
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#ffffff"
COLOR_RF = "#2a78d6"
COLOR_DEH = "#eb6834"
# Ordinal ramp for sinus Types 0-3 (blue 250/400/550/700): validated
# light-to-dark, light end >= 2:1 on the surface.
SINUS_COLORS = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
SINUS_TEXT = [INK, "#ffffff", "#ffffff", "#ffffff"]


# ---------- statistics ----------
def wilson(k, n):
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    return 100 * k / n, 100 * lo, 100 * hi


def pearson(table):
    chi2, p, dof, expected = stats.chi2_contingency(np.asarray(table), correction=False)
    return {"chi2": float(chi2), "df": int(dof), "p": float(p),
            "min_expected": float(expected.min()),
            "pct_expected_lt5": float(100 * (expected < 5).mean())}


def fisher_freeman_halton_mc(table, rng):
    """Monte Carlo Fisher-Freeman-Halton exact p (fixed margins)."""
    t = np.asarray(table)
    rows = np.repeat(np.arange(t.shape[0]), t.sum(1))
    cols = np.repeat(np.arange(t.shape[1]), t.sum(0))
    # Table probability up to a constant that is fixed by the margins.
    observed = -gammaln(t + 1).sum()
    hits = 0
    for _ in range(MC_SIMULATIONS):
        sim = np.zeros_like(t)
        np.add.at(sim, (rows, rng.permutation(cols)), 1)
        hits += -gammaln(sim + 1).sum() <= observed + 1e-9
    return (hits + 1) / (MC_SIMULATIONS + 1)


def cochran_armitage(cases, totals):
    """Two-sided chi-square test for linear trend across ordered groups."""
    x, n = np.asarray(cases, float), np.asarray(totals, float)
    s = np.arange(1, len(x) + 1, dtype=float)
    N, R = n.sum(), x.sum()
    pbar = R / N
    T = (s * (x - n * pbar)).sum()
    var = pbar * (1 - pbar) * ((n * s ** 2).sum() - (n * s).sum() ** 2 / N)
    z = T / np.sqrt(var)
    return {"z": float(z), "chi2": float(z ** 2), "p": float(2 * stats.norm.sf(abs(z)))}


def analyse():
    rng = np.random.default_rng(MC_SEED)
    table9 = {}
    for group, d in TABLE9.items():
        counts = np.array(d["counts"])
        table9[group] = {
            "counts": d["counts"],
            "letters": d["letters"],
            "row_pct": (100 * counts / counts.sum(1, keepdims=True)).round(1).tolist(),
            "row_n": counts.sum(1).tolist(),
            "p_reported": d["p_reported"],
            "pearson": pearson(counts),
            "ffh_exact_mc": fisher_freeman_halton_mc(counts, rng),
        }
    total = sum(np.array(d["counts"]) for d in TABLE9.values())
    table9["Total"] = {
        "counts": total.tolist(),
        "row_pct": (100 * total / total.sum(1, keepdims=True)).round(1).tolist(),
        "row_n": total.sum(1).tolist(),
        "pearson": pearson(total),
        "ffh_exact_mc": fisher_freeman_halton_mc(total, rng),
    }

    alveolar_tooth = {
        g: {"teeth": n, "rf": wilson(rf, n), "rf_n": rf, "deh": wilson(dh, n), "deh_n": dh}
        for g, n, rf, dh in zip(TOOTH_GROUPS, TEETH_BY_TOOTH, RF_BY_TOOTH, DEH_BY_TOOTH)
    }
    alveolar_age = {
        a: {"teeth": n, "rf": wilson(rf, n), "rf_n": rf, "deh": wilson(dh, n), "deh_n": dh}
        for a, n, rf, dh in zip(AGE_GROUPS, TEETH_BY_AGE, RF_BY_AGE, DEH_BY_AGE)
    }
    age_tests = {
        "rf_trend": cochran_armitage(RF_BY_AGE, TEETH_BY_AGE),
        "deh_trend": cochran_armitage(DEH_BY_AGE, TEETH_BY_AGE),
        "rf_chi2": pearson([RF_BY_AGE, np.subtract(TEETH_BY_AGE, RF_BY_AGE)]),
        "deh_chi2": pearson([DEH_BY_AGE, np.subtract(TEETH_BY_AGE, DEH_BY_AGE)]),
    }
    table7 = {g: {"counts": c, "n": int(sum(c)), "pct": (100 * np.array(c) / sum(c)).round(1).tolist()}
              for g, c in TABLE7.items()}
    return {
        "source": "Counts copied from the manuscript tables; no patient-level data used.",
        "settings": {"mc_simulations": MC_SIMULATIONS, "mc_seed": MC_SEED, "ci": "Wilson 95%"},
        "table9": table9,
        "table7": table7,
        "alveolar_by_tooth": alveolar_tooth,
        "alveolar_by_age": alveolar_age,
        "age_tests": age_tests,
        "reported_p": {"rf_by_tooth": P_RF_BY_TOOTH, "deh_by_tooth": P_DEH_BY_TOOTH,
                       "table7": P_TABLE7},
    }


# ---------- drawing helpers ----------
def style_axes(ax, grid_axis="y"):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASELINE)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=INK_2, labelsize=8.5, width=0.8, length=3)
    getattr(ax, f"{grid_axis}axis").grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def rounded_bar(ax, x0, x1, y0, y1, color, radius_pt=2.5, end="top"):
    """Bar with a rounded data-end and a square baseline end."""
    fig = ax.figure
    bbox = ax.get_window_extent()
    px = radius_pt * fig.dpi / 72
    xr = px * (ax.get_xlim()[1] - ax.get_xlim()[0]) / bbox.width
    yr = px * (ax.get_ylim()[1] - ax.get_ylim()[0]) / bbox.height
    if end == "top":
        yr = min(yr, (y1 - y0) / 2)
        xr = min(xr, (x1 - x0) / 2)
        verts = [(x0, y0), (x0, y1 - yr), (x0, y1), (x0 + xr, y1), (x1 - xr, y1),
                 (x1, y1), (x1, y1 - yr), (x1, y0), (x0, y0)]
    else:  # rounded right end, square left end
        xr = min(xr, (x1 - x0) / 2)
        yr = min(yr, (y1 - y0) / 2)
        verts = [(x0, y0), (x1 - xr, y0), (x1, y0), (x1, y0 + yr), (x1, y1 - yr),
                 (x1, y1), (x1 - xr, y1), (x0, y1), (x0, y0)]
    codes = [MPath.MOVETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO,
             MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color, edgecolor="none", zorder=3))


def save_figure(fig, stem):
    """Save as 600 dpi PNG and LZW-compressed TIFF, plus a vector PDF."""
    fig.savefig(stem.with_suffix(".png"), dpi=FIG_DPI, facecolor=SURFACE)
    fig.savefig(stem.with_suffix(".tif"), dpi=FIG_DPI, facecolor=SURFACE,
                pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(stem.with_suffix(".pdf"), facecolor=SURFACE)
    plt.close(fig)


def legend_swatches(fig, items, y, x0=0.5, marker="s"):
    handles = [plt.Line2D([], [], marker=marker, linestyle="none", markersize=7,
                          markerfacecolor=c, markeredgecolor="none") for c, _ in items]
    fig.legend(handles, [t for _, t in items], loc="upper center", bbox_to_anchor=(x0, y),
               ncol=len(items), frameon=False, fontsize=8.5, handletextpad=0.4,
               columnspacing=1.4, labelcolor=INK_2)


def fmt_p(p):
    if isinstance(p, str):
        return p.replace("<", "< ")
    return "< 0.001" if p < 0.001 else f"= {p:.3f}"


# ---------- figures ----------
# Labels and ticks are set before tight_layout so the layout makes room for
# them; marks are drawn after it because rounded_bar needs the final axes size.
def fig_alveolar_by_tooth(res, stem):
    d = res["alveolar_by_tooth"]
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    style_axes(ax)
    x = np.arange(len(TOOTH_GROUPS))
    w = 0.3
    ax.set_xlim(-0.6, len(x) - 0.4)
    ax.set_ylim(0, 60)
    ax.set_xticks(x, [f"{g}\nn = {d[g]['teeth']}" for g in TOOTH_GROUPS], fontsize=8.5, color=INK)
    ax.set_ylabel("Teeth affected (%)", fontsize=9, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    for i, g in enumerate(TOOTH_GROUPS):
        for off, key, color in ((-w / 2 - 0.02, "rf", COLOR_RF), (w / 2 + 0.02, "deh", COLOR_DEH)):
            pct, lo, hi = d[g][key]
            xc = i + off
            rounded_bar(ax, xc - w / 2, xc + w / 2, 0, pct, color)
            ax.errorbar(xc, pct, yerr=[[pct - lo], [hi - pct]], fmt="none", ecolor=INK_2,
                        elinewidth=0.8, capsize=2.5, capthick=0.8, zorder=4)
            ax.text(xc, hi + 1.2, f"{pct:.1f}", ha="center", va="bottom", fontsize=7.5, color=INK)
    p = res["reported_p"]
    legend_swatches(fig, [(COLOR_RF, f"Root fenestration (p {fmt_p(p['rf_by_tooth'])})"),
                          (COLOR_DEH, f"Dehiscence (p {fmt_p(p['deh_by_tooth'])})")], y=0.99)
    save_figure(fig, stem)


def fig_alveolar_by_age(res, stem):
    d = res["alveolar_by_age"]
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    style_axes(ax)
    x = np.arange(len(AGE_GROUPS))
    for key, color, dx, label in (("rf", COLOR_RF, -0.06, "Root fenestration"),
                                  ("deh", COLOR_DEH, 0.06, "Dehiscence")):
        pct = np.array([d[a][key][0] for a in AGE_GROUPS])
        lo = np.array([d[a][key][1] for a in AGE_GROUPS])
        hi = np.array([d[a][key][2] for a in AGE_GROUPS])
        ax.errorbar(x + dx, pct, yerr=[pct - lo, hi - pct], fmt="none", ecolor=color,
                    elinewidth=0.9, capsize=2.5, capthick=0.9, alpha=0.55, zorder=2)
        ax.plot(x + dx, pct, color=color, linewidth=2, solid_capstyle="round",
                solid_joinstyle="round", zorder=3)
        ax.scatter(x + dx, pct, s=34, color=color, edgecolor=SURFACE, linewidth=1.5, zorder=4)
        ax.text(x[-1] + dx + 0.14, pct[-1], label, va="center", ha="left", fontsize=8, color=INK)
    ax.set_xlim(-0.4, len(x) - 0.2)
    ax.set_ylim(0, 70)
    ax.set_xticks(x, [f"{a}\nn = {d[a]['teeth']}" for a in AGE_GROUPS], fontsize=8.5, color=INK)
    ax.set_xlabel("Age group (years)", fontsize=9, color=INK)
    ax.set_ylabel("Teeth affected (%)", fontsize=9, color=INK)
    fig.tight_layout(rect=(0, 0, 0.9, 0.9))
    legend_swatches(fig, [(COLOR_RF, "Root fenestration"), (COLOR_DEH, "Dehiscence")], y=0.99,
                    marker="o")
    save_figure(fig, stem)


def stacked_row(ax, y, pcts, height):
    left = 0.0
    last = max(i for i, p in enumerate(pcts) if p > 0)
    for i, p in enumerate(pcts):
        if p <= 0:
            continue
        gap = 0.35 if i < last else 0  # surface gap between segments
        if i == last:
            rounded_bar(ax, left, left + p, y - height / 2, y + height / 2, SINUS_COLORS[i],
                        end="right")
        else:
            ax.barh(y, p - gap, left=left, height=height, color=SINUS_COLORS[i], zorder=3,
                    linewidth=0)
        if p >= 7:
            ax.text(left + (p - gap) / 2, y, f"{p:.0f}", ha="center", va="center",
                    fontsize=7.5, color=SINUS_TEXT[i], zorder=5)
        left += p


def style_stacked(ax, ys, labels, ylim):
    style_axes(ax, grid_axis="x")
    ax.set_xlim(0, 100)
    ax.set_ylim(*ylim)
    ax.set_yticks(ys, labels, fontsize=8.5, color=INK)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xticks(range(0, 101, 20))


def fig_sinus_by_tooth(res, stem):
    t7 = res["table7"]
    rows = TOOTH_GROUPS + ["All tooth groups"]
    total = np.sum([t7[g]["counts"] for g in TOOTH_GROUPS], axis=0)
    data = [t7[g]["pct"] for g in TOOTH_GROUPS] + [(100 * total / total.sum()).round(1).tolist()]
    ns = [t7[g]["n"] for g in TOOTH_GROUPS] + [int(total.sum())]
    fig, ax = plt.subplots(figsize=(6.5, 3.3))
    ys = np.array([5.3, 4.3, 3.3, 2.3, 1.0])
    style_stacked(ax, ys, [f"{r}\nn = {n}" for r, n in zip(rows, ns)], (0.4, 5.9))
    ax.set_xlabel("Roots (%)", fontsize=9, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    for y, pcts in zip(ys, data):
        stacked_row(ax, y, pcts, height=0.6)
    legend_swatches(fig, list(zip(SINUS_COLORS, SINUS_LABELS)), y=0.99)
    save_figure(fig, stem)


def fig_sinus_by_ethnicity(res, stem):
    t9 = res["table9"]
    panels = TOOTH_GROUPS + ["Total"]
    fig, axes = plt.subplots(len(panels), 1, figsize=(6.5, 7.8), sharex=True)
    ys = [2, 1, 0]
    for ax, g in zip(axes, panels):
        d = t9[g]
        style_stacked(ax, ys, [f"{e} (n = {n})" for e, n in zip(ETHNICITIES, d["row_n"])],
                      (-0.6, 2.6))
        if g == "Total":
            title = f"All tooth groups   (p {fmt_p(d['pearson']['p'])})"
        else:
            title = f"{g}   (p {fmt_p(d['p_reported'])})"
        ax.set_title(title, loc="left", fontsize=9, color=INK, pad=4)
        if ax is not axes[-1]:
            ax.tick_params(axis="x", length=0)
    axes[-1].set_xlabel("Roots (%)", fontsize=9, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95), h_pad=1.4)
    for ax, g in zip(axes, panels):
        for y, pcts in zip(ys, t9[g]["row_pct"]):
            stacked_row(ax, y, pcts, height=0.66)
    legend_swatches(fig, list(zip(SINUS_COLORS, SINUS_LABELS)), y=0.995)
    save_figure(fig, stem)


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    res = analyse()
    fig_alveolar_by_tooth(res, out / "fig2_alveolar_by_tooth")
    fig_alveolar_by_age(res, out / "fig3_alveolar_by_age")
    fig_sinus_by_tooth(res, out / "fig4_sinus_by_tooth")
    fig_sinus_by_ethnicity(res, out / "fig5_sinus_by_ethnicity")
    (out / "results.json").write_text(json.dumps(res, indent=2))
    tot = res["table9"]["Total"]["pearson"]
    print(f"Table 9 total: chi2({tot['df']}) = {tot['chi2']:.2f}, p = {tot['p']:.3f}, "
          f"min expected = {tot['min_expected']:.1f}")
    for g in TOOTH_GROUPS:
        r = res["table9"][g]
        print(f"  {g}: reported p = {r['p_reported']}, exact (MC) p = {r['ffh_exact_mc']:.3f}")
    print(f"Wrote figures and results.json to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
