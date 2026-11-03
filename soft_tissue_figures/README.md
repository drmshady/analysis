# Figures for Tables 1–7

Figures built from the values in *Statistical Methodology and Results*
(2D vs 3D soft-tissue prediction, Dolphin 3D). Regenerate with
`python make_figures.py` (needs matplotlib, numpy; Inter font). Each figure is in
`figures/` as a 300-dpi PNG and a vector PDF.

Suggested captions (they assume the new figures follow the existing Figures 1–2; renumber to fit the manuscript):

- **Table 1 → Figure_T1_patient_characteristics**: Planned maxillary advancement, mandibular setback and genioplasty advancement for each patient, with sex and age. The legend gives mean ± SD for the patients who received each movement; — marks a movement that was not performed.
- **Table 2 → Figure_T2_descriptive_prediction_error**: Soft-tissue prediction error with 2D and 3D planning. Dot = mean (labelled mean ± SD), thick bar = 95% CI, shaded box = median (IQR), thin line = range. The dashed line marks the 2 mm limit of clinical acceptability.
- **Table 3 → Figure_T3_mean_difference_forest**: Mean difference in prediction error (2D − 3D) with 95% CI. Positive values mean 3D planning was more accurate. Coloured estimates are significant (paired t-test, p < 0.05); the paired t-test p, Holm-adjusted p and Cohen's dz are listed beside each estimate.
- **Table 4 → Figure_T4_correlation_2D_3D**: Pearson r and Spearman ρ between the 2D and 3D prediction errors. Shaded bands mark weak (< 0.3), moderate (0.3–0.7) and strong (> 0.7) correlation. *p < 0.05.
- **Table 5 → Figure_T5_clinical_acceptability**: Percentage of predictions within 2 mm with 2D and 3D planning, with exact McNemar p for each landmark. The pooled column is descriptive only.
- **Table 6 → Figure_T6_landmark_comparison_friedman**: Median (IQR) prediction error at each landmark, by planning method, with the Friedman test result in each panel title. Brackets show Bonferroni-adjusted pairwise Wilcoxon p values.
- **Table 7 → Figure_T7_movement_vs_error**: Spearman ρ between the size of the planned surgical movement and the prediction error at the matching landmark (exploratory). No correlation was significant.
