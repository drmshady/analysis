// Builds the "Statistical methodology and results" Word document from the
// output of analysis.py.
//
// Usage: node build_report.js <output_dir>
// Reads <output_dir>/results.json and the two figures, writes
// <output_dir>/Statistical_Methodology_and_Results.docx

const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, HeadingLevel, ImageRun, LevelFormat, LineRuleType,
  Packer, Paragraph, Table, TableCell, TableRow, TextRun, VerticalAlign, WidthType,
} = require("docx");

const outDir = process.argv[2];
if (!outDir) {
  console.error("Usage: node build_report.js <output_dir>");
  process.exit(1);
}
const R = JSON.parse(fs.readFileSync(path.join(outDir, "results.json"), "utf8"));
const S = R.sample;
const ALPHA = R.settings.alpha;
const MM = R.settings.acceptable_mm;

const FONT = "Times New Roman";
const PAGE_W = 11906; // A4
const MARGIN = 1440;
const CONTENT_W = PAGE_W - 2 * MARGIN;

// ---------- number formatting ----------
const MINUS = "−";
const f = (x, d = 2) => {
  const s = Number(x).toFixed(d);
  return s.startsWith("-") ? (Number(s) === 0 ? s.slice(1) : MINUS + s.slice(1)) : s;
};
const pTxt = (p) => (p < 0.001 ? "< 0.001" : `= ${f(p, 3)}`); // in sentences
const pCell = (p) => (p < 0.001 ? "<0.001" : f(p, 3)); // in tables
const sig = (p) => p < ALPHA;
const msd = (d, dp = 2) => `${f(d.mean, dp)} ± ${f(d.sd, dp)}`;
const ci = (lo, hi) => `${f(lo)} to ${f(hi)}`;
const pct = (n, N) => `${n} (${f((100 * n) / N, 1)}%)`;
const range = (d, dp = 0) => `${f(d.min, dp)}–${f(d.max, dp)}`;
const strength = (r) => (Math.abs(r) < 0.3 ? "weak" : Math.abs(r) <= 0.7 ? "moderate" : "strong");
const WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"];
const word = (n) => WORDS[n] ?? String(n);
const Word = (n) => word(n).charAt(0).toUpperCase() + word(n).slice(1);

const LANDMARKS = ["Upper lip", "Lower lip", "Soft-tissue pogonion"];
const OVERALL = "Overall (patient mean)";
const byLm = (arr, lm, method) =>
  arr.find((r) => r.landmark === lm && (method === undefined || r.method === method));
const desc = (lm, m) => byLm(R.descriptive, lm, m);
const paired = (lm) => byLm(R.paired, lm);
const corr = (lm) => byLm(R.correlation, lm);
const acc = (lm) => byLm(R.acceptability, lm);
const lc = (lm) => lm.charAt(0).toLowerCase() + lm.slice(1);

// ---------- paragraph helpers ----------
// Text may contain _italic_ spans (used for statistical symbols).
function runs(text, opts = {}) {
  return text.split(/(_[^_]+_)/).filter(Boolean).map((part) =>
    part.startsWith("_") && part.endsWith("_")
      ? new TextRun({ text: part.slice(1, -1), italics: true, ...opts })
      : new TextRun({ text: part, ...opts }));
}
const para = (text, opts = {}) =>
  new Paragraph({ children: runs(text), alignment: AlignmentType.JUSTIFIED, spacing: { after: 160 }, ...opts });
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
const bullet = (text) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(text), spacing: { after: 80 } });

function caption(label, title) {
  return new Paragraph({
    keepNext: true,
    spacing: { before: 240, after: 100, line: 240 },
    children: [new TextRun({ text: `${label} `, bold: true }), ...runs(title)],
  });
}
function note(text) {
  return new Paragraph({
    spacing: { before: 60, after: 240, line: 240 },
    children: runs(text, { size: 18 }),
  });
}

// ---------- three-line academic table ----------
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const THICK = { style: BorderStyle.SINGLE, size: 12, color: "000000" };
const THIN = { style: BorderStyle.SINGLE, size: 6, color: "000000" };

