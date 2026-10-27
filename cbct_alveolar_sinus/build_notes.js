// Builds the revision notes (revised Table 9, manuscript changes, Figures 2-5)
// from the output of analysis.py.
//
// Usage: node build_notes.js <output_dir>
// Reads <output_dir>/results.json and the figure PNGs, writes
// <output_dir>/Revision_notes_Table9_and_Figures.docx

const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, HeadingLevel, ImageRun, LevelFormat, LineRuleType,
  Packer, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, VerticalAlign, WidthType,
} = require("docx");

const outDir = process.argv[2];
if (!outDir) {
  console.error("Usage: node build_notes.js <output_dir>");
  process.exit(1);
}
const R = JSON.parse(fs.readFileSync(path.join(outDir, "results.json"), "utf8"));
const T9 = R.table9;
const TOT = T9.Total.pearson;

const FONT = "Times New Roman";
const PAGE_W = 12240; // US Letter, as in the manuscript
const MARGIN = 1440;
const CONTENT_W = PAGE_W - 2 * MARGIN;
const CHANGED = "FFF2CC"; // shading for cells that differ from the manuscript

const f = (x, d = 1) => Number(x).toFixed(d);
const pTxt = (p) => (p < 0.001 ? "p < 0.001" : `p = ${f(p, 3)}`);
const chiTxt = (t) => `χ²(${t.df}) = ${f(t.chi2, 2)}, ${pTxt(t.p)}`;

// ---------- paragraphs ----------
const para = (children, opts = {}) => new Paragraph({ spacing: { after: 120 }, ...opts, children });
const text = (s, o = {}) => new TextRun({ text: s, ...o });
const h1 = (s, pageBreakBefore = false) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore, spacing: { before: 280, after: 140 }, children: [text(s)] });
const h2 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 100 }, children: [text(s)] });
const bullet = (children) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 80 }, children });

// A "current text -> revised text" block for one manuscript change.
function change(n, where, current, revised, why) {
  const out = [
    new Paragraph({ spacing: { before: 200, after: 80 }, keepNext: true,
      children: [text(`${n}. `, { bold: true }), text(where, { bold: true })] }),
  ];
  if (current) {
    out.push(new Paragraph({ indent: { left: 360 }, spacing: { after: 80 }, keepNext: true,
      children: [text("Current: ", { bold: true, color: "595959" }), text(current, { italics: true, color: "595959" })] }));
  }
  out.push(new Paragraph({ indent: { left: 360 }, spacing: { after: 80 }, keepNext: Boolean(why),
    children: [text("Revised: ", { bold: true }), ...(Array.isArray(revised) ? revised : [text(revised)])] }));
  if (why) {
    out.push(new Paragraph({ indent: { left: 360 }, spacing: { after: 120 },
      children: [text("Why: ", { bold: true, size: 22, color: "595959" }), text(why, { size: 22, color: "595959" })] }));
  }
  return out;
}

// ---------- Table 9 ----------
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const THICK = { style: BorderStyle.SINGLE, size: 12, color: "000000" };
const THIN = { style: BorderStyle.SINGLE, size: 6, color: "000000" };
const r10 = (s, o = {}) => new TextRun({ text: s, size: 20, ...o });
const WIDTHS = [1500, 1100, 1250, 1150, 1150, 1150, 900, 1160];

function cell(runs, col, opts = {}) {
  const { top = NONE, bottom = NONE, span = 1, rowSpan = 1, align = AlignmentType.CENTER, shade, bold } = opts;
  const width = WIDTHS.slice(col, col + span).reduce((a, b) => a + b, 0);
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    columnSpan: span,
    rowSpan,
    verticalAlign: VerticalAlign.CENTER,
    borders: { top, bottom, left: NONE, right: NONE },
    margins: { top: 50, bottom: 50, left: 70, right: 70 },
    shading: shade ? { fill: shade, type: ShadingType.CLEAR, color: "auto" } : undefined,
    children: [new Paragraph({ alignment: align, spacing: { after: 0, line: 240, lineRule: LineRuleType.AUTO },
      children: typeof runs === "string" ? [r10(runs, { bold })] : runs })],
  });
}

const countCell = (n, pct, letter) => [r10(String(n)), ...(letter ? [r10(letter, { superScript: true })] : []), r10(` (${f(pct)})`)];

const GROUPS = ["First premolars", "Second premolars", "First molars", "Second molars"];
const ETH = ["Malay", "Chinese", "Indian"];

