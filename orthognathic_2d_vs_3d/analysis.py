"""Statistical analysis of 2D vs 3D (Dolphin 3D) soft-tissue prediction error
after bimaxillary orthognathic surgery for skeletal Class III patients.

The input workbook lists, for each patient, the planned surgical movements
(maxillary advancement, mandibular setback, genioplasty) and the linear
difference (mm) between the simulated and the post-operative position of the
upper lip, lower lip and soft-tissue pogonion, for 2D and 3D planning.

Usage:
    python analysis.py <input.xlsx> <output_dir>

Writes to <output_dir>:
    data_tidy.csv   anonymised long-format data (patient IDs, no names)
    results.json    every number used in the report
    results.xlsx    all result tables, one sheet each
    fig1_paired.png, fig2_scatter.png
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
import pandas as pd
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar

LANDMARKS = ["Upper lip", "Lower lip", "Soft-tissue pogonion"]
LANDMARK_LABELS = {"U lip": "Upper lip", "L lip": "Lower lip", "pogonion": "Soft-tissue pogonion"}
# The movement recorded on the same row as each landmark in the workbook.
LANDMARK_MOVEMENT = {
    "Upper lip": "max_advancement",
    "Lower lip": "mand_setback",
    "Soft-tissue pogonion": "genioplasty",
}
MOVEMENT_LABELS = {
    "max_advancement": "Maxillary advancement",
    "mand_setback": "Mandibular setback",
    "genioplasty": "Genioplasty advancement",
}
ACCEPTABLE_MM = 2.0
ALPHA = 0.05

COLOR_2D = "#2a78d6"
COLOR_3D = "#eb6834"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"


def read_workbook(path):
    """Parse the patient blocks of the data sheet into a long-format frame."""
    ws = openpyxl.load_workbook(path, data_only=True).active
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    records = []
    patient = 0
    for i, row in enumerate(rows):
        movement = str(row[2] or "").lower()
        if "adv" not in movement:
            continue
        patient += 1
        block = rows[i : i + 3]
        plan = {
            "max_advancement": float(block[0][3]),
            "mand_setback": abs(float(block[1][3])),
            "genioplasty": float(block[2][3]),
        }
        sex = str(row[11]).strip()
        age = int(row[13])
        for line in block:
            records.append(
                {
                    "patient": f"P{patient:02d}",
                    "sex": sex,
                    "age": age,
                    **plan,
                    "landmark": LANDMARK_LABELS[str(line[8]).strip()],
                    "error_2d": float(line[5]),
                    "error_3d": float(line[7]),
                }
            )
    df = pd.DataFrame(records)
    df["landmark"] = pd.Categorical(df["landmark"], LANDMARKS, ordered=True)
    return df


def describe(x):
    x = np.asarray(x, dtype=float)
    n = len(x)
    mean, sd = x.mean(), x.std(ddof=1)
    half = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n)
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "ci_low": mean - half,
        "ci_high": mean + half,
        "median": med,
        "q1": q1,
        "q3": q3,
        "min": x.min(),
        "max": x.max(),
    }


def paired_comparison(a, b):
    """2D (a) vs 3D (b): paired t-test, Wilcoxon signed-rank, effect size."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    n = len(d)
    t = stats.ttest_rel(a, b)
    ci = t.confidence_interval(0.95)
    w = stats.wilcoxon(a, b)
    sw = stats.shapiro(d)
    sd = d.std(ddof=1)
    return {
        "n": n,
        "mean_diff": d.mean(),
        "sd_diff": sd,
        "ci_low": ci.low,
        "ci_high": ci.high,
        "t": t.statistic,
        "df": n - 1,
        "p_t": t.pvalue,
        "shapiro_W": sw.statistic,
        "p_shapiro": sw.pvalue,
        "wilcoxon_W": w.statistic,
        "p_wilcoxon": w.pvalue,
        "cohen_dz": d.mean() / sd if sd > 0 else np.nan,
        "loa_low": d.mean() - 1.96 * sd,
        "loa_high": d.mean() + 1.96 * sd,
    }


def correlation(a, b):
    p = stats.pearsonr(a, b)
    s = stats.spearmanr(a, b)
    return {
        "n": len(a),
        "pearson_r": p.statistic,
        "p_pearson": p.pvalue,
        "spearman_rho": s.statistic,
        "p_spearman": s.pvalue,
    }


def acceptability(a, b):
    """Share of predictions within the clinical threshold; exact McNemar test."""
    ok_2d = np.asarray(a) <= ACCEPTABLE_MM
    ok_3d = np.asarray(b) <= ACCEPTABLE_MM
    table = [
        [int(np.sum(ok_2d & ok_3d)), int(np.sum(ok_2d & ~ok_3d))],
        [int(np.sum(~ok_2d & ok_3d)), int(np.sum(~ok_2d & ~ok_3d))],
    ]
    return {
        "n": len(ok_2d),
        "ok_2d": int(ok_2d.sum()),
        "ok_3d": int(ok_3d.sum()),
        "only_2d": table[0][1],
        "only_3d": table[1][0],
        "p_mcnemar": mcnemar(table, exact=True).pvalue,
    }


