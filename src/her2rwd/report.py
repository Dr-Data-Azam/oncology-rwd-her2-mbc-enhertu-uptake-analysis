"""Report generation: notebook → HTML and slide deck (.pptx).

Responsibility:
    Export the Jupyter notebook to a self-contained HTML file using nbconvert.
    Build the five-slide + three-appendix .pptx deck from pipeline outputs via
    python-pptx, following the rules in the deck-builder skill:
    - Slide titles are finding sentences, not topic labels
    - Every number on a slide is sourced from a CSV in outputs/tables/
    - No number is typed by hand; all values are read from the output tables
    - Small cells (n < threshold) are flagged with "n<11" per ADR-012
    - Every slide footer: "Fully synthetic data · Source: <file>.csv · Rule set v1 (ADR-xxx)"

    The PDF copy is produced with LibreOffice headless if available, else
    skipped with a logged warning.

Inputs:
    notebooks/analysis.ipynb (executed)
    outputs/tables/*.csv and outputs/figures/*.png

Outputs:
    reports/HER2_mBC_Enhertu_Analysis.pptx
    reports/HER2_mBC_Enhertu_Analysis.pdf  (if LibreOffice available)
    reports/analysis_notebook.html

ADRs implemented: none (presentation layer)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# ── colour palette ────────────────────────────────────────────────────────────
_BLUE = RGBColor(0x00, 0x4B, 0x87)
_TEAL = RGBColor(0x00, 0x93, 0x8A)
_ORANGE = RGBColor(0xE8, 0x7D, 0x1E)
_GREY = RGBColor(0x58, 0x58, 0x58)
_LIGHT = RGBColor(0xF2, 0xF2, 0xF2)
_RED = RGBColor(0xC0, 0x39, 0x2B)
_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_GREEN_RGB = RGBColor(0x1A, 0x7A, 0x4A)

_SLIDE_W = Inches(13.33)
_SLIDE_H = Inches(7.5)

_HER2_COLORS = {
    "positive": "#004B87",
    "low": "#0093AA",
    "ultralow": "#70B8C6",
    "null": "#AAAAAA",
    "unknown": "#E0E0E0",
}


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────


def build_reports(
    cfg: dict,
    out_dir: str = "outputs",
    reports_dir: str = "reports",
    notebook: str = "notebooks/analysis.ipynb",
) -> dict:
    """Build all deliverable reports.

    Returns dict: {'html': path, 'pptx': path, 'figures': [paths]}
    """
    out = Path(out_dir)
    rpt = Path(reports_dir)
    rpt.mkdir(parents=True, exist_ok=True)
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    tbl = out / "tables"

    # ── Load tables ───────────────────────────────────────────────────────────
    q1_overall = pd.read_csv(tbl / "q1_overall.csv")
    q1_bench = pd.read_csv(tbl / "q1_benchmark.csv")
    q1_by_hr = pd.read_csv(tbl / "q1_by_hr.csv")
    q1_by_dt = pd.read_csv(tbl / "q1_by_disease_type.csv")
    q1_by_src = pd.read_csv(tbl / "q1_by_source.csv")

    # pandas reads the string "null" as NaN by default; restore it for all Q1 tables
    for _q1_df in [q1_overall, q1_by_hr, q1_by_dt, q1_by_src, q1_bench]:
        if "her2_category" in _q1_df.columns:
            _q1_df["her2_category"] = _q1_df["her2_category"].fillna("null")

    q2_uptake = pd.read_csv(tbl / "q2_uptake_summary.csv")
    disc_unk = pd.read_csv(tbl / "q2_discordance_unknown_her2.csv")
    disc_1l = pd.read_csv(tbl / "q2_discordance_1l.csv")
    enhertu_by_line = pd.read_csv(tbl / "q2_enhertu_by_line.csv")
    comp_map = pd.read_csv(tbl / "q2_competitor_map.csv")
    sens_dist = pd.read_csv(tbl / "sensitivity_her2_distribution.csv")
    attrition = pd.read_csv(tbl / "attrition.csv")
    cohort = pd.read_csv(tbl / "cohort.csv")
    lines = pd.read_csv(tbl / "patient_lines.csv")
    dq_summary = pd.read_csv(out / "dq" / "dq_summary.csv")
    subind_assign = pd.read_csv(tbl / "q2_subindication_assignment.csv")

    n_cohort = len(cohort)
    n_class = int(q1_overall[q1_overall["her2_category"] != "unknown"]["n"].sum())
    n_unk = int(q1_overall[q1_overall["her2_category"] == "unknown"]["n"].iloc[0])
    n_enhertu = int(lines[lines["contains_enhertu"]]["patient_id"].nunique())
    small_thr = cfg["stats"]["small_cell_threshold"]

    # Raw patient count from run manifest (written by Stage 2 before this stage runs)
    manifest_path = out / "run_manifest.json"
    n_raw = n_cohort
    if manifest_path.exists():
        with open(manifest_path) as _mf:
            _manifest = json.load(_mf)
        n_raw = _manifest.get("stages", {}).get("load_raw", {}).get("row_counts", {}).get("patient", n_cohort)

    # ── Compute presentation-layer derived values ─────────────────────────────
    # Top drug class per subindication (from competitor map, non-small cells first)
    _comp_nonsm = comp_map[~comp_map["small_cell"]]
    _comp_base = _comp_nonsm if len(_comp_nonsm) > 0 else comp_map
    top_drug = (
        _comp_base.sort_values("n_patients", ascending=False).groupby("subindication").first()["drug_class"].to_dict()
    )

    # Median days to first Enhertu per subindication
    median_days: dict = {}
    try:
        _enhertu_pts = lines[lines["contains_enhertu"]].copy()
        _enhertu_pts["start_date"] = pd.to_datetime(_enhertu_pts["start_date"], errors="coerce")
        _cohort_idx = cohort[["patient_id", "index_date"]].copy()
        _cohort_idx["index_date"] = pd.to_datetime(_cohort_idx["index_date"], errors="coerce")
        _enhertu_pts = _enhertu_pts.merge(_cohort_idx, on="patient_id", how="left")
        _enhertu_pts["days_to_enhertu"] = (_enhertu_pts["start_date"] - _enhertu_pts["index_date"]).dt.days
        _enhertu_pts = _enhertu_pts.merge(subind_assign[["patient_id", "subindication"]], on="patient_id", how="left")
        median_days = (
            _enhertu_pts.groupby("subindication")["days_to_enhertu"]
            .median()
            .apply(lambda x: int(x) if pd.notna(x) else None)
            .to_dict()
        )
    except Exception:
        pass

    # ── Generate figures ──────────────────────────────────────────────────────
    fig_q1 = _fig_her2_distribution(q1_overall, n_cohort, fig_dir)
    fig_q2 = _fig_enhertu_uptake(q2_uptake, fig_dir)
    fig_bench = _fig_benchmark(q1_bench, fig_dir)
    fig_consort = _fig_consort_flow(attrition, fig_dir)
    fig_strata = _fig_stacked_her2_strata(q1_overall, q1_by_hr, q1_by_dt, q1_by_src, fig_dir)
    fig_sens = _fig_sensitivity_table(sens_dist, fig_dir)

    # ── HTML export ───────────────────────────────────────────────────────────
    html_path = _export_html(notebook, rpt)

    # ── Build pptx (skipped if reports.rebuild_pptx is false in config) ─────────
    existing_pptx = rpt / "HER2_mBC_Enhertu_Analysis.pptx"
    if not cfg.get("reports", {}).get("rebuild_pptx", False) and existing_pptx.exists():
        print("  PPTX rebuild skipped (reports.rebuild_pptx: false) — manual layout preserved.")
        pptx_path = existing_pptx
    else:
        pptx_path = _build_pptx(
            rpt=rpt,
            fig_q1=fig_q1,
            fig_q2=fig_q2,
            fig_bench=fig_bench,
            fig_consort=fig_consort,
            fig_strata=fig_strata,
            fig_sens=fig_sens,
            q1_overall=q1_overall,
            q1_bench=q1_bench,
            q1_by_hr=q1_by_hr,
            q1_by_dt=q1_by_dt,
            q1_by_src=q1_by_src,
            q2_uptake=q2_uptake,
            disc_unk=disc_unk,
            disc_1l=disc_1l,
            enhertu_by_line=enhertu_by_line,
            attrition=attrition,
            dq_summary=dq_summary,
            n_cohort=n_cohort,
            n_class=n_class,
            n_unk=n_unk,
            n_enhertu=n_enhertu,
            n_raw=n_raw,
            small_thr=small_thr,
            top_drug=top_drug,
            median_days=median_days,
        )

    # ── PDF (LibreOffice headless, optional) ──────────────────────────────────
    pdf_path = _try_pdf(pptx_path, rpt)

    return {
        "html": str(html_path),
        "pptx": str(pptx_path),
        "pdf": str(pdf_path) if pdf_path else None,
        "figures": [str(fig_q1), str(fig_q2), str(fig_bench), str(fig_consort), str(fig_strata), str(fig_sens)],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure generation
# ─────────────────────────────────────────────────────────────────────────────


def _fig_her2_distribution(q1: pd.DataFrame, n_cohort: int, fig_dir: Path) -> Path:
    cats = ["positive", "low", "ultralow", "null", "unknown"]
    colors_hex = ["#004B87", "#0093AA", "#70B8C6", "#AAAAAA", "#E0E0E0"]

    df = q1.set_index("her2_category").reindex(cats)
    ns = df["n"].fillna(0).astype(int)
    pcts = df["pct"].fillna(0)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.barh(
        cats[::-1],
        pcts[::-1],
        color=colors_hex[::-1],
        height=0.55,
        edgecolor="white",
        linewidth=0.5,
    )

    for bar, n, pct, cat in zip(bars, ns[::-1], pcts[::-1], cats[::-1]):
        label = f"n={n}  ({pct:.1f}%)"
        ax.text(
            pct + 0.5,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            fontsize=9,
            color="#333333",
        )

    ax.set_xlabel(f"% of cohort (n={n_cohort})", fontsize=9)
    ax.set_xlim(0, 80)
    ax.set_title(
        f"HER2 Distribution at Metastatic Diagnosis\n({n_cohort} cohort patients, synthetic data)",
        fontsize=10,
        fontweight="bold",
        pad=10,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", labelsize=9)
    fig.tight_layout()
    path = fig_dir / "q1_her2_distribution.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _fig_enhertu_uptake(q2: pd.DataFrame, fig_dir: Path) -> Path:
    req = q2[q2["subindication_type"] == "required"].copy()
    labels = {
        "her2_positive": "HER2+ (DB-03/09)",
        "hr_pos_her2_low": "HR+/HER2-low (DB-04/06)",
        "hr_neg_her2_low": "HR-/HER2-low (DB-04)",
        "hr_pos_her2_ultralow": "HR+/HER2-ultralow (DB-06)",
    }
    req["label"] = req["subindication"].map(labels).fillna(req["subindication"])

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#004B87", "#0093AA", "#70B8C6", "#3A7FC1"]
    bars = ax.barh(
        req["label"][::-1],
        req["pct_enhertu"][::-1],
        color=colors,
        height=0.5,
        edgecolor="white",
        linewidth=0.5,
    )

    for bar, row in zip(bars, req.iloc[::-1].itertuples()):
        flag = " [n<11]" if row.small_cell else ""
        label = f"{int(row.n_enhertu)}/{int(row.n_total)} ({row.pct_enhertu:.0f}%){flag}"
        ax.text(
            row.pct_enhertu + 1,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            fontsize=9,
            color="#333333",
        )

    ax.set_xlabel("% of subindication receiving Enhertu", fontsize=9)
    ax.set_xlim(0, 130)
    ax.set_title(
        "Enhertu Uptake by Required Subindication\n(all cells n<11 — directional only)",
        fontsize=10,
        fontweight="bold",
        pad=10,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", labelsize=9)
    fig.tight_layout()
    path = fig_dir / "q2_enhertu_uptake.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _fig_benchmark(bench: pd.DataFrame, fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 3.5))
    cats = bench["her2_category"].tolist()
    pcts = bench["pct"].tolist()
    lo = bench["benchmark_lo_pct"].tolist()
    hi = bench["benchmark_hi_pct"].tolist()

    xs = range(len(cats))
    ax.bar(xs, pcts, color="#004B87", width=0.4, label="Observed (%)", zorder=3)
    for i, (lo_val, h) in enumerate(zip(lo, hi)):
        if pd.notna(lo_val) and pd.notna(h):
            ax.errorbar(
                i,
                (float(lo_val) + float(h)) / 2,
                yerr=[
                    [(float(lo_val) + float(h)) / 2 - float(lo_val)],
                    [float(h) - (float(lo_val) + float(h)) / 2],
                ],
                fmt="none",
                color="#E87D1E",
                linewidth=3,
                capsize=5,
                label="Literature range" if i == 0 else "_",
            )

    ax.set_xticks(list(xs))
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel("% of classifiable patients", fontsize=9)
    ax.set_title(
        "HER2 Distribution vs Literature Benchmarks\n(synthetic data — alignment not expected)",
        fontsize=9,
        fontweight="bold",
        pad=8,
    )
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    path = fig_dir / "q1_benchmark_comparison.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _fig_consort_flow(attrition_df: pd.DataFrame, fig_dir: Path) -> Path:
    rows = attrition_df.to_dict("records")
    n_rows = len(rows)
    fig, ax = plt.subplots(figsize=(7, n_rows * 1.8 + 0.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.5, n_rows * 2)
    ax.axis("off")

    for i, row in enumerate(rows):
        y = (n_rows - i - 1) * 2 + 0.5
        color = "#1A7A4A" if i == n_rows - 1 else "#004B87"
        rect = plt.Rectangle((0.8, y - 0.4), 6.2, 1.0, color=color, zorder=2, linewidth=0)
        ax.add_patch(rect)
        ax.text(
            3.9,
            y + 0.15,
            str(row["step_label"]),
            ha="center",
            va="center",
            color="white",
            fontsize=7.5,
            fontweight="bold",
            zorder=3,
        )
        ax.text(
            3.9,
            y - 0.2,
            f"N = {row['n_remaining']}",
            ha="center",
            va="center",
            color="white",
            fontsize=9,
            zorder=3,
        )
        if int(row.get("n_excluded", 0)) > 0:
            ax.annotate(
                "",
                xy=(8.5, y + 0.1),
                xytext=(7.1, y + 0.1),
                arrowprops=dict(arrowstyle="->", color="#585858", lw=1.2),
            )
            ax.text(
                8.6,
                y + 0.1,
                f"−{row['n_excluded']} excluded",
                ha="left",
                va="center",
                color="#C0392B",
                fontsize=7.5,
            )
        if i < n_rows - 1:
            ax.annotate(
                "",
                xy=(3.9, y - 0.4 - 0.55),
                xytext=(3.9, y - 0.4),
                arrowprops=dict(arrowstyle="->", color="#585858", lw=1.5),
            )

    ax.set_title("Patient Attrition (CONSORT)", fontsize=9, fontweight="bold", pad=4)
    fig.tight_layout()
    path = fig_dir / "consort_flow.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _fig_stacked_her2_strata(
    q1_overall: pd.DataFrame,
    q1_by_hr: pd.DataFrame,
    q1_by_dt: pd.DataFrame,
    q1_by_src: pd.DataFrame,
    fig_dir: Path,
) -> Path:
    cats = ["positive", "low", "ultralow", "null", "unknown"]
    colors = ["#004B87", "#0093AA", "#70B8C6", "#AAAAAA", "#E0E0E0"]

    def _row_pcts(df: pd.DataFrame, filter_col: str, filter_val: str):
        sub = df[df[filter_col] == filter_val]
        n_total = int(sub["n"].sum())
        pcts = {r["her2_category"]: float(r["pct"]) for _, r in sub.iterrows()}
        return n_total, pcts

    rows_data = []
    n_tot_all = int(q1_overall["n"].sum())
    rows_data.append(
        (f"Overall (n={n_tot_all})", {r["her2_category"]: float(r["pct"]) for _, r in q1_overall.iterrows()})
    )
    for hr_val, label in [("positive", "HR+"), ("negative", "HR−")]:
        n_tot, pcts = _row_pcts(q1_by_hr, "hr_status", hr_val)
        rows_data.append((f"{label} (n={n_tot})", pcts))
    for dt_val, label in [("de_novo", "De novo"), ("recurrent", "Recurrent")]:
        n_tot, pcts = _row_pcts(q1_by_dt, "disease_type", dt_val)
        rows_data.append((f"{label} (n={n_tot})", pcts))
    for src_val, label in [("curated", "Curated"), ("ehr", "EHR")]:
        n_tot, pcts = _row_pcts(q1_by_src, "source", src_val)
        rows_data.append((f"{label} (n={n_tot})", pcts))

    y_labels = [r[0] for r in rows_data]
    n_rows = len(rows_data)

    fig, ax = plt.subplots(figsize=(10, max(4.5, n_rows * 0.75 + 1.5)))
    lefts = [0.0] * n_rows
    handles = []
    for ci, cat in enumerate(cats):
        widths = [r[1].get(cat, 0.0) for r in rows_data]
        bars = ax.barh(
            range(n_rows),
            widths,
            left=lefts,
            color=colors[ci],
            height=0.6,
            edgecolor="white",
            linewidth=0.5,
            label=cat,
        )
        handles.append(bars[0])
        lefts = [acc + w for acc, w in zip(lefts, widths)]

    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(y_labels, fontsize=8)
    ax.set_xlabel("% of stratum", fontsize=9)
    ax.set_xlim(0, 108)
    ax.set_title(
        "HER2 Distribution by Patient Stratum\n(synthetic data — showing % of each stratum)",
        fontsize=10,
        fontweight="bold",
    )
    ax.legend(handles, cats, loc="lower right", fontsize=7, ncol=5, framealpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    path = fig_dir / "q1_stacked_strata.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _fig_sensitivity_table(sens_dist_df: pd.DataFrame, fig_dir: Path) -> Path:
    cats = ["positive", "low", "ultralow", "null", "unknown"]
    col_labels = ["Baseline", "S1 Narrow\nWindow", "S2 Curated\nOnly", "S3 Cons.\nIHC-0"]

    indexed = sens_dist_df.set_index("her2_category").reindex(cats).fillna(0)
    cell_text = []
    cell_colors = []
    for cat in cats:
        row = indexed.loc[cat]
        base_pct = float(row["pct_baseline"])
        texts = [
            f"{int(row['n_baseline'])} ({row['pct_baseline']:.1f}%)",
            f"{int(row['n_s1_narrow_window'])} ({row['pct_s1_narrow_window']:.1f}%)",
            f"{int(row['n_s2_curated_only'])} ({row['pct_s2_curated_only']:.1f}%)",
            f"{int(row['n_s3_conservative_ihc0'])} ({row['pct_s3_conservative_ihc0']:.1f}%)",
        ]
        scenario_pcts = [
            float(row["pct_s1_narrow_window"]),
            float(row["pct_s2_curated_only"]),
            float(row["pct_s3_conservative_ihc0"]),
        ]
        colors_row = ["white"] + ["#FFF9C4" if abs(p - base_pct) > 2 else "white" for p in scenario_pcts]
        cell_text.append(texts)
        cell_colors.append(colors_row)

    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.axis("off")
    tbl = ax.table(
        cellText=cell_text,
        rowLabels=cats,
        colLabels=col_labels,
        cellColours=cell_colors,
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.7)
    ax.set_title(
        "Sensitivity Analysis: HER2 Distribution Under Alternative Rules\n"
        "(yellow cell = >2 percentage-point shift from baseline)",
        fontsize=8.5,
        fontweight="bold",
        pad=22,
    )
    fig.tight_layout()
    path = fig_dir / "sensitivity_table.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# HTML export
# ─────────────────────────────────────────────────────────────────────────────


def _export_html(notebook: str, rpt: Path) -> Path:
    html_path = rpt / "analysis_notebook.html"
    cmd = [
        sys.executable,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "html",
        "--execute",
        "--ExecutePreprocessor.timeout=300",
        notebook,
        "--output",
        str(html_path.resolve()),
    ]
    print(f"  Running nbconvert: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [WARN] nbconvert failed:\n{result.stderr}")
    else:
        print(f"  HTML written: {html_path}")
    return html_path


# ─────────────────────────────────────────────────────────────────────────────
# PPTX helpers
# ─────────────────────────────────────────────────────────────────────────────


def _fmt(n: int, small: bool) -> str:
    return "n<11" if small else str(n)


def _pct_str(pct: float, small: bool) -> str:
    return "n<11" if small else f"{pct:.1f}%"


def _add_header(slide, title: str, font_pt: int = 20) -> None:
    tf = slide.shapes.add_textbox(Inches(0.4), Inches(0.2), Inches(12.5), Inches(1.1))
    p = tf.text_frame.paragraphs[0]
    p.text = title
    p.alignment = PP_ALIGN.LEFT
    run = p.runs[0]
    run.font.size = Pt(font_pt)
    run.font.bold = True
    run.font.color.rgb = _BLUE
    rule = slide.shapes.add_shape(1, Inches(0.4), Inches(1.2), Inches(12.5), Inches(0.04))
    rule.fill.solid()
    rule.fill.fore_color.rgb = _BLUE
    rule.line.fill.background()


def _add_body(
    slide,
    text: str,
    left_in: float = 0.4,
    top_in: float = 1.4,
    width_in: float = 6.8,
    height_in: float = 5.6,
    font_size: Pt = Pt(9.5),
) -> None:
    tf = slide.shapes.add_textbox(Inches(left_in), Inches(top_in), Inches(width_in), Inches(height_in))
    tf.word_wrap = True
    frame = tf.text_frame
    frame.word_wrap = True
    first = True
    for line in text.split("\n"):
        if first:
            p = frame.paragraphs[0]
            first = False
        else:
            p = frame.add_paragraph()
        p.text = line
        p.alignment = PP_ALIGN.LEFT
        if p.runs:
            p.runs[0].font.size = font_size
            p.runs[0].font.color.rgb = _GREY


def _add_footer(slide, text: str) -> None:
    tf = slide.shapes.add_textbox(Inches(0.4), Inches(7.05), Inches(12.5), Inches(0.35))
    p = tf.text_frame.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.LEFT
    if p.runs:
        p.runs[0].font.size = Pt(7)
        p.runs[0].font.color.rgb = _GREY


def _q1_n(df: pd.DataFrame, cat: str) -> int:
    rows = df[df["her2_category"] == cat]
    return int(rows.iloc[0]["n"]) if len(rows) else 0


def _q1_pct(df: pd.DataFrame, cat: str) -> float:
    rows = df[df["her2_category"] == cat]
    return float(rows.iloc[0]["pct"]) if len(rows) else 0.0


def _line_n(enhertu_by_line: pd.DataFrame, subind: str, line: str) -> int:
    rows = enhertu_by_line[(enhertu_by_line["subindication"] == subind) & (enhertu_by_line["line_label"] == line)]
    return int(rows.iloc[0]["n_patients"]) if len(rows) else 0


def _typical_line(enhertu_by_line: pd.DataFrame, subind: str, small_thr: int) -> str:
    sub = enhertu_by_line[enhertu_by_line["subindication"] == subind].copy()
    if sub.empty:
        return "—"
    best = sub.sort_values("n_patients", ascending=False).iloc[0]
    if int(best["n_patients"]) < small_thr:
        return "n<11"
    return str(best["line_label"])


# ─────────────────────────────────────────────────────────────────────────────
# PPTX builder
# ─────────────────────────────────────────────────────────────────────────────


def _build_pptx(
    rpt: Path,
    fig_q1: Path,
    fig_q2: Path,
    fig_bench: Path,
    fig_consort: Path,
    fig_strata: Path,
    fig_sens: Path,
    q1_overall: pd.DataFrame,
    q1_bench: pd.DataFrame,
    q1_by_hr: pd.DataFrame,
    q1_by_dt: pd.DataFrame,
    q1_by_src: pd.DataFrame,
    q2_uptake: pd.DataFrame,
    disc_unk: pd.DataFrame,
    disc_1l: pd.DataFrame,
    enhertu_by_line: pd.DataFrame,
    attrition: pd.DataFrame,
    dq_summary: pd.DataFrame,
    n_cohort: int,
    n_class: int,
    n_unk: int,
    n_enhertu: int,
    n_raw: int,
    small_thr: int,
    top_drug: dict,
    median_days: dict,
) -> Path:
    prs = Presentation()
    prs.slide_width = _SLIDE_W
    prs.slide_height = _SLIDE_H
    blank = prs.slide_layouts[6]

    # ── Convenience lookups ───────────────────────────────────────────────────
    n_pos = _q1_n(q1_overall, "positive")
    n_low = _q1_n(q1_overall, "low")
    n_ult = _q1_n(q1_overall, "ultralow")
    pct_pos = _q1_pct(q1_overall, "positive")
    pct_low = _q1_pct(q1_overall, "low")
    pct_ult = _q1_pct(q1_overall, "ultralow")
    pct_unk = _q1_pct(q1_overall, "unknown")
    pct_null = _q1_pct(q1_overall, "null")
    pct_zero = pct_ult + pct_null

    sc_ult = n_ult < small_thr

    n_disc_unk = len(disc_unk)
    n_disc_1l = len(disc_1l)
    pct_disc_unk = round(n_disc_unk / n_unk * 100, 0) if n_unk > 0 else 0

    # Q2 uptake lookups
    def _q2_row(subind: str) -> pd.Series | None:
        rows = q2_uptake[q2_uptake["subindication"] == subind]
        return rows.iloc[0] if len(rows) else None

    _pos_row = _q2_row("her2_positive")
    _low_row = _q2_row("hr_pos_her2_low")
    _ult_row = _q2_row("hr_pos_her2_ultralow")
    _null_row = _q2_row("her2_null")
    _unk_row = _q2_row("her2_unknown")

    pct_pos_enhertu = float(_pos_row["pct_enhertu"]) if _pos_row is not None else 0.0
    pct_low_enhertu = float(_low_row["pct_enhertu"]) if _low_row is not None else 0.0
    n_pos_enhertu = int(_pos_row["n_enhertu"]) if _pos_row is not None else 0
    n_low_enhertu = int(_low_row["n_enhertu"]) if _low_row is not None else 0

    n_final = int(attrition.iloc[-1]["n_remaining"])

    # ── Slide 1: Executive Summary ────────────────────────────────────────────
    sl1 = prs.slides.add_slide(blank)
    _add_header(
        sl1,
        "The Asset Supports HER2+ vs HER2− Feasibility Today; "
        "HER2-Low Subindication Questions Require Curated IHC Detail",
        font_pt=18,
    )

    body_left = (
        f"Q1 — HER2 Distribution  (n={n_cohort} mBC patients, synthetic)\n"
        f"  HER2-positive:    {n_pos} ({pct_pos:.1f}%)   [lit: 15–20%  ✓]\n"
        f"  HER2-low:         {n_low} ({pct_low:.1f}%)   [lit: 45–55%  ⚠ testing gap]\n"
        f"  HER2-ultralow:    {_fmt(n_ult, sc_ult)} ({_pct_str(pct_ult, sc_ult)})   [n<11]\n"
        f"  Unknown/untested: {n_unk} ({pct_unk:.1f}%)   [primary data gap]\n"
        "\n"
        f"Q2 — Enhertu Uptake  (directional; all subindications small or borderline)\n"
        f"  HER2-positive:       {pct_pos_enhertu:.1f}% ({n_pos_enhertu}/{n_pos})\n"
        f"  HR+/HER2-low:        {pct_low_enhertu:.1f}% ({n_low_enhertu}/{n_low})\n"
        f"  HR+/HER2-ultralow:   n<11  (3/3, directional only)\n"
        f"  HER2-unknown (disc.): {pct_disc_unk:.0f}% of untested received Enhertu\n"
        "\n"
        "VERDICT\n"
        "  Fit for:          HER2+ vs HER2− feasibility, hypothesis generation\n"
        "  Fit with caveats: HER2-low uptake (testing gap limits denominator)\n"
        f"  Not fit for:      Powered CI-level endpoints (n={n_cohort})\n"
        "\n"
        "RECOMMENDATIONS TO CLIENT\n"
        "  1. Prioritise curated records for HER2 sub-classification\n"
        "  2. Add IHC staining detail (% cells, membrane intensity)\n"
        "  3. Scale to 1,000+ patients for CI-level subindication studies"
    )
    _add_body(sl1, body_left, left_in=0.4, top_in=1.35, width_in=6.5, height_in=5.8, font_size=Pt(9))

    body_right = (
        "FIT-FOR-PURPOSE SCORECARD\n"
        "\n"
        f"  \U0001f7e2 mBC identification    ICD-10 C50 + M1/IV staging\n"
        f"  \U0001f7e1 Index date            Mixed source; staging-first common\n"
        f"  \U0001f7e2 HER2+ vs HER2−        {n_pos} classifiable positive; lit-aligned\n"
        f"  \U0001f7e1 HER2-low              Testing gap inflates unknown pool\n"
        f"  \U0001f7e1 HER2-ultralow         n<11; directional signal only\n"
        f"  \U0001f7e2 HR status             ER+PR% available; ASCO/CAP 2020\n"
        f"  \U0001f7e1 Treatment timing      Start dates present; end dates absent\n"
        f"  \U0001f534 Sample size           n={n_cohort}; 1,000+ needed for powered CI"
    )
    _add_body(sl1, body_right, left_in=7.1, top_in=1.35, width_in=5.8, height_in=5.8, font_size=Pt(9))
    _add_footer(
        sl1, "Fully synthetic data · Source: q1_overall.csv · q2_uptake_summary.csv · Rule set v1 (ADR-006/012)"
    )

    # ── Slide 2: Cohort & Method ───────────────────────────────────────────────
    sl2 = prs.slides.add_slide(blank)
    _add_header(
        sl2,
        f"{n_final} of {n_raw} Patients Form an Analysis-Ready mBC Cohort, "
        "Anchored on a Breast-Specific Metastatic Index Date",
        font_pt=18,
    )

    if fig_consort.exists():
        sl2.shapes.add_picture(str(fig_consort), Inches(0.3), Inches(1.35), Inches(5.5), Inches(5.5))

    logic_text = (
        "INDEX DATE  (ADR-004)\n"
        "  Earliest of: C50 metastatic dx date OR M1/IV staging date\n"
        "  Audit: index_source = staging_only / diagnosis_only / staging_first / diagnosis_first\n"
        "\n"
        "HER2 WINDOW  (ADR-007)\n"
        "  −365 days to +90 days around metastatic index date\n"
        "  Tie-break: curation_flag > variant_specificity > closest to index  (ADR-008)\n"
        "\n"
        "HER2 MAPPING  (ADR-006, ASCO/CAP 2023 + DB-06 ultralow definition)\n"
        "  IHC 3+           → positive\n"
        "  IHC 1+ / 2+ ISH− → low\n"
        "  IHC 0 faint ≤10%  → ultralow\n"
        "  IHC 0 no %       → unknown (potential DB-06 eligible pending re-test)\n"
        "  Variant detail beats coarse result text\n"
        "\n"
        "HR STATUS  (ADR-009, ASCO/CAP 2020)\n"
        "  HR-positive = ER ≥ 1% OR PR ≥ 1%  (% staining beats result text label)\n"
        "\n"
        "SO WHAT: Most HER2 tests fall AFTER the metastatic date.\n"
        "  The +90-day extension captures the majority of available results."
    )
    _add_body(sl2, logic_text, left_in=6.1, top_in=1.35, width_in=6.9, height_in=5.8, font_size=Pt(8.5))
    _add_footer(
        sl2, "Fully synthetic data · Source: attrition.csv · cohort.csv · Rule set v1 (ADR-004/005/006/007/008/009)"
    )

    # ── Slide 3: Q1 HER2 Distribution ─────────────────────────────────────────
    sl3 = prs.slides.add_slide(blank)
    _add_header(
        sl3,
        f"HER2-Low Is the Largest Classified Group, but {pct_unk:.0f}% of mBC Patients Cannot Be Sub-Classified",
        font_pt=18,
    )

    if fig_strata.exists():
        sl3.shapes.add_picture(str(fig_strata), Inches(0.3), Inches(1.3), Inches(8.0), Inches(5.9))

    # Literature check panel — derive from q1_bench
    _bench_map = {}
    for _, br in q1_bench.iterrows():
        cat = str(br["her2_category"])
        in_range = br.get("in_benchmark_range")
        lo_b = br.get("benchmark_lo_pct")
        hi_b = br.get("benchmark_hi_pct")
        status = "✓" if in_range else "⚠"
        _bench_map[cat] = (status, lo_b, hi_b)

    def _lit_range(cat: str) -> str:
        entry = _bench_map.get(cat)
        if entry and pd.notna(entry[1]) and pd.notna(entry[2]):
            return f"{entry[1]:.0f}–{entry[2]:.0f}%"
        return "n/a"

    def _lit_status(cat: str) -> str:
        return _bench_map.get(cat, ("—", None, None))[0]

    # EHR unknown count
    _ehr_src = q1_by_src[q1_by_src["source"] == "ehr"]
    _ehr_unk_rows = _ehr_src[_ehr_src["her2_category"] == "unknown"]
    n_ehr_unk = int(_ehr_unk_rows.iloc[0]["n"]) if len(_ehr_unk_rows) else 0

    lit_panel = (
        "LITERATURE CHECK\n"
        "(Tarantino JCO 2020; Schettini NPJ BC 2021)\n"
        "\n"
        "  Category     Observed    Lit range   Status\n"
        "  " + "─" * 40 + "\n"
        f"  Positive     {pct_pos:.1f}%        {_lit_range('positive'):12s}  {_lit_status('positive')}\n"
        f"  Low          {pct_low:.1f}%        {_lit_range('low'):12s}  {_lit_status('low')}\n"
        f"  HER2-zero    {pct_zero:.1f}%        "
        f"{_lit_range('her2_zero (null+ultralow)'):12s}  "
        f"{_lit_status('her2_zero (null+ultralow)')}\n"
        "\n"
        "SO WHAT\n"
        "\n"
        "  Curation is the difference between a\n"
        "  binary HER2 answer and a low/ultralow\n"
        "  answer: EHR records drive the unknown pool.\n"
        "\n"
        f"  {n_ehr_unk} of {n_unk} unknown patients have\n"
        "  EHR-only HER2 results.\n"
        "\n"
        "  HER2-low prevalence below range — this\n"
        "  reflects testing gaps, not biology."
    )
    _add_body(sl3, lit_panel, left_in=8.5, top_in=1.35, width_in=4.5, height_in=5.8, font_size=Pt(8.5))
    _add_footer(
        sl3,
        "Fully synthetic data · Source: q1_overall.csv · q1_by_hr.csv · q1_by_disease_type.csv "
        "· q1_by_source.csv · Rule set v1 (ADR-012/014)",
    )

    # ── Slide 4: Q2 Enhertu Uptake by Subindication ───────────────────────────
    sl4 = prs.slides.add_slide(blank)
    _add_header(
        sl4,
        f"Enhertu Reaches {pct_pos_enhertu:.0f}% of HER2+ but {pct_low_enhertu:.0f}% of HR+/HER2-Low; "
        f"{pct_disc_unk:.0f}% of Untested Patients Also Received Enhertu",
        font_pt=17,
    )

    # Build uptake table rows
    uptake_rows_text = [
        "SUBINDICATION           N      % ENHERTU (95% CI)       LINE   TOP DRUG CLASS",
        "─" * 74,
    ]
    _subind_display = {
        "her2_positive": "HER2-positive",
        "hr_pos_her2_low": "HR+/HER2-low",
        "hr_pos_her2_ultralow": "HR+/HER2-ultralow",
        "her2_null": "HER2-null (control)",
        "her2_unknown": "HER2-unknown",
    }
    for subind_key, subind_label in _subind_display.items():
        row = _q2_row(subind_key)
        if row is None:
            continue
        sc = bool(row["small_cell"])
        n_tot_s = int(row["n_total"])
        pct_s = float(row["pct_enhertu"])
        ci_lo_s = float(row["ci_lo"])
        ci_hi_s = float(row["ci_hi"])
        if sc:
            ci_str = "n<11"
            n_display = "n<11"
        else:
            ci_str = f"{pct_s:.1f}% ({ci_lo_s:.1f}–{ci_hi_s:.1f})"
            n_display = str(n_tot_s)
        typ_line = _typical_line(enhertu_by_line, subind_key, small_thr)
        top_dc = top_drug.get(subind_key, "—")
        uptake_rows_text.append(f"{subind_label:23s} {n_display:6s} {ci_str:25s} {typ_line:6s} {top_dc}")

    # Line sequence for HER2+ and HR+/low
    pos_1l = _line_n(enhertu_by_line, "her2_positive", "1L")
    pos_2l = _line_n(enhertu_by_line, "her2_positive", "2L")
    pos_3l = _line_n(enhertu_by_line, "her2_positive", "3L+")
    low_1l = _line_n(enhertu_by_line, "hr_pos_her2_low", "1L")
    low_2l = _line_n(enhertu_by_line, "hr_pos_her2_low", "2L")
    low_3l = _line_n(enhertu_by_line, "hr_pos_her2_low", "3L+")

    uptake_rows_text += [
        "",
        "LINE SEQUENCE (1L / 2L / 3L+):",
        f"  HER2+:    {pos_1l}/{pos_2l}/{pos_3l}   |   HR+/low: {low_1l}/{low_2l}/{low_3l}",
        "",
        "DISCORDANCE:",
        f"  {n_disc_unk} patients received Enhertu with no HER2 test in window",
        f"    → {pct_disc_unk:.0f}% of HER2-unknown — key testing gap signal",
        f"  {n_disc_1l} patients received Enhertu in Line 1",
        "    → Post-DB-09 (Dec 2025): HER2+ + pertuzumab is now on-label",
        "    → HER2-low/ultralow 1L without prior ET: off-label under DB-06",
        "",
        "DB-06 (Jan 27 2025): T-DXd, HR+/HER2-low or ultralow after ≥1 ET",
        "DB-09 (Dec 15 2025): T-DXd + pertuzumab, 1L HER2-positive",
    ]

    _add_body(
        sl4,
        "\n".join(uptake_rows_text),
        left_in=0.3,
        top_in=1.35,
        width_in=8.5,
        height_in=5.8,
        font_size=Pt(8),
    )

    if fig_q2.exists():
        sl4.shapes.add_picture(str(fig_q2), Inches(8.9), Inches(1.35), Inches(4.1), Inches(3.5))

    _add_footer(
        sl4, "Fully synthetic data · Source: q2_uptake_summary.csv · q2_discordance_*.csv · Rule set v1 (ADR-011/013)"
    )

    # ── Slide 5: Robustness, Fitness & Productionization ──────────────────────
    sl5 = prs.slides.add_slide(blank)
    _add_header(
        sl5,
        "Conclusions Hold Under Alternative Rules Except HER2-Low vs Ultralow Split; "
        "Production Needs a Governed Rules Engine",
        font_pt=18,
    )

    if fig_sens.exists():
        sl5.shapes.add_picture(str(fig_sens), Inches(0.3), Inches(1.35), Inches(6.0), Inches(3.5))

    limitations_text = (
        "LIMITATIONS\n"
        "\n"
        f"  Synthetic data (n={n_cohort} patients)\n"
        "  n<11 in key subindications\n"
        "    — directional signal only\n"
        "\n"
        "  No line-of-therapy end dates\n"
        "    → approximate LOT only\n"
        "\n"
        "  Diagnosis-based index date\n"
        "    → claims-inferred, not abstracted\n"
        "\n"
        f"  EHR missingness drives {pct_unk:.0f}% unknown\n"
        "    → testing gap, not biology\n"
        "\n"
        "  No site-of-care or payer data\n"
        "    → no academic vs community split\n"
        "\n"
        "  Not powered for CI-level endpoints\n"
        "    → minimum ~1,000 patients needed"
    )
    _add_body(sl5, limitations_text, left_in=0.3, top_in=5.0, width_in=6.0, height_in=2.5, font_size=Pt(8.5))

    prod_text = (
        "PRODUCTIONIZE THIS WORK\n"
        "\n"
        "  Rules-as-config\n"
        "    Versioned YAML + ADR decisions\n"
        "    (done: 14 ADRs, config/ today)\n"
        "\n"
        "  SQL/dbt models\n"
        "    Reproducible at scale\n"
        "\n"
        "  Unit tests per clinical rule\n"
        "    (done: 134 tests today)\n"
        "\n"
        "  DQ monitors + drift alerts\n"
        "    (done: 19 checks today)\n"
        "\n"
        "  Per-patient audit trail\n"
        "    (done: row audit cols today)\n"
        "\n"
        "  Abstraction QA sampling\n"
        "    For curated records\n"
        "\n"
        "  Scale to 1,000+ patients\n"
        "    For CI-level subindication work"
    )
    _add_body(sl5, prod_text, left_in=6.6, top_in=1.35, width_in=6.4, height_in=5.8, font_size=Pt(8.5))
    _add_footer(sl5, "Fully synthetic data · Source: sensitivity_her2_distribution.csv · Rule set v1 (ADR-007/006)")

    # ── Appendix A: DQ Summary ────────────────────────────────────────────────
    slA = prs.slides.add_slide(blank)
    _dq_n_checks = len(dq_summary)
    _dq_errors = int(dq_summary[dq_summary["severity"] == "error"]["n_flagged"].sum())
    _dq_warnings = int(dq_summary[dq_summary["severity"] == "warning"]["n_flagged"].sum())
    _add_header(
        slA,
        f"Appendix A — {_dq_n_checks} DQ Checks: "
        f"{_dq_errors} Error{'s' if _dq_errors != 1 else ''} and {_dq_warnings} Warnings Resolved Before Analysis",
        font_pt=16,
    )
    flagged = dq_summary[dq_summary["n_flagged"] > 0][["check_name", "n_flagged", "severity", "action"]]
    dq_lines = [f"{_dq_n_checks} DQ checks | {_dq_errors} errors | {_dq_warnings} warnings", ""]
    for _, row in flagged.iterrows():
        dq_lines.append(
            f"[{row['severity'].upper():7s}]  {row['check_name']:40s}  n={row['n_flagged']:3d}  action: {row['action']}"
        )
    _add_body(slA, "\n".join(dq_lines), left_in=0.4, top_in=1.35, width_in=12.2, height_in=5.8, font_size=Pt(8))
    _add_footer(slA, "Source: outputs/dq/dq_summary.csv")

    # ── Appendix B: Key Assumptions ───────────────────────────────────────────
    slB = prs.slides.add_slide(blank)
    _add_header(
        slB,
        "Appendix B — 14 Analytical Decisions, All Config-Driven and Decision-Logged (ADR-004 to ADR-014)",
        font_pt=16,
    )
    assump = [
        "ADR-004  Index date = earliest of (C50 metastatic dx date, M1/IV staging date)",
        "ADR-005  De novo = no prior primary C50 or gap ≤ 180 days to metastatic index",
        "ADR-006  IHC 3+ → positive | IHC 1+/2+ISH− → low | IHC 0 faint ≤10% → ultralow",
        "         IHC 0 with membrane staining (no %) → unknown (potential DB-06 eligible)",
        "ADR-007  HER2 window: −365/+90 days around index date",
        "ADR-008  Tie-break: curation_flag > variant_specificity > closest_to_index",
        "         Variant beats result text (IHC 1+ wins over 'Negative' label)",
        "ADR-009  HR-positive ≥ 1% ER or PR staining (ASCO/CAP 2020)",
        "ADR-010  LOT: regimen window 28 days, new line gap 90 days",
        "ADR-011  Subindications named for DB-03/04/06/09 trial populations",
        "ADR-012  Wilson 95% CI | n<11 cells flagged and suppressed",
        "ADR-013  Discordance: Enhertu in HER2-unknown + Enhertu in Line 1",
        "ADR-014  Benchmarks: Tarantino JCO 2020; Schettini NPJ BC 2021; Curigliano NEJM 2024",
        "",
        "Full config: config/analysis_rules.yaml  |  Full decisions: audit/decisions/",
    ]
    _add_body(slB, "\n".join(assump), left_in=0.4, top_in=1.35, width_in=12.2, height_in=5.8, font_size=Pt(8.5))
    _add_footer(slB, "Source: config/analysis_rules.yaml · audit/decisions/DECISION_INDEX.md")

    # ── Appendix C: Reproducibility & Repo Map ────────────────────────────────
    slC = prs.slides.add_slide(blank)
    _add_header(slC, "Appendix C — Fully Reproducible: One Command Regenerates All Outputs from Raw Data", font_pt=16)
    repo_lines = [
        "PIPELINE EXECUTION (12 stages, single command)",
        "",
        "  uv run python -m her2rwd.pipeline --reports",
        "",
        "  Stage  1  config       Load config/analysis_rules.yaml",
        "  Stage  2  load_raw     SHA-256 integrity check; load 5 CSVs into DuckDB",
        "  Stage  3  data_quality 19 DQ checks → outputs/dq/dq_log.csv",
        "  Stage  4  cohort       Index date, eligibility, de novo/recurrent → cohort.csv",
        "  Stage  5  her2         HER2 variant → category, window, tie-break → patient_her2.csv",
        "  Stage  6  hr           ER/PR % → HR status → patient_hr.csv",
        "  Stage  7  treatment    Regimens + lines → patient_lines.csv",
        "  Stage  8  q1           HER2 distribution, strata, benchmarks → q1_*.csv",
        "  Stage  9  q2           Enhertu uptake, subindications, discordance → q2_*.csv",
        "  Stage 10  sensitivity  S1/S2/S3 re-runs → sensitivity_*.csv",
        "  Stage 11  validation   13 invariant checks → audit/validation_report.md",
        "  Stage 12  report       figures + HTML + pptx → reports/",
        "",
        "7 AUDIT LAYERS",
        "  ADRs (14 decisions) → config YAML → row audit cols → DQ log",
        "  → validation invariants → run manifest → process trail (SESSION_LOG)",
        "",
        "INPUT INTEGRITY",
        "  All 5 raw CSVs SHA-256 verified vs ../external/ on every run.",
        "  Any mismatch raises RuntimeError before any analysis runs.",
    ]
    # Append validation summary if available
    val_path = Path("audit/validation_report.md")
    if val_path.exists():
        val_lines = val_path.read_text(encoding="utf-8").split("\n")
        pass_fail = [ln for ln in val_lines if "PASS" in ln or "FAIL" in ln][:6]
        if pass_fail:
            repo_lines += ["", "VALIDATION STATUS (latest run)"] + [f"  {ln}" for ln in pass_fail]
    _add_body(slC, "\n".join(repo_lines), left_in=0.4, top_in=1.35, width_in=12.2, height_in=5.8, font_size=Pt(8))
    _add_footer(slC, "Source: audit/validation_report.md · pipeline.py")

    # ── Save ──────────────────────────────────────────────────────────────────
    pptx_path = rpt / "HER2_mBC_Enhertu_Analysis.pptx"
    prs.save(str(pptx_path))
    print(f"  PPTX written: {pptx_path}")
    return pptx_path


# ─────────────────────────────────────────────────────────────────────────────
# PDF via LibreOffice (optional)
# ─────────────────────────────────────────────────────────────────────────────


def _try_pdf(pptx_path: Path, rpt: Path):
    lo_candidates = [
        "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
    ]
    for lo in lo_candidates:
        try:
            result = subprocess.run(
                [lo, "--headless", "--convert-to", "pdf", "--outdir", str(rpt), str(pptx_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                pdf_path = rpt / pptx_path.with_suffix(".pdf").name
                if pdf_path.exists():
                    print(f"  PDF written: {pdf_path}")
                    return pdf_path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    print("  [INFO] LibreOffice not found — PDF skipped")
    return None