function table9() {
  const rows = [
    new TableRow({ tableHeader: true, children: [
      cell("Tooth group", 0, { top: THICK, bottom: THIN, rowSpan: 2, align: AlignmentType.LEFT, bold: true }),
      cell("Ethnicity", 1, { top: THICK, bottom: THIN, rowSpan: 2, align: AlignmentType.LEFT, bold: true }),
      cell("Vertical sinus relationship, N (%)", 2, { top: THICK, span: 4, bold: true }),
      cell("Total", 6, { top: THICK, bottom: THIN, rowSpan: 2, bold: true }),
      cell("p-value", 7, { top: THICK, bottom: THIN, rowSpan: 2, bold: true }),
    ] }),
    new TableRow({ tableHeader: true, children: ["Type 0", "Type 1", "Type 2", "Type 3"].map((t, i) =>
      cell(t, 2 + i, { bottom: THIN, bold: true })) }),
  ];
  for (const g of [...GROUPS, "Total"]) {
    const d = T9[g];
    const isTotal = g === "Total";
    d.counts.forEach((counts, e) => {
      const top = isTotal && e === 0 ? THIN : NONE;
      const bottom = isTotal && e === 2 ? THICK : NONE;
      const children = [];
      if (e === 0) {
        children.push(cell(isTotal ? "Total" : g, 0, { top, bottom: isTotal ? THICK : NONE, rowSpan: 3, align: AlignmentType.LEFT }));
      }
      children.push(cell(ETH[e], 1, { top, bottom, align: AlignmentType.LEFT }));
      counts.forEach((n, t) => {
        const letter = isTotal ? null : d.letters[e][t];
        // The one letter that differs from the manuscript (SPSS output: "a").
        const fixed = g === "Second molars" && e === 1 && t === 0;
        // Cells whose parentheses were mistyped in the manuscript.
        const typo = (g === "First premolars" && e === 1 && t === 0) || (g === "First premolars" && e === 2 && t === 3);
        children.push(cell(countCell(n, d.row_pct[e][t], letter), 2 + t, { top, bottom, shade: fixed || typo ? CHANGED : undefined }));
      });
      children.push(cell(String(d.row_n[e]), 6, { top, bottom }));
      if (e === 0) {
        const p = isTotal ? f(TOT.p, 3) : f(d.p_reported, 3);
        children.push(cell(p, 7, { top, bottom: isTotal ? THICK : NONE, rowSpan: 3, shade: isTotal ? CHANGED : undefined }));
      }
      rows.push(new TableRow({ cantSplit: true, children }));
    });
  }
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: WIDTHS, rows });
}

// ---------- figures ----------
function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function figure(stem, n, caption) {
  const file = path.join(outDir, `${stem}.png`);
  const { w, h } = pngSize(file);
  const width = 600; // px at 96 dpi = 6.25 in
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 80 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file),
        transformation: { width, height: Math.round((width * h) / w) },
        altText: { title: `Figure ${n}`, description: caption, name: stem } })] }),
    new Paragraph({ spacing: { after: 240 }, children: [text(`Figure ${n}. `, { bold: true }), text(caption)] }),
  ];
}

const CAPTIONS = {
  2: "Prevalence of root fenestration and dehiscence by tooth group. Bars show the percentage of teeth affected, with 95% confidence intervals (Wilson); n, number of teeth examined. p-values: chi-square test comparing tooth groups.",
  3: "Prevalence of root fenestration and dehiscence by age group. Points show the percentage of teeth affected, with 95% confidence intervals (Wilson); n, number of teeth examined in each age group.",
  4: "Vertical sinus–root relationship by tooth group. Bars show the percentage of roots of each type; n, number of roots. Type 0, no contact with the sinus floor; Type 1, contact; Type 2, lateral projection along the sinus with the apex outside it; Type 3, apical protrusion into the sinus. The distribution differed between tooth groups (chi-square test, p < 0.001; Table 7).",
  5: "Vertical sinus–root relationship by ethnicity, for each tooth group and for all tooth groups pooled. Bars show the percentage of roots of each type; n, number of roots. p-values: Fisher–Freeman–Halton exact test within tooth groups; chi-square test for all tooth groups pooled (Table 9).",
};

// ---------- content ----------
const sp = T9["Second premolars"];
const sm = T9["Second molars"];
const fm = T9["First molars"];
const rows = (g) => T9[g].row_pct;
const trend = R.age_tests;

