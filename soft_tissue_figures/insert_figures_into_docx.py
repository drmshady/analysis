import copy, re, sys
import docx
from docx.shared import Inches

src, figdir, out = sys.argv[1:4]
d = docx.Document(src)
els = list(d.element.body.iterchildren())
P = lambda el: docx.text.paragraph.Paragraph(el, d)
img_tpl, cap_tpl = els[36], els[37]
assert img_tpl.xpath('.//w:drawing') and P(cap_tpl).text.startswith('Figure 1.')
notes = {1: els[24], 2: els[29], 3: els[35], 4: els[42], 5: els[49], 6: els[54], 7: els[59]}
for k, el in notes.items():   # each note directly follows its table
    assert el.getprevious().tag.endswith('}tbl'), k

CAP = {
 1: ("Figure_T1_patient_characteristics", "Planned surgical movements of each patient (data of Table 1). Bars show the planned maxillary advancement, mandibular setback and genioplasty advancement; the legend gives the mean ± SD for the patients who received each movement. — = movement not performed."),
 2: ("Figure_T2_descriptive_prediction_error", "Soft-tissue prediction error with 2D and 3D planning (data of Table 2). Dot = mean (labelled mean ± SD); thick bar = 95% CI; shaded box = median (IQR); thin line = range. The dashed line marks the 2 mm limit of clinical acceptability."),
 3: ("Figure_T3_mean_difference_forest", "Mean difference in prediction error between 2D and 3D planning (2D − 3D) with 95% CI (data of Table 3). Positive values indicate a smaller error with 3D planning. Coloured estimates are statistically significant (paired _t_-test, _p_ < 0.05); paired _t_-test _p_, Holm-adjusted _p_ and Cohen's _d_z are listed alongside."),
 4: ("Figure_T4_correlation_2D_3D", "Correlation between the 2D and 3D prediction errors (data of Table 4). Shaded bands mark weak (< 0.3), moderate (0.3–0.7) and strong (> 0.7) correlation. _r_ = Pearson correlation coefficient; _ρ_ = Spearman rank correlation coefficient. *Statistically significant (_p_ < 0.05)."),
 5: ("Figure_T5_clinical_acceptability", "Percentage of predictions within the clinically acceptable limit of 2 mm with 2D and 3D planning (data of Table 5), with the exact McNemar _p_ for each landmark. The pooled column is descriptive only."),
 6: ("Figure_T6_landmark_comparison_friedman", "Prediction error among the three landmarks for each planning method (data of Table 6). Boxes show the median (IQR); the Friedman test result is given above each panel and brackets show the Bonferroni-adjusted pairwise Wilcoxon _p_ values. The dashed line marks the 2 mm limit."),
 7: ("Figure_T7_movement_vs_error", "Spearman rank correlation (_ρ_) between the magnitude of the planned surgical movement and the prediction error at the corresponding landmark (data of Table 7; exploratory). No correlation was statistically significant."),
}

def make_caption(label, text):
    p = copy.deepcopy(cap_tpl)
    runs = p.xpath('./w:r')
    bold, body = runs[0], runs[1]
    for r in runs[1:]:
        p.remove(r)
    bold.xpath('./w:t')[0].text = f"Figure {label}. "
    for i, seg in enumerate(re.split(r'_', text)):
        if not seg:
            continue
        r = copy.deepcopy(body)
        rpr = r.find(docx.oxml.ns.qn('w:rPr'))
        for tag in ('w:i', 'w:iCs'):
            for x in rpr.findall(docx.oxml.ns.qn(tag)):
                rpr.remove(x)
        if i % 2:
            rpr.insert(0, docx.oxml.OxmlElement('w:i'))
        r.xpath('./w:t')[0].text = seg
        r.xpath('./w:t')[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        p.append(r)
    return p

def make_image(png):
    para = d.add_paragraph()
    para.add_run().add_picture(png, width=Inches(6.2))
    el = para._p
    el.remove(el.find(docx.oxml.ns.qn('w:pPr'))) if el.find(docx.oxml.ns.qn('w:pPr')) is not None else None
    el.insert(0, copy.deepcopy(img_tpl.find(docx.oxml.ns.qn('w:pPr'))))
    return el

# new numbering in reading order
NEWNUM = {1: 1, 2: 2, 3: 3, 4: 5, 5: 7, 6: 8, 7: 9}
for k, (name, text) in CAP.items():
    img = make_image(f"{figdir}/{name}.png")
    cap = make_caption(NEWNUM[k], text)
    notes[k].addnext(img)
    img.addnext(cap)

# renumber existing figures 1 -> 4, 2 -> 6
for el, n in [(els[37], 4), (els[44], 6)]:
    t = el.xpath('./w:r/w:t')[0]
    assert t.text.startswith('Figure '), t.text
    t.text = f"Figure {n}. "

# update in-text references
REF = {
 21: [("(Table 1)", "(Table 1, Figure 1)")],
 26: [("Table 2 summarises", "Table 2 and Figure 2 summarise")],
 32: [("(Figure 1)", "(Figure 4)")],
 39: [("(Table 4, Figure 2)", "(Table 4; Figures 5 and 6)")],
 46: [("(Table 5)", "(Table 5, Figure 7)")],
 51: [("(Table 6)", "(Table 6, Figure 8)")],
 56: [("(Table 7)", "(Table 7, Figure 9)")],
}
for i, subs in REF.items():
    for a, b in subs:
        hits = [t for t in els[i].xpath('.//w:t') if a in t.text]
        assert len(hits) == 1, (i, a)
        hits[0].text = hits[0].text.replace(a, b)

# Table 3 is not cited in the text: cite it with its new figure
t31 = [t for t in els[31].xpath('.//w:t') if 'every comparison.' in t.text]
assert len(t31) == 1
t31[0].text = t31[0].text.replace("every comparison.", "every comparison (Table 3, Figure 3).")
d.save(out)
print("saved", out)
