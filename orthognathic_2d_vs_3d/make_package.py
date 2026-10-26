"""Bundle the report, result tables and high-resolution figures into one zip.

Usage: python make_package.py <output_dir>
"""

import sys
import zipfile
from pathlib import Path

CONTENTS = {
    "Statistical_Methodology_and_Results.docx": "Statistical_Methodology_and_Results.docx",
    "Statistical_Methodology_and_Results.pdf": "Statistical_Methodology_and_Results.pdf",
    "results.xlsx": "Results_tables.xlsx",
}
FIGURES = {
    "fig1_paired": "Figure_1_prediction_error_2D_vs_3D",
    "fig2_scatter": "Figure_2_correlation_2D_vs_3D",
}

out_dir = Path(sys.argv[1])
zip_path = out_dir / "Statistics_2D_vs_3D_package.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for src, name in CONTENTS.items():
        z.write(out_dir / src, name)
    for src, name in FIGURES.items():
        for ext in (".png", ".tif", ".pdf"):
            z.write(out_dir / f"{src}{ext}", f"Figures/{name}{ext}")
print(f"Wrote {zip_path}")
