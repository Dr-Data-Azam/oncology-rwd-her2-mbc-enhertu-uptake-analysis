"""Report generation: notebook → HTML and slide deck (.pptx).

Responsibility:
    Export the Jupyter notebook to a self-contained HTML file using nbconvert.
    Build the five-slide + three-appendix .pptx deck from pipeline outputs via
    python-pptx, following the rules in the deck-builder skill:
    - Slide titles are finding sentences, not topic labels
    - Every number on a slide is sourced from a CSV in outputs/tables/
    - No number is typed by hand; all values are read from the output tables
    - Small cells (n < threshold) are flagged with "n<11" per ADR-012

    The PDF copy is produced with LibreOffice headless if available, else
    skipped with a logged warning.

Inputs:
    notebooks/analysis.ipynb (executed)
    outputs/tables/*.csv and outputs/figures/*.png

Outputs:
    reports/HER2_mBC_Enhertu_Assessment.pptx
    reports/HER2_mBC_Enhertu_Assessment.pdf  (if LibreOffice available)
    reports/analysis_notebook.html

ADRs implemented: none (presentation layer)
"""