// columns: [{ header, w, align }] with w as relative widths; rows: arrays of
// cells, each a string or { text, bold }. Options: boldRows (indices), ruleAbove (indices).
function academicTable(columns, rows, { boldRows = [], ruleAbove = [], size = 19 } = {}) {
  const total = columns.reduce((a, c) => a + c.w, 0);
  const widths = columns.map((c) => Math.floor((c.w / total) * CONTENT_W));
  widths[widths.length - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);

  const cell = (content, i, borders, bold, keepNext = true) => {
    const c = typeof content === "object" ? content : { text: String(content) };
    return new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      borders: { left: NONE, right: NONE, ...borders },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 50, bottom: 50, left: 70, right: 70 },
      children: [new Paragraph({
        alignment: i === 0 ? AlignmentType.LEFT : (columns[i].align ?? AlignmentType.CENTER),
        keepNext,
        spacing: { after: 0, line: 240, lineRule: LineRuleType.AUTO },
        children: runs(c.text, { size, bold: bold || c.bold }),
      })],
    });
  };

  const header = new TableRow({
    tableHeader: true,
    children: columns.map((c, i) => cell(c.header, i, { top: THICK, bottom: THIN }, true)),
  });
  const body = rows.map((row, r) => new TableRow({
    cantSplit: true,
    children: row.map((content, i) => cell(content, i, {
      top: ruleAbove.includes(r) ? THIN : NONE,
      bottom: r === rows.length - 1 ? THICK : NONE,
    }, boldRows.includes(r), r < rows.length - 1)),
  }));
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [header, ...body],
  });
}

const sigCell = (p, text = pCell(p)) => ({ text: sig(p) ? `${text}*` : text, bold: sig(p) });

function figure(file, widthIn, label, title) {
  const buf = fs.readFileSync(path.join(outDir, file));
  // PNG header: width and height are big-endian at bytes 16 and 20.
  const ratio = buf.readUInt32BE(20) / buf.readUInt32BE(16);
  const w = Math.round(widthIn * 96);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true,
      spacing: { before: 240, after: 60, line: 240, lineRule: LineRuleType.AUTO },
      children: [new ImageRun({ type: "png", data: buf, transformation: { width: w, height: Math.round(w * ratio) } })],
    }),
    new Paragraph({
      spacing: { after: 240, line: 240 }, alignment: AlignmentType.JUSTIFIED,
      children: [new TextRun({ text: `${label} `, bold: true, size: 20 }), ...runs(title, { size: 20 })],
    }),
  ];
}