const discussionRevised =
  `When all tooth groups were pooled, ethnicity was not significantly associated with the vertical root–sinus relationship (${chiTxt(TOT)}). ` +
  `Within tooth groups, significant differences were found in second premolars (p = ${f(sp.p_reported, 3)}), first molars (p = ${f(fm.p_reported, 3)}) and second molars (p = ${f(sm.p_reported, 3)}), but not in first premolars (p = ${f(T9["First premolars"].p_reported, 3)}). ` +
  `In second premolars, apical protrusion (Type 3) was more frequent in Malay than in Chinese participants (${f(rows("Second premolars")[0][3])}% vs ${f(rows("Second premolars")[1][3])}%), whereas Chinese participants more often showed no contact (Type 0: ${f(rows("Second premolars")[1][0])}% vs ${f(rows("Second premolars")[0][0])}%). ` +
  `In second molars, Type 0 was more frequent in Indian participants (${f(rows("Second molars")[2][0])}%) than in Malay (${f(rows("Second molars")[0][0])}%) or Chinese (${f(rows("Second molars")[1][0])}%) participants.`;

const changes = [
  ...change(1, "Table 9 (cells, total row and footnote)", null,
    "Replace Table 9 with the revised table in section 2. Three things change: the total row gets its p-value (p = " + f(TOT.p, 3) +
    "); second molars, Chinese, Type 0 becomes 12ᵃ (27.9) instead of 12ᵇ (27.9), as in the SPSS output; and the typos 93ᵃ ((81.6) and 1ᵃ 5.6) are corrected. The footnote is extended to name the tests.",
    "The total row had no test; the letter and typos are transcription errors."),
  ...change(2, "Results, paragraph before Table 8 (sentence on Table 9)",
    "Table 9 shows that the distribution of vertical sinus relationship types varied by ethnicity, with significant differences detected in several tooth groups overall (second premolars p = 0.019, first molars p = 0.027, second molars p = 0.032).",
    `Table 9 and Figure 5 show that the distribution of vertical sinus relationship types varied by ethnicity within second premolars (p = ${f(sp.p_reported, 3)}), first molars (p = ${f(fm.p_reported, 3)}) and second molars (p = ${f(sm.p_reported, 3)}), but not within first premolars (p = ${f(T9["First premolars"].p_reported, 3)}). When all tooth groups were pooled, ethnicity was not significantly associated with the vertical relationship (${chiTxt(TOT)}).`,
    "Adds the pooled result and removes “overall”, which implied a significant pooled test."),
  ...change(3, "Discussion, paragraph beginning “Ethnicity was significantly associated…” (first two sentences)",
    "Ethnicity was significantly associated with the vertical root–sinus relationship in this cohort (χ²(6)=18.94, p=0.004). Chinese and Indian participants showed a higher frequency of Type 0 (no contact), whereas Malay participants demonstrated a higher frequency of Type 3 (apical protrusion).",
    discussionRevised + " Keep the rest of the paragraph from “Maxillary sinus dimensions vary by ethnicity…”.",
    "χ²(6) = 18.94, p = 0.004 cannot be reproduced from the Table 9 counts; it came from an earlier, error-flagged table in the statistics workbook. In both molar groups the three ethnic groups share the same letter for Type 3, so “Type 3 more frequent in Malay” holds only for second premolars."),
  ...change(4, "Clinical Implications for Risk-Specific Treatment Planning, second paragraph",
    "In populations such as Malay patients, where Type 3 root–sinus relationships are more prevalent, bone augmentation or grafting may be necessary prior to extensive orthodontic movement or implant placement (35).",
    "Where roots protrude into the sinus (Type 3), as seen most often in maxillary first molars, bone augmentation or grafting may be necessary prior to extensive orthodontic movement or implant placement (35).",
    `Type 3 was most frequent in first molars (${f(R.table7["First molars"].pct[3])}% of roots; Table 7), not tied to one ethnic group.`),
  ...change(5, "Conclusions",
    "In terms of demographics, Type 2 relationships were significantly more frequent in older age groups, and Type 3 relationships were more frequent among Malay patients.",
    "In terms of demographics, Type 2 relationships were significantly more frequent in older age groups. Ethnicity was not associated with the vertical relationship overall, although in second premolars Type 3 relationships were more frequent among Malay than Chinese patients.",
    null),
  ...change(6, "Abstract (optional)",
    "Additionally, apical protrusions were descriptively more frequent among Malay patients.",
    `Apical protrusions were more frequent among Malay patients, although the overall association with ethnicity was not significant (p = ${f(TOT.p, 3)}).`,
    "The current wording is already correct; this version states the p-value."),
  ...change(7, "Methods, Statistical analysis (add after “…where significant differences were detected.”)", null,
    "Within tooth groups, the association between ethnicity and vertical sinus relationship was tested with the Fisher–Freeman–Halton exact test; for all tooth groups pooled, the chi-square test was used because all expected counts were ≥ 5. Changes in prevalence across age groups were assessed with the chi-square test for trend. In the figures, proportions are shown with 95% confidence intervals calculated by the Wilson score method.",
    "Names the tests behind the new total-row p-value and the age-trend p-values (change 13), and the confidence intervals in Figures 2–3."),
  ...change(8, "Limitations (add at the end of the paragraph)", null,
    "In addition, the Indian subgroup was small (17 patients; 59 roots), so comparisons involving this group have limited precision. Analyses were performed at tooth and root level, and several teeth and roots came from the same patient; because these observations are not fully independent, p-values may be somewhat optimistic.",
    "Reviewers commonly raise both points."),
  new Paragraph({ spacing: { before: 200, after: 80 }, keepNext: true, children: [text("9. Figure call-outs in Results", { bold: true })] }),
  bullet([text("Root fenestration paragraph: “…and second molars (4/33, 12.12%)” → “…and second molars (4/33, 12.12%; Figure 2)”.")]),
  bullet([text("Dehiscence paragraph: “The distribution differed by tooth groups (χ² test, p < 0.001).” → “…(χ² test, p < 0.001; Figure 2).”")]),
  bullet([text("“Table 2 shows that RF prevalence was broadly comparable…” → “Table 2 and Figure 3 show that RF prevalence was broadly comparable…”")]),
  bullet([text("“Table 5 shows that an age gradient was observed for dehiscence…” → “Table 5 and Figure 3 show that an age gradient was observed for dehiscence…”")]),
  bullet([text("“Table 7 shows that the vertical sinus relationship differed significantly by tooth group…” → “Table 7 and Figure 4 show that…”")]),
  bullet([text("Figure 5 is cited in change 2.")]),
  new Paragraph({ spacing: { before: 200, after: 80 }, keepNext: true, children: [text("10. Figure legends", { bold: true })] }),
  para([text("Add the legends of Figures 2–5 (section 4) below each figure. Place each figure after the paragraph that first cites it, or at the end of the manuscript if the journal asks for figures separately, and upload the TIFF files as the figure files.")], { indent: { left: 360 } }),
  ...change(11, "Results, root fenestration (wording of the tooth-group test)",
    "First premolars are significantly more affected than second premolars (χ² test, p = 0.024).",
    "RF prevalence differed among tooth groups (χ² test, p = 0.024); post hoc comparison showed that first premolars were more affected than second premolars.",
    "p = 0.024 is the overall test across the four tooth groups, not the first-versus-second premolar comparison."),
  ...change(12, "Results, dehiscence severity",
    "…with mild defects being the most frequent observation (100/188, 53.5%).",
    "…with mild defects being the most frequent observation (100/187, 53.5%).",
    "Table 4 totals 187 root surfaces, and 100/187 is the 53.5% reported."),
  ...change(13, "Results, Table 2 and Table 5 sentences (age trend)",
    "…broadly comparable across age strata (17.65%-23.26%), peaking… / …to 37/70 (52.86%) in the >50 group.",
    `…broadly comparable across age strata (17.65%-23.26%; χ² test for trend, p = ${f(trend.rf_trend.p, 3)}), peaking… / …to 37/70 (52.86%) in the >50 group (χ² test for trend, p < 0.001).`,
    `The Abstract and Conclusions state that dehiscence increased with age but no test was reported. From the Table 2 and 5 totals: dehiscence χ²(1) = ${f(trend.deh_trend.chi2, 2)}, p < 0.001; RF χ²(1) = ${f(trend.rf_trend.chi2, 2)}, p = ${f(trend.rf_trend.p, 3)}.`),
];

