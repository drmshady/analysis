# CBCT fenestration, dehiscence and sinus proximity: Table 9 and figures

Revised Table 9 (total-row p-value), the manuscript changes that follow from it,
and Figures 2–5 for the manuscript "Evaluation of Bone Fenestration, Dehiscence,
and Maxillary Sinus Proximity in Maxillary Posterior Teeth: A CBCT Study on a
Malaysian Subpopulation".

No patient-level data are used. The counts in `analysis.py` are copied from the
manuscript (Tables 2, 5, 7 and 9 and the Results text). If a table changes, edit
the counts there and re-run:

```bash
pip install numpy scipy statsmodels matplotlib
python analysis.py output        # results.json and Figures 2-5
node build_notes.js output       # needs the `docx` npm package
python make_package.py output    # zip: revision notes and figures
```

Figures are written at 600 dpi (PNG and LZW TIFF) and as vector PDF.

`output/Revision_notes_Table9_and_Figures.docx` holds the revised Table 9, each
manuscript change (current and revised text), other inconsistencies to check,
and Figures 2–5 with legends. Every number in it is read from
`output/results.json`.

The Table 9 total-row p-value is a Pearson chi-square test on the pooled counts
(all expected counts ≥ 5). The tooth-group p-values are the reported SPSS exact
values; `analysis.py` re-checks them with a seeded Monte Carlo
Fisher–Freeman–Halton test.
