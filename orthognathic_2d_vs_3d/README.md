# 2D vs 3D soft-tissue prediction (Dolphin 3D) — statistics

Re-run after the data sheet changes:

```bash
pip install pandas numpy scipy statsmodels matplotlib openpyxl
python analysis.py Final_for_statistic.xlsx output   # tables, figures, results.json
node build_report.js output                            # needs the `docx` npm package
soffice --headless --convert-to pdf --outdir output output/Statistical_Methodology_and_Results.docx
python make_package.py output                          # zip: report, tables, figures
```

Figures are written at 600 dpi (PNG and LZW TIFF) and as vector PDF.

`output/Statistical_Methodology_and_Results.docx` is the methodology and results
chapter; every number and significance statement in it is read from
`output/results.json`. The patient workbook is not stored here (it contains
names); `output/data_tidy.csv` is the anonymised copy.