// =====================================================================
// Methodology
// =====================================================================
const methods = [
  h1("Statistical Methodology"),
  h2("Outcome variable"),
  para(`The primary outcome was the soft-tissue prediction error, defined as the linear difference (in millimetres) between the simulated (virtually planned) position and the actual postoperative position of three soft-tissue landmarks: upper lip, lower lip and soft-tissue pogonion. The error was recorded for every patient with both two-dimensional (2D) and three-dimensional (3D) virtual planning in Dolphin 3D software, so that each patient served as their own control (paired design). Errors were analysed as absolute values, without regard to direction. Recorded values of 0.00 mm represent a true zero error and were analysed as entered; all ${S.n_patients} patients were included.`),
  h2("Descriptive statistics"),
  para("Continuous variables were described as mean ± standard deviation (SD), 95% confidence interval (CI) of the mean, median (interquartile range, IQR) and range (minimum–maximum). Categorical variables were described as frequency and percentage."),
  h2("Comparison between 2D and 3D planning"),
  para("Normality of the paired differences (2D − 3D) was tested with the Shapiro–Wilk test. The prediction errors of 2D and 3D planning were compared at each landmark with the paired _t_-test, and the mean difference was reported with its 95% CI. Because of the small sample size, the Wilcoxon signed-rank test was applied as a confirmatory non-parametric test. The effect size was expressed as Cohen's _d_z (mean difference divided by the SD of the differences) and interpreted as small (0.2), medium (0.5) or large (≥ 0.8). To control the family-wise error rate across the three landmarks, the paired _t_-test _p_ values were additionally adjusted with the Holm method. The overall prediction error of each patient was calculated as the mean of the three landmarks and compared in the same way."),
  h2("Correlation between 2D and 3D planning"),
  para("The correlation between the 2D and 3D prediction errors at each landmark was assessed with Pearson's correlation coefficient (_r_). Spearman's rank correlation coefficient (_ρ_), which is robust to outliers, was reported alongside. Correlation strength was interpreted as weak (|_r_| < 0.3), moderate (0.3–0.7) or strong (> 0.7)."),
  h2("Clinical acceptability"),
  para(`A prediction error of ≤ ${f(MM, 0)} mm was considered clinically acceptable. The proportions of clinically acceptable predictions with 2D and 3D planning were compared at each landmark with the exact McNemar test for paired proportions.`),
  h2("Comparison among landmarks"),
  para("Differences in prediction error among the three landmarks were tested separately for each planning method with the Friedman test, followed by pairwise Wilcoxon signed-rank tests with Bonferroni correction."),
  h2("Planned movement and prediction error"),
  para("The association between the magnitude of the planned surgical movement and the prediction error at the corresponding landmark (maxillary advancement – upper lip; mandibular setback – lower lip; genioplasty advancement – soft-tissue pogonion) was explored with Spearman's rank correlation."),
  h2("Software and level of significance"),
  para(`Statistical analysis was performed with Python ${R.versions.python} using the SciPy (v${R.versions.scipy}) and statsmodels (v${R.versions.statsmodels}) libraries. All tests were two-tailed, and a _p_ value < ${ALPHA} was considered statistically significant.`),
];

// =====================================================================
// Results
// =====================================================================

// ---- Table 1: sample ----
const mv = (x) => (x > 0 ? f(x, 0) : "—");
const t1 = academicTable(
  [
    { header: "Patient", w: 11 }, { header: "Sex", w: 11 }, { header: "Age (years)", w: 12 },
    { header: "Maxillary advancement (mm)", w: 20 }, { header: "Mandibular setback (mm)", w: 20 },
    { header: "Genioplasty advancement (mm)", w: 20 },
  ],
  [
    ...S.patients.map((p) => [p.patient, p.sex, String(p.age), mv(p.max_advancement), mv(p.mand_setback), mv(p.genioplasty)]),
    ["Mean ± SD", `F ${S.n_female} / M ${S.n_male}`, msd(S.age, 1), msd(S.max_advancement, 1),
      `${msd(S.mand_setback, 1)} (_n_ = ${S.mand_setback.n})`, `${msd(S.genioplasty, 1)} (_n_ = ${S.genioplasty.n})`],
    ["Range", "", range(S.age), range(S.max_advancement), range(S.mand_setback), range(S.genioplasty)],
  ],
  { ruleAbove: [S.patients.length], boldRows: [] },
);

const sampleText = para(`${Word(S.n_patients)} patients with skeletal Class III deformity were included: ${word(S.n_female)} females (${f((100 * S.n_female) / S.n_patients, 0)}%) and ${word(S.n_male)} males (${f((100 * S.n_male) / S.n_patients, 0)}%), with a mean age of ${f(S.age.mean, 1)} ± ${f(S.age.sd, 1)} years (range ${range(S.age)}). ${Word(S.n_bimaxillary)} patients (${f((100 * S.n_bimaxillary) / S.n_patients, 0)}%) underwent bimaxillary surgery (maxillary advancement with mandibular setback) and ${word(S.n_maxilla_only)} (${f((100 * S.n_maxilla_only) / S.n_patients, 0)}%) underwent maxillary advancement only; ${word(S.n_genioplasty)} patients (${f((100 * S.n_genioplasty) / S.n_patients, 0)}%) also had an advancement genioplasty. The mean planned maxillary advancement was ${msd(S.max_advancement, 1)} mm, the mandibular setback ${msd(S.mand_setback, 1)} mm and the genioplasty advancement ${msd(S.genioplasty, 1)} mm (Table 1).`);