def between_landmarks(wide):
    """Friedman test across the three landmarks, Bonferroni post-hoc Wilcoxon."""
    cols = [wide[l].to_numpy() for l in LANDMARKS]
    fr = stats.friedmanchisquare(*cols)
    pairs = []
    for i in range(len(LANDMARKS)):
        for j in range(i + 1, len(LANDMARKS)):
            p = stats.wilcoxon(cols[i], cols[j]).pvalue
            pairs.append(
                {
                    "pair": f"{LANDMARKS[i]} vs {LANDMARKS[j]}",
                    "p_raw": p,
                    "p_bonferroni": min(1.0, p * 3),
                }
            )
    return {"n": len(wide), "chi2": fr.statistic, "df": 2, "p": fr.pvalue, "posthoc": pairs}


def analyse(df):
    """Run every per-landmark analysis on one dataset (primary or sensitivity)."""
    out = {"descriptive": [], "paired": [], "correlation": [], "acceptability": []}
    for lm in LANDMARKS:
        sub = df[df["landmark"] == lm]
        a, b = sub["error_2d"], sub["error_3d"]
        out["descriptive"].append({"landmark": lm, "method": "2D", **describe(a)})
        out["descriptive"].append({"landmark": lm, "method": "3D", **describe(b)})
        out["paired"].append({"landmark": lm, **paired_comparison(a, b)})
        out["correlation"].append({"landmark": lm, **correlation(a, b)})
        out["acceptability"].append({"landmark": lm, **acceptability(a, b)})

    # Overall error per patient: mean of the three landmarks (patients with all three).
    counts = df.groupby("patient", observed=True)["landmark"].nunique()
    complete = df[df["patient"].isin(counts[counts == len(LANDMARKS)].index)]
    per_patient = complete.groupby("patient", observed=True)[["error_2d", "error_3d"]].mean()
    a, b = per_patient["error_2d"], per_patient["error_3d"]
    out["descriptive"].append({"landmark": "Overall (patient mean)", "method": "2D", **describe(a)})
    out["descriptive"].append({"landmark": "Overall (patient mean)", "method": "3D", **describe(b)})
    out["paired"].append({"landmark": "Overall (patient mean)", **paired_comparison(a, b)})
    out["correlation"].append({"landmark": "Overall (patient mean)", **correlation(a, b)})

    # All landmark predictions pooled, for the acceptability summary only.
    out["acceptability"].append(
        {"landmark": "All predictions", **acceptability(df["error_2d"], df["error_3d"])}
    )

    out["between_landmarks"] = {}
    for method, col in (("2D", "error_2d"), ("3D", "error_3d")):
        wide = complete.pivot(index="patient", columns="landmark", values=col)
        out["between_landmarks"][method] = between_landmarks(wide)

    out["movement_correlation"] = []
    for lm in LANDMARKS:
        sub = df[df["landmark"] == lm]
        mv = sub[LANDMARK_MOVEMENT[lm]]
        for method, col in (("2D", "error_2d"), ("3D", "error_3d")):
            s = stats.spearmanr(mv, sub[col])
            out["movement_correlation"].append(
                {
                    "landmark": lm,
                    "movement": MOVEMENT_LABELS[LANDMARK_MOVEMENT[lm]],
                    "method": method,
                    "n": len(sub),
                    "spearman_rho": s.statistic,
                    "p": s.pvalue,
                }
            )
    return out


def sample_summary(df):
    pts = df.drop_duplicates("patient").set_index("patient")
    bimax = int((pts["mand_setback"] > 0).sum())
    return {
        "n_patients": len(pts),
        "n_female": int((pts["sex"] == "Female").sum()),
        "n_male": int((pts["sex"] == "Male").sum()),
        "age": describe(pts["age"]),
        "n_bimaxillary": bimax,
        "n_maxilla_only": len(pts) - bimax,
        "n_genioplasty": int((pts["genioplasty"] > 0).sum()),
        "max_advancement": describe(pts["max_advancement"]),
        "mand_setback": describe(pts.loc[pts["mand_setback"] > 0, "mand_setback"]),
        "genioplasty": describe(pts.loc[pts["genioplasty"] > 0, "genioplasty"]),
        "patients": pts[["sex", "age", "max_advancement", "mand_setback", "genioplasty"]]
        .reset_index()
        .to_dict("records"),
    }


