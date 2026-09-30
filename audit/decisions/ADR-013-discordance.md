# ADR-013: Discordance definitions (treatment vs biomarker)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Phase** | 06 |
| **Config keys** | `discordance.definitions` |
| **Module** | `src/her2rwd/q2_uptake.py` |
| **Approved by** | Azam Uddin |
| **Date** | 2026-09-29 |

---

## Context

"Discordance" in this analysis means a patient received Enhertu in a situation where the
biomarker evidence or line of therapy does not clearly support the labeled indication.
Identifying discordant cases demonstrates the asset's ability to detect real-world patterns
that matter for commercial and pharmacovigilance questions.

---

## Definitions adopted

### 1. `enhertu_in_her2_unknown`

**Definition:** Patient received Enhertu and has no HER2 test result in the window
(−365 to +90 days of metastatic index date). Subindication = `her2_unknown`.

**Why flagged:** Without a HER2 test result, it cannot be confirmed that the patient
has HER2-expressing disease meeting label criteria. This may represent:
- Off-label use
- Testing performed outside the data window (not captured)
- Empirical prescribing based on clinical judgment

**n in dataset:** 23 patients (37% of the 62 HER2-unknown patients).

**Output:** `q2_discordance_unknown_her2.csv`

---

### 2. `enhertu_in_line_1`

**Definition:** Patient received Enhertu as their first line of therapy after
metastatic index date (line_number = 1).

**Why flagged / reframed (updated 2026-09-29):**

- **DB-09 approved December 15, 2025**: T-DXd + pertuzumab combination is now FDA-approved
  for 1L HER2-positive mBC (IHC 3+ or ISH+). HER2+ patients receiving T-DXd + pertuzumab
  in Line 1 are now **on-label**. The 1L flag for HER2+ patients is now commercially
  interesting as a post-DB-09 uptake signal, not a discordance flag.
- **DB-06 approved January 27, 2025**: T-DXd for HR+, HER2-low or HER2-ultralow mBC is
  approved, but **requires ≥1 prior endocrine therapy in the metastatic setting**. Patients
  receiving T-DXd as their very first treatment (before any endocrine therapy) would be
  off-label under DB-06.
- **Practical reframe**: The `enhertu_in_line_1` list should be reviewed against:
  (a) HER2 subindication — HER2+ with pertuzumab may be on-label (DB-09)
  (b) Prior endocrine therapy — HER2-low/ultralow without prior ET is off-label (DB-06)
  The asset's ability to detect 1L Enhertu use is itself a commercial finding for
  post-DB-09 launch monitoring.

**n in dataset:** 5 patients.

**Output:** `q2_discordance_1l.csv`

---

## Definitions NOT adopted

- `enhertu_in_her2_null` — 0 patients in this dataset; definition retained in principle
  but produces empty output. Could be added to a sensitivity run.
- `enhertu_before_her2_test_date` — would require knowing test order vs treatment order;
  complex to implement and not requested for this assessment.
- `cdk46i_in_hr_negative` — out of scope for Q2 Enhertu focus.

---

## Consequences

- Both discordance lists carry patient-level IDs and subindication labels.
- All discordant patients are flagged in the deck with appropriate caveats.
- The 23 `enhertu_in_her2_unknown` cases are the most analytically important finding:
  they reveal a testing gap that limits ability to confirm label-appropriate Enhertu use.