// ---- Table 2: descriptive ----
const t2rows = [];
[...LANDMARKS, OVERALL].forEach((lm) => {
  ["2D", "3D"].forEach((m, k) => {
    const d = desc(lm, m);
    t2rows.push([k === 0 ? lm : "", m, String(d.n), msd(d), ci(d.ci_low, d.ci_high),
      `${f(d.median)} (${f(d.q1)}–${f(d.q3)})`, `${f(d.min)}–${f(d.max)}`]);
  });
});
const t2 = academicTable(
  [
    { header: "Landmark", w: 20 }, { header: "Method", w: 9 }, { header: "_N_", w: 5 },
    { header: "Mean ± SD", w: 15 }, { header: "95% CI", w: 15 }, { header: "Median (IQR)", w: 20 },
    { header: "Min–Max", w: 13 },
  ],
  t2rows,
  { ruleAbove: [6] },
);

const d2 = (lm) => desc(lm, "2D");
const d3 = (lm) => desc(lm, "3D");
const widest = LANDMARKS.reduce((a, lm) => (d2(lm).sd + d3(lm).sd > d2(a).sd + d3(a).sd ? lm : a));
const descText = para(`Table 2 summarises the prediction errors. With 2D planning, the mean error was ${msd(d2("Upper lip"))} mm at the upper lip, ${msd(d2("Lower lip"))} mm at the lower lip and ${msd(d2("Soft-tissue pogonion"))} mm at soft-tissue pogonion. With 3D planning, the corresponding errors were ${msd(d3("Upper lip"))} mm, ${msd(d3("Lower lip"))} mm and ${msd(d3("Soft-tissue pogonion"))} mm. The overall prediction error per patient (mean of the three landmarks) was ${msd(d2(OVERALL))} mm with 2D and ${msd(d3(OVERALL))} mm with 3D planning. The ${lc(widest)} showed the widest variation with both methods (2D: ${f(d2(widest).min)}–${f(d2(widest).max)} mm; 3D: ${f(d3(widest).min)}–${f(d3(widest).max)} mm).`);

// ---- Table 3: paired comparison ----
const t3 = academicTable(
  [
    { header: "Landmark", w: 17 }, { header: "Mean difference ± SD (mm)", w: 14 }, { header: "95% CI", w: 15 },
    { header: "Shapiro–Wilk _p_", w: 10 }, { header: "_t_ (df)", w: 10 }, { header: "_p_", w: 8 },
    { header: "Holm _p_", w: 8 }, { header: "Wilcoxon _p_", w: 11 }, { header: "_d_z", w: 7 },
  ],
  [...LANDMARKS, OVERALL].map((lm) => {
    const p = paired(lm);
    return [lm, msd({ mean: p.mean_diff, sd: p.sd_diff }), ci(p.ci_low, p.ci_high), pCell(p.p_shapiro),
      `${f(p.t)} (${p.df})`, sigCell(p.p_t), p.p_t_holm === undefined ? "—" : sigCell(p.p_t_holm),
      sigCell(p.p_wilcoxon), f(p.cohen_dz)];
  }),
  { ruleAbove: [3], size: 18 },
);