def style_axes(ax):
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_2)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=INK_2, labelsize=9, width=0.8)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def fig_paired(df, path):
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.6), sharey=True)
    ymax = max(df["error_2d"].max(), df["error_3d"].max()) * 1.08
    for ax, lm in zip(axes, LANDMARKS):
        sub = df[df["landmark"] == lm]
        for _, r in sub.iterrows():
            ax.plot([0, 1], [r["error_2d"], r["error_3d"]], color="#b9b8b3", linewidth=1, zorder=1)
        ax.scatter(np.zeros(len(sub)), sub["error_2d"], s=36, color=COLOR_2D,
                   edgecolor="white", linewidth=1.5, zorder=3, clip_on=False, label="2D")
        ax.scatter(np.ones(len(sub)), sub["error_3d"], s=36, color=COLOR_3D,
                   edgecolor="white", linewidth=1.5, zorder=3, clip_on=False, label="3D")
        for x, col, c in ((0, "error_2d", COLOR_2D), (1, "error_3d", COLOR_3D)):
            m = sub[col].mean()
            ax.plot([x - 0.18, x + 0.18], [m, m], color=c, linewidth=2.5, zorder=4)
        ax.axhline(ACCEPTABLE_MM, color=INK_2, linewidth=0.9, linestyle=(0, (4, 3)), zorder=2)
        style_axes(ax)
        ax.set_xticks([0, 1], ["2D", "3D"])
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0, ymax)
        ax.set_title(lm, fontsize=10, color=INK)
    axes[0].set_ylabel("Prediction error (mm)", fontsize=9, color=INK)
    axes[-1].text(1.52, ACCEPTABLE_MM, " 2 mm", va="center", ha="left", fontsize=8, color=INK_2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=9,
               bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)


def fig_scatter(df, corr, path):
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.4))
    lim = max(df["error_2d"].max(), df["error_3d"].max()) * 1.08
    r_by_lm = {c["landmark"]: c for c in corr}
    for ax, lm in zip(axes, LANDMARKS):
        sub = df[df["landmark"] == lm]
        ax.plot([0, lim], [0, lim], color=INK_2, linewidth=0.9, linestyle=(0, (4, 3)), zorder=1)
        ax.scatter(sub["error_2d"], sub["error_3d"], s=36, color=COLOR_2D,
                   edgecolor="white", linewidth=1.5, zorder=3, clip_on=False)
        style_axes(ax)
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.set_aspect("equal")
        ticks = np.arange(0, lim, 2)
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        c = r_by_lm[lm]
        ax.set_title(lm, fontsize=10, color=INK)
        ax.text(0.04, 0.96, f"r = {c['pearson_r']:.2f} (p = {fmt_p(c['p_pearson'])})",
                transform=ax.transAxes, va="top", fontsize=8, color=INK)
        ax.set_xlabel("2D error (mm)", fontsize=9, color=INK)
    axes[0].set_ylabel("3D error (mm)", fontsize=9, color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)


def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if np.isnan(obj) else float(obj)
    return obj


def main(xlsx, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = read_workbook(xlsx)
    df.to_csv(out_dir / "data_tidy.csv", index=False)

    # Sensitivity: a recorded 0.00 mm is treated as "not measured" and the pair dropped.
    zero = (df["error_2d"] == 0) | (df["error_3d"] == 0)
    sens_df = df[~zero]

    results = {
        "sample": sample_summary(df),
        "primary": analyse(df),
        "sensitivity": analyse(sens_df),
        "excluded_in_sensitivity": df.loc[zero, ["patient", "landmark", "error_2d", "error_3d"]]
        .astype({"landmark": str})
        .to_dict("records"),
        "settings": {"acceptable_mm": ACCEPTABLE_MM, "alpha": ALPHA},
        "versions": {
            "python": sys.version.split()[0],
            "scipy": __import__("scipy").__version__,
            "statsmodels": __import__("statsmodels").__version__,
            "pandas": pd.__version__,
        },
    }
    (out_dir / "results.json").write_text(json.dumps(to_jsonable(results), indent=2))

    with pd.ExcelWriter(out_dir / "results.xlsx") as xw:
        df.to_excel(xw, sheet_name="Data (anonymised)", index=False)
        for key in ("primary", "sensitivity"):
            r = results[key]
            pd.DataFrame(r["descriptive"]).to_excel(xw, sheet_name=f"{key} descriptive", index=False)
            pd.DataFrame(r["paired"]).to_excel(xw, sheet_name=f"{key} 2D vs 3D", index=False)
            pd.DataFrame(r["correlation"]).to_excel(xw, sheet_name=f"{key} correlation", index=False)
            pd.DataFrame(r["acceptability"]).to_excel(xw, sheet_name=f"{key} within 2mm", index=False)
            rows = []
            for method, bl in r["between_landmarks"].items():
                for ph in bl["posthoc"]:
                    rows.append({"method": method, "friedman_chi2": bl["chi2"], "p_friedman": bl["p"], **ph})
            pd.DataFrame(rows).to_excel(xw, sheet_name=f"{key} landmarks", index=False)
            pd.DataFrame(r["movement_correlation"]).to_excel(xw, sheet_name=f"{key} movement", index=False)

    fig_paired(df, out_dir / "fig1_paired.png")
    fig_scatter(df, results["primary"]["correlation"], out_dir / "fig2_scatter.png")
    print(f"Wrote results for {df['patient'].nunique()} patients to {out_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
