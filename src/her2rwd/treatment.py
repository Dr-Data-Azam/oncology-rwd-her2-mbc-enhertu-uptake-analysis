"""Treatment regimen grouping and line-of-therapy approximation.

Responsibility:
    Group medication events into regimens (drugs starting within
    regimen_window_days of each other form one regimen) and assign an
    approximate line-of-therapy number relative to the metastatic index date.
    Because the raw data has no explicit end dates or line fields, this module
    implements a date-proximity heuristic documented in ADR-010.

    All window parameters are read from config/analysis_rules.yaml.

Algorithm (ADR-010):
    1. Load medications on/after index date for cohort patients.
       De-duplicate per (patient_id, med_generic_name, med_date) — curated first.
    2. Sort drugs by (patient_id, med_date, med_generic_name).
    3. Regimen grouping: consecutive drugs with gap <= regimen_window_days
       (measured from the previous drug's start date) are in the same regimen.
    4. Line assignment: regimens are sorted by start date per patient.
       A new line starts when the gap from the previous regimen's start date
       to the current regimen's start date exceeds new_line_gap_days.

Outputs:
    outputs/tables/patient_lines.csv — one row per patient per line:
        patient_id, line_number, line_start, regimen_drugs, drug_classes,
        contains_enhertu, days_from_index, n_drugs_in_line

ADRs implemented: ADR-010
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_treatment_lines(
    con,
    cohort_df: pd.DataFrame,
    cfg: dict,
    out_dir: str | Path = "outputs/tables",
) -> pd.DataFrame:
    """Build one row per patient per line-of-therapy.

    ADR-010: regimen_window_days=28, new_line_gap_days=90, anchor=index_date.
    """
    regimen_window = cfg["treatment"]["regimen_window_days"]
    new_line_gap = cfg["treatment"]["new_line_gap_days"]
    drug_class_map = cfg["treatment"]["drug_class_map"]
    enhertu_name = cfg["treatment"].get("enhertu_generic_name", "trastuzumab deruxtecan")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # ── Load & de-duplicate medications ──────────────────────────────────────
    con.register("_cohort_for_tx", cohort_df[["patient_id", "index_date"]])
    meds = con.execute("""
        WITH ranked AS (
            SELECT
                m.patient_id,
                m.med_generic_name,
                m.med_brand_name,
                m.med_date,
                m.med_status,
                m.curation_flag,
                c.index_date,
                ROW_NUMBER() OVER (
                    PARTITION BY m.patient_id, m.med_generic_name, m.med_date
                    ORDER BY m.curation_flag DESC
                ) AS rn
            FROM medication m
            INNER JOIN _cohort_for_tx c ON m.patient_id = c.patient_id
            WHERE CAST(m.med_date AS DATE) >= CAST(c.index_date AS DATE)
        )
        SELECT patient_id, med_generic_name, med_brand_name,
               med_date, med_status, curation_flag, index_date
        FROM ranked
        WHERE rn = 1
        ORDER BY patient_id, med_date, med_generic_name
    """).df()

    if meds.empty:
        empty = pd.DataFrame(
            columns=[
                "patient_id",
                "line_number",
                "line_start",
                "regimen_drugs",
                "drug_classes",
                "contains_enhertu",
                "days_from_index",
                "n_drugs_in_line",
            ]
        )
        empty.to_csv(out_path / "patient_lines.csv", index=False)
        return empty

    meds["med_date"] = pd.to_datetime(meds["med_date"])
    meds["index_date"] = pd.to_datetime(meds["index_date"])
    meds["drug_class"] = meds["med_generic_name"].map(drug_class_map).fillna("other")
    meds["is_enhertu"] = meds["med_generic_name"] == enhertu_name

    # ── Regimen + line assignment per patient ─────────────────────────────────
    line_rows = []
    for pid, grp in meds.groupby("patient_id"):
        grp = grp.sort_values("med_date").reset_index(drop=True)
        index_date = grp["index_date"].iloc[0]

        # Step 1: regimen assignment (consecutive gap <= window → same regimen)
        regimen_ids = []
        reg_id = 1
        prev_date = None
        for _, row in grp.iterrows():
            if prev_date is None or (row["med_date"] - prev_date).days <= regimen_window:
                regimen_ids.append(reg_id)
            else:
                reg_id += 1
                regimen_ids.append(reg_id)
            prev_date = row["med_date"]
        grp["regimen_id"] = regimen_ids

        # Step 2: collapse each regimen to one summary row
        regimens = (
            grp.groupby("regimen_id")
            .agg(
                regimen_start=("med_date", "min"),
                regimen_drugs=("med_generic_name", lambda x: ", ".join(sorted(set(x)))),
                drug_classes=("drug_class", lambda x: ", ".join(sorted(set(x)))),
                contains_enhertu=("is_enhertu", "any"),
            )
            .reset_index()
            .sort_values("regimen_start")
            .reset_index(drop=True)
        )

        # Step 3: line assignment (gap from previous regimen start > new_line_gap → new line)
        line_number = 1
        line_numbers = []
        prev_start = None
        for _, reg in regimens.iterrows():
            if prev_start is None:
                line_number = 1
            elif (reg["regimen_start"] - prev_start).days > new_line_gap:
                line_number += 1
            line_numbers.append(line_number)
            prev_start = reg["regimen_start"]
        regimens["line_number"] = line_numbers
        regimens["patient_id"] = pid

        # Step 4: collapse regimens with same line_number → one row per line
        for ln, ln_grp in regimens.groupby("line_number"):
            all_drugs = sorted(set(", ".join(ln_grp["regimen_drugs"]).split(", ")))
            all_classes = sorted(set(", ".join(ln_grp["drug_classes"]).split(", ")))
            line_start = ln_grp["regimen_start"].min()
            line_rows.append(
                {
                    "patient_id": pid,
                    "line_number": ln,
                    "line_start": line_start.date(),
                    "regimen_drugs": ", ".join(all_drugs),
                    "drug_classes": ", ".join(all_classes),
                    "contains_enhertu": bool(ln_grp["contains_enhertu"].any()),
                    "days_from_index": (line_start - index_date).days,
                    "n_drugs_in_line": len(all_drugs),
                }
            )

    lines_df = pd.DataFrame(line_rows).sort_values(["patient_id", "line_number"]).reset_index(drop=True)
    lines_df.to_csv(out_path / "patient_lines.csv", index=False)
    return lines_df