const diffDetail = (lm, withD) => {
  const p = paired(lm);
  return `${lc(lm)} (mean difference ${f(p.mean_diff)} mm, 95% CI ${ci(p.ci_low, p.ci_high)}; _p_ ${pTxt(p.p_t)}${withD ? `; _d_z = ${f(p.cohen_dz)}` : ""})`;
};
function compareSentences() {
  const better3 = LANDMARKS.filter((lm) => sig(paired(lm).p_t) && paired(lm).mean_diff > 0);
  const better2 = LANDMARKS.filter((lm) => sig(paired(lm).p_t) && paired(lm).mean_diff < 0);
  const ns = LANDMARKS.filter((lm) => !sig(paired(lm).p_t));
  const out = [];
  if (better3.length) out.push(`3D planning produced a significantly smaller prediction error than 2D planning at the ${better3.map((lm) => diffDetail(lm, true)).join(" and at the ")}.`);
  if (better2.length) out.push(`2D planning produced a significantly smaller prediction error than 3D planning at the ${better2.map((lm) => diffDetail(lm, true)).join(" and at the ")}.`);
  if (ns.length) out.push(`No significant difference between the two methods was found at the ${ns.map((lm) => diffDetail(lm, false)).join(" or at the ")}.`);
  return out.join(" ");
}
const minShapiro = Math.min(...R.paired.map((p) => p.p_shapiro));
const allNormal = R.paired.every((p) => !sig(p.p_shapiro));
const wilcoxonAgrees = R.paired.every((p) => sig(p.p_t) === sig(p.p_wilcoxon));
const holmAgrees = R.paired.filter((p) => p.p_t_holm !== undefined).every((p) => sig(p.p_t) === sig(p.p_t_holm));
const ov = paired(OVERALL);
const dirText = (lm) => {
  const p = paired(lm);
  return `${p.n_3d_smaller} of ${p.n} patients at the ${lc(lm)}`;
};
const compareText = [
  para(`${allNormal ? `The paired differences were normally distributed at all landmarks (Shapiro–Wilk _p_ ≥ ${f(minShapiro, 2)}), so the paired _t_-test was appropriate.` : "The paired differences departed from normality for at least one comparison (Table 3), so the Wilcoxon signed-rank results should be given priority there."} ${compareSentences()} ${holmAgrees ? "All conclusions were unchanged after Holm correction for the three landmarks." : "Note that not all conclusions survived Holm correction for the three landmarks (Table 3)."} ${wilcoxonAgrees ? "The Wilcoxon signed-rank test led to the same conclusions in every comparison." : "The Wilcoxon signed-rank test did not agree with the paired _t_-test in every comparison (Table 3)."}`),
  para(`Averaged over the three landmarks, the overall prediction error per patient was ${f(Math.abs(ov.mean_diff))} mm ${ov.mean_diff > 0 ? "smaller with 3D" : "smaller with 2D"} planning (95% CI ${ci(ov.ci_low, ov.ci_high)}); this difference was ${sig(ov.p_t) ? "statistically significant" : "not statistically significant"} (_p_ ${pTxt(ov.p_t)}). At patient level (Figure 1), 3D planning gave the smaller error in ${LANDMARKS.map(dirText).join(", ").replace(/, ([^,]*)$/, " and $1")}.`),
];

// ---- Table 4: correlation ----
const t4 = academicTable(
  [
    { header: "Landmark", w: 26 }, { header: "_N_", w: 8 }, { header: "Pearson _r_", w: 16 },
    { header: "_p_", w: 16 }, { header: "Spearman _ρ_", w: 17 }, { header: "_p_", w: 17 },
  ],
  [...LANDMARKS, OVERALL].map((lm) => {
    const c = corr(lm);
    return [lm, String(c.n), f(c.pearson_r), sigCell(c.p_pearson), f(c.spearman_rho), sigCell(c.p_spearman)];
  }),
  { ruleAbove: [3] },
);

function corrSentence(lm) {
  const c = corr(lm);
  return `${strength(c.pearson_r)} and ${sig(c.p_pearson) ? "significant" : "non-significant"} at the ${lc(lm)} (_r_ = ${f(c.pearson_r)}, _p_ ${pTxt(c.p_pearson)}; _ρ_ = ${f(c.spearman_rho)}, _p_ ${pTxt(c.p_spearman)})`;
}
const sigCorr = LANDMARKS.filter((lm) => sig(corr(lm).p_pearson));
const co = corr(OVERALL);
const corrText = para(`The correlation between the 2D and 3D prediction errors (Table 4, Figure 2) was ${LANDMARKS.map(corrSentence).join("; ")}. ${sigCorr.length ? `Thus, patients whose ${sigCorr.map(lc).join(" and ")} ${sigCorr.length > 1 ? "were" : "was"} poorly predicted by 2D planning also tended to be poorly predicted by 3D planning. ` : ""}For the overall prediction error per patient, the correlation was ${strength(co.pearson_r)} and ${sig(co.p_pearson) ? "significant" : "non-significant"} (_r_ = ${f(co.pearson_r)}, _p_ ${pTxt(co.p_pearson)}).`);

