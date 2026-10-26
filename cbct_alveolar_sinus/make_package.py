"""Bundle the revision notes and the high-resolution figures into one zip.

Usage: python make_package.py <output_dir>
"""

import sys
import zipfile
from pathlib import Path

CONTENTS = {
    "Revision_notes_Table9_and_Figures.docx": "Revision_notes_Table9_and_Figures.docx",
}
FIGURES = {
    "fig2_alveolar_by_tooth": "Figure_2_alveolar_defects_by_tooth_group",
    "fig3_alveolar_by_age": "Figure_3_alveolar_defects_by_age_group",
    "fig4_sinus_by_tooth": "Figure_4_sinus_relationship_by_tooth_group",
    "fig5_sinus_by_ethnicity": "Figure_5_sinus_relationship_by_ethnicity",
}

out_dir = Path(sys.argv[1])
zip_path = out_dir / "CBCT_Table9_and_Figures_package.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for src, name in CONTENTS.items():
        z.write(out_dir / src, name)
    for src, name in FIGURES.items():
        for ext in (".tif", ".png", ".pdf"):
            z.write(out_dir / f"{src}{ext}", f"Figures/{name}{ext}")
print(f"Wrote {zip_path}")
