# Candidate Facing Instructions (verbatim text extraction)

> Source: `candidate_facing_instructions.docx` (copy of `../../../../external/candidate_facing_instructions.docx`, READ-ONLY original). Text only; formatting not preserved.

## Senior Data Scientist Technical Assessment: Synthetic Oncology Real-World Data Exercise

## Overview

You have been provided a fully synthetic oncology real-world data dataset representing a multi-site provider network with both structured EHR and expert-curated records. The dataset is intentionally designed to resemble a production-style analytical asset while remaining entirely synthetic. The exercise focuses on metastatic breast cancer, HER2 testing, HER2-expression subcategories, and treatment uptake for trastuzumab deruxtecan (Enhertu) relative to selected competitor therapies.

## Files Provided

- patient.csv

- diagnosis.csv

- staging.csv

- biomarker.csv

- medication.csv

- data_dictionary.xlsx

## Dataset Context

- The dataset is breast-cancer dominant and designed to support HER2-focused metastatic breast cancer analytics.

- Both structured EHR (curation_flag = 0) and expert-curated (curation_flag = 1) records are present.

- Some fields are deliberately incomplete or discordant to reflect real-world data complexity.

- Clinical time windows matter. Biomarker, diagnosis, stage, and treatment records do not always align perfectly to the same calendar date.

## Rules of Engagement

- You may use SQL, Python, R, or a combination of these tools.

- If using SQL, you may load the CSV files into your preferred local analytical engine (for example: SQLite, DuckDB, PostgreSQL, or similar).

- State all assumptions clearly and document any tie-break rules used when multiple candidate records exist for the same patient and analytic event.

- Your submission should be reproducible. Include enough code and explanation for another analyst to rerun your work.

- Focus on analytical rigor, data quality reasoning, and defensible clinical logic rather than cosmetic visualization.

## Submission Requirements

- Source code used to complete the assessment

- A concise slide deck or written summary (recommended maximum: 5  slides or 2 pages)

- One appendix section or slide that documents your data quality checks and key assumptions

- Any supporting output tables or figures needed to explain your results

## Presentation Expectations

- Be prepared to present for 20–30 minutes.

- You should walk through your implementation approach, assumptions, validation steps, and final conclusions.

- You will be asked follow-up questions about tradeoffs, alternative definitions, and how you would productionize the analysis.

## Question 1: Data Feasibility and HER2 Distribution at Metastatic Diagnosis

- Construct an analysis-ready metastatic breast cancer cohort and estimate the distribution of HER2 status at the time of metastatic diagnosis. Your analysis must classify patients into HER2-positive, HER2-low, HER2-ultralow, HER2-0/null, or unknown/indeterminate using the records provided.

- Define a metastatic breast cancer cohort using diagnosis and/or stage evidence. Clearly explain how you define the metastatic index date.

- Determine HER2 status at metastatic diagnosis using biomarker records in a clinically justified time window around the metastatic index date.

- Resolve situations with multiple HER2 records, discordant records, ambiguous records, and records with incomplete variant detail.

- Characterize the overall HER2 distribution and stratify it by at least three additional factors such as hormone receptor status, curation source, organization type, de novo vs recurrent metastatic disease, or calendar year.

- Compare the observed HER2 distribution against external clinical expectations or literature-based expectations. Discuss whether the values appear directionally credible and whether any deviations may be explained by the synthetic data design, missingness, capture bias, or classification choices.

- Quantify uncertainty: show how many patients could not be confidently classified and perform at least one sensitivity analysis using an alternate rule or alternate time window.

## Question 2: Enhertu Uptake vs Competitor Therapies by HER2-Defined Metastatic Breast Cancer Subindication

- Using the metastatic breast cancer cohort above, evaluate uptake of trastuzumab deruxtecan (Enhertu) relative to competing therapies. You should define clinically meaningful subindications and quantify how treatment use differs across them.

- Propose and implement a subindication framework. At minimum, consider HER2-positive metastatic breast cancer, hormone receptor–positive HER2-low metastatic breast cancer, and hormone receptor–positive HER2-ultralow metastatic breast cancer. You may define additional exploratory groups if justified.

- Derive treatment timing relative to metastatic diagnosis and identify first treatment after metastatic diagnosis. If possible, derive additional treatment sequencing logic that improves interpretation of Enhertu uptake.

- For each subindication, quantify the proportion of patients who receive Enhertu, the time from metastatic diagnosis to first Enhertu, and the most common competing therapies observed instead of or before Enhertu.

- Assess whether recorded biomarker and hormone receptor evidence support the observed use of Enhertu. Identify potentially discordant or analytically interesting cases where treatment selection does not appear to align with the documented biomarker profile.

- Provide an executive-ready summary of whether this synthetic data asset appears fit for answering a commercial or feasibility-style question about Enhertu uptake by HER2-defined metastatic breast cancer subindication.

## Evaluation Criteria

- Cohort construction accuracy and defensible event indexing

- Appropriate clinical logic for HER2 and HR status derivation

- Ability to reason through data quality and ambiguity

- Analytical depth and clarity of explanation

- Communication quality and production-minded thinking

## Notes

- This dataset is synthetic and intended for assessment purposes only. There is no expectation that you reproduce any specific proprietary workflow. We are evaluating your reasoning, implementation quality, and ability to work with imperfect real-world data structures.