// ---- Table 5: acceptability ----
const pooled = acc("All predictions");
const t5 = academicTable(
  [
    { header: "Landmark", w: 28 }, { header: "_N_", w: 8 }, { header: `2D ≤ ${f(MM, 0)} mm, n (%)`, w: 21 },
    { header: `3D ≤ ${f(MM, 0)} mm, n (%)`, w: 21 }, { header: "McNemar _p_", w: 22 },
  ],
  [
    ...LANDMARKS.map((lm) => {
      const a = acc(lm);
      return [lm, String(a.n), pct(a.ok_2d, a.n), pct(a.ok_3d, a.n), sigCell(a.p_mcnemar)];
    }),
    ["All predictions†", String(pooled.n), pct(pooled.ok_2d, pooled.n), pct(pooled.ok_3d, pooled.n), "—"],
  ],
  { ruleAbove: [3] },
);
const accLm = LANDMARKS.map((lm) => acc(lm));
const all3dMore = accLm.every((a) => a.ok_3d > a.ok_2d);
const anyAccSig = accLm.some((a) => sig(a.p_mcnemar));
const accText = para(`Of the ${pooled.n} landmark predictions, ${pct(pooled.ok_3d, pooled.n)} were within the clinically acceptable limit of ${f(MM, 0)} mm with 3D planning, compared with ${pct(pooled.ok_2d, pooled.n)} with 2D planning (Table 5). ${all3dMore ? "3D planning gave more clinically acceptable predictions at every landmark" : "The proportion of clinically acceptable predictions differed between landmarks"} (${LANDMARKS.map((lm) => { const a = acc(lm); return `${lc(lm)} ${a.ok_3d}/${a.n} vs ${a.ok_2d}/${a.n}`; }).join("; ")}, 3D vs 2D). ${anyAccSig ? "" : `However, none of the per-landmark differences reached statistical significance (McNemar _p_ = ${accLm.map((a) => f(a.p_mcnemar, 3)).join(", ")}, respectively), reflecting the small number of patients.`}`);

// ---- Table 6: among landmarks ----
const bl = R.between_landmarks;
const medIqr = (lm, m) => { const d = desc(lm, m); return `${f(d.median)} (${f(d.q1)}–${f(d.q3)})`; };
const t6 = academicTable(
  [
    { header: "Method", w: 11 }, { header: "Upper lip", w: 19 }, { header: "Lower lip", w: 19 },
    { header: "Soft-tissue pogonion", w: 19 }, { header: "Friedman _χ_² (df = 2)", w: 17 }, { header: "_p_", w: 15 },
  ],
  ["2D", "3D"].map((m) => [m, ...LANDMARKS.map((lm) => medIqr(lm, m)), f(bl[m].chi2), sigCell(bl[m].p)]),
);
const short = { "Upper lip": "upper lip", "Lower lip": "lower lip", "Soft-tissue pogonion": "pogonion" };
const posthocTxt = (m) => bl[m].posthoc.map((ph) => {
  const [a, b] = ph.pair.split(" vs ");
  return `${short[a]} vs ${short[b]} _p_ = ${f(ph.p_bonferroni, 3)}`;
}).join(", ");
const landmarkSentence = (m) => sig(bl[m].p)
  ? `differed significantly among the landmarks with ${m} planning (_χ_²(2) = ${f(bl[m].chi2)}, _p_ ${pTxt(bl[m].p)})`
  : `did not differ significantly among the landmarks with ${m} planning (_χ_²(2) = ${f(bl[m].chi2)}, _p_ ${pTxt(bl[m].p)})`;
const anyPosthocSig = ["2D", "3D"].some((m) => bl[m].posthoc.some((ph) => sig(ph.p_bonferroni)));
const fr = (m) => `${m} (_χ_²(2) = ${f(bl[m].chi2)}, _p_ ${pTxt(bl[m].p)})`;
const landmarkOpening = sig(bl["2D"].p) === sig(bl["3D"].p)
  ? `The prediction error ${sig(bl["2D"].p) ? "differed significantly" : "did not differ significantly"} among the three landmarks with ${sig(bl["2D"].p) ? "both" : "either"} ${fr("2D")} ${sig(bl["2D"].p) ? "and" : "or"} ${fr("3D")} planning (Table 6).`
  : `The prediction error ${landmarkSentence("2D")}, whereas it ${landmarkSentence("3D")} (Table 6).`;