const openIssues = [
  bullet([text("Table 7 and Table 9 disagree in three cells: ", { bold: true }),
    text("first premolars Type 1 (22 vs 21), first molars Type 0 (51 vs 50) and second molars Type 1 (33 vs 35); tooth-group totals 243/207/108 vs 242/206/110. Both total 711. Table 9 matches the SPSS ethnicity output, and the SPSS root-level output also has 21 for first premolars Type 1, so Table 7 is the likelier one to be wrong. Figure 4 uses Table 7 and Figure 5 uses Table 9 as published; once the counts are reconciled, the figures can be redrawn in a minute. (Comment on the Table 7 title.)")]),
  bullet([text("Gender and first premolars: ", { bold: true }), text("χ²(3) = 12.18, p = 0.007 could not be reproduced from the gender counts in the statistics workbook (χ²(3) = 11.38, p = 0.010; still significant). Those counts also sum to Type 2 = 21 where Table 7 has 20. Please check against the SPSS output. (Comment on the χ² value in the Results.)")]),
];

const doc = new Document({
  creator: "Statistics revision",
  title: "Revision notes: Table 9, manuscript text and Figures 2–5",
  styles: {
    default: { document: { run: { font: FONT, size: 24 }, paragraph: { spacing: { line: 276, lineRule: LineRuleType.AUTO } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: "000000" }, paragraph: { outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true, color: "000000" }, paragraph: { outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 15840 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    children: [
      new Paragraph({ spacing: { after: 80 }, children: [text("Revision notes: Table 9, manuscript text and Figures 2–5", { bold: true, size: 30 })] }),
      new Paragraph({ spacing: { after: 240 }, children: [text("Evaluation of Bone Fenestration, Dehiscence, and Maxillary Sinus Proximity in Maxillary Posterior Teeth: A CBCT Study on a Malaysian Subpopulation", { italics: true })] }),

      h1("1. Summary"),
      bullet([text("Table 9 total row: ", { bold: true }), text(`${chiTxt(TOT)} (Pearson chi-square, computed from the Table 9 counts; all expected counts ≥ 5). The pooled association between ethnicity and vertical sinus relationship is not significant.`)]),
      bullet([text("Discussion p-value: ", { bold: true }), text("χ²(6) = 18.94, p = 0.004 cannot be reproduced from any version of the counts. It came from an earlier, error-flagged ethnicity table in the statistics workbook and should be replaced (change 3).")]),
      bullet([text("Table 9 corrections: ", { bold: true }), text("one superscript letter (second molars, Chinese, Type 0: b → a, as in the SPSS output) and two typos.")]),
      bullet([text("Figures 2–5: ", { bold: true }), text("drawn from the published tables only; no raw data were used. Files are supplied as 600 dpi TIFF and PNG and as vector PDF.")]),
      bullet([text("Tracked manuscript: ", { bold: true }), text("changes 1–13 are applied as tracked changes (author “Claude”) in the manuscript copy, with Figures 2–5 and their legends inserted. The two items that need the SPSS output are Word comments (end of section 3).")]),
      bullet([text("Checks: ", { bold: true }), text(`the four tooth-group p-values in Table 9 were re-computed with the Fisher–Freeman–Halton exact test (Monte Carlo, ${R.settings.mc_simulations.toLocaleString("en-US")} samples) and agree with the reported values: ${GROUPS.map((g) => f(T9[g].ffh_exact_mc, 3)).join(", ")} vs ${GROUPS.map((g) => f(T9[g].p_reported, 3)).join(", ")}.`)]),

      h1("2. Revised Table 9", true),
      para([text("Table 9 ", { bold: true }), text("Chi square analysis for ethnicity and vertical sinus relationship according to tooth group")], { keepNext: true }),
      table9(),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [r10(
        `N = number of roots; percentages are within each ethnic group. Within each tooth group and sinus type, ethnic groups sharing a superscript letter do not differ significantly (pairwise comparisons of proportions, Bonferroni-adjusted). p-values: Fisher–Freeman–Halton exact test within tooth groups; Pearson chi-square test for the total (χ²(${TOT.df}) = ${f(TOT.chi2, 2)}; all expected counts ≥ 5). Post hoc letters are not shown for the total because the overall test was not significant.`)] }),
      new Paragraph({ spacing: { after: 200 }, children: [r10("Shaded cells differ from the current manuscript (shading is for review only; remove it in the manuscript).", { italics: true, color: "595959" })] }),

      h1("3. Changes to the manuscript", true),
      ...changes,

      h2("Left as comments in the manuscript (need the SPSS output)"),
      ...openIssues,

      h1("4. Figures 2–5", true),
      ...figure("fig2_alveolar_by_tooth", 2, CAPTIONS[2]),
      ...figure("fig3_alveolar_by_age", 3, CAPTIONS[3]),
      ...figure("fig4_sinus_by_tooth", 4, CAPTIONS[4]),
      ...figure("fig5_sinus_by_ethnicity", 5, CAPTIONS[5]),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(outDir, "Revision_notes_Table9_and_Figures.docx");
  fs.writeFileSync(out, buf);
  console.log(`Wrote ${out}`);
});