const landmarkText = para(`${landmarkOpening} ${anyPosthocSig ? "Significant Bonferroni-adjusted pairwise differences are listed below Table 6." : "None of the Bonferroni-adjusted pairwise comparisons was significant."} With 3D planning, the median error at soft-tissue pogonion (${f(desc("Soft-tissue pogonion", "3D").median)} mm) was higher than at the upper lip (${f(desc("Upper lip", "3D").median)} mm) and lower lip (${f(desc("Lower lip", "3D").median)} mm).`);

// ---- Table 7: movement ----
const mc = R.movement_correlation;
const t7 = academicTable(
  [
    { header: "Landmark", w: 22 }, { header: "Planned movement", w: 26 }, { header: "2D _ρ_", w: 13 },
    { header: "_p_", w: 13 }, { header: "3D _ρ_", w: 13 }, { header: "_p_", w: 13 },
  ],
  LANDMARKS.map((lm) => {
    const a = mc.find((r) => r.landmark === lm && r.method === "2D");
    const b = mc.find((r) => r.landmark === lm && r.method === "3D");
    return [lm, a.movement, f(a.spearman_rho), sigCell(a.p), f(b.spearman_rho), sigCell(b.p)];
  }),
);
const anyMvSig = mc.some((r) => sig(r.p));
const rhoRange = (m) => {
  const v = mc.filter((r) => r.method === m).map((r) => r.spearman_rho);
  return `${f(Math.min(...v))} to ${f(Math.max(...v))}`;
};
const movementText = para(`${anyMvSig ? "A significant correlation between the magnitude of the planned movement and the prediction error was found for at least one landmark (Table 7)." : `No significant correlation was found between the magnitude of the planned surgical movement and the prediction error at the corresponding landmark, with either 2D (_ρ_ = ${rhoRange("2D")}) or 3D planning (_ρ_ = ${rhoRange("3D")}; all _p_ ≥ ${f(Math.min(...mc.map((r) => r.p)), 2)}) (Table 7).`} Given the small sample, this analysis is exploratory.`);

// ---- summary ----
const pUL = paired("Upper lip"), pLL = paired("Lower lip"), pPg = paired("Soft-tissue pogonion");
const summary = [
  h2("Summary of the main findings"),
  bullet(`Compared with 2D planning, 3D planning gave ${sig(pUL.p_t) ? "a significantly" : "a non-significantly"} smaller prediction error at the upper lip (mean ${f(d3("Upper lip").mean)} vs ${f(d2("Upper lip").mean)} mm; _d_z = ${f(pUL.cohen_dz)}) and ${sig(pLL.p_t) ? "a significantly" : "a non-significantly"} smaller error at the lower lip (${f(d3("Lower lip").mean)} vs ${f(d2("Lower lip").mean)} mm; _d_z = ${f(pLL.cohen_dz)}).`),
  bullet(`At soft-tissue pogonion, ${sig(pPg.p_t) ? "the two methods differed significantly" : "the two methods were equally accurate"} (${f(d3("Soft-tissue pogonion").mean)} vs ${f(d2("Soft-tissue pogonion").mean)} mm), and both showed the largest and most variable errors.`),
  bullet(`The 2D and 3D errors were ${sigCorr.length ? `significantly correlated only at the ${sigCorr.map(lc).join(" and ")}` : "not significantly correlated at any landmark"}.`),
  bullet(`${f((100 * pooled.ok_3d) / pooled.n, 0)}% of 3D predictions versus ${f((100 * pooled.ok_2d) / pooled.n, 0)}% of 2D predictions were within the clinically acceptable limit of ${f(MM, 0)} mm.`),
];

const results = [
  h1("Results"),
  h2("Sample characteristics"),
  sampleText,
  caption("Table 1.", "Patient characteristics and planned surgical movements"),
  t1,
  note("F = female; M = male; — = movement not performed. Mean ± SD of the mandibular setback and genioplasty is given for the patients who received that movement."),

  h2("Soft-tissue prediction error"),
  descText,
  caption("Table 2.", "Descriptive statistics of the soft-tissue prediction error (mm) with 2D and 3D planning"),
  t2,
  note("SD = standard deviation; CI = confidence interval; IQR = interquartile range. Overall = mean of the three landmarks for each patient."),

  h2("Comparison of prediction error between 2D and 3D planning"),
  ...compareText,
  caption("Table 3.", "Comparison of prediction error between 2D and 3D planning (paired _t_-test)"),
  t3,
  note("Mean difference = 2D − 3D; positive values indicate a larger error with 2D planning. Shapiro–Wilk test applied to the paired differences. Holm _p_ = paired _t_-test _p_ adjusted for the three landmarks. _d_z = Cohen's effect size for paired data. *Statistically significant (_p_ < 0.05)."),
  ...figure("fig1_paired.png", 6.2, "Figure 1.", "Soft-tissue prediction error with 2D and 3D planning at each landmark. Each grey line connects the 2D and 3D errors of one patient; short horizontal bars show the mean. The dashed line marks the 2 mm limit of clinical acceptability."),

  h2("Correlation between 2D and 3D prediction errors"),
  corrText,
  caption("Table 4.", "Correlation between 2D and 3D prediction errors"),
  t4,
  note("_r_ = Pearson correlation coefficient; _ρ_ = Spearman rank correlation coefficient. *Statistically significant (_p_ < 0.05)."),
  ...figure("fig2_scatter.png", 6.2, "Figure 2.", "Relationship between 2D and 3D prediction errors at each landmark. The dashed diagonal is the line of equality: points below it are patients in whom 3D planning was more accurate. _r_ = Pearson correlation coefficient."),

  h2("Clinical acceptability of the prediction"),
  accText,
  caption("Table 5.", `Number (%) of predictions within the clinically acceptable limit (≤ ${f(MM, 0)} mm)`),
  t5,
  note("†All landmark predictions pooled (three per patient); shown descriptively without a test because the three landmarks of one patient are not independent observations. *Statistically significant (_p_ < 0.05)."),

  h2("Comparison of prediction error among landmarks"),
  landmarkText,
  caption("Table 6.", "Prediction error (mm) among the three landmarks for each planning method (Friedman test)"),
  t6,
  note(`Values are median (IQR). Bonferroni-adjusted pairwise Wilcoxon tests — 2D: ${posthocTxt("2D")}; 3D: ${posthocTxt("3D")}. *Statistically significant (_p_ < 0.05).`),

  h2("Planned surgical movement and prediction error"),
  movementText,
  caption("Table 7.", "Correlation between the magnitude of the planned movement and the prediction error (exploratory)"),
  t7,
  note("_ρ_ = Spearman rank correlation coefficient; a movement that was not performed was entered as 0 mm. *Statistically significant (_p_ < 0.05)."),

  ...summary,
];

// =====================================================================
const doc = new Document({
  creator: "Statistical analysis",
  title: "Statistical methodology and results",
  styles: {
    default: { document: { run: { font: FONT, size: 24 }, paragraph: { spacing: { line: 360, lineRule: LineRuleType.AUTO } } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: FONT, size: 30, bold: true },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 120, line: 276 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: "000000" },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true, color: "000000" },
        paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 1, keepNext: true } },
    ],
  },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 540, hanging: 300 } } } }],
    }],
  },
  sections: [{
    properties: { page: { margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    children: [
      new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("Correlation Between Two-Dimensional and Three-Dimensional Virtual Planning on Soft Tissue Prediction for Orthognathic Surgery Using Dolphin 3D Software")] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [new TextRun({ text: "Statistical Methodology and Results", italics: true, size: 26 })] }),
      ...methods,
      ...results,
    ],
  }],
});

const outFile = path.join(outDir, "Statistical_Methodology_and_Results.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outFile, buf);
  console.log(`Wrote ${outFile}`);
});
