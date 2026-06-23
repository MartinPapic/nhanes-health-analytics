"""Nodos Kedro — Miembro 3: Laboratory & Limited Access Data.

Author:
    Matías Retamal

Covers:
    [DATA-01][DATA-04] Bronze ingestion · [DATA-02] Data dictionary
    [ETL-03] Modular Kedro pipelines · [ETL-04][ETL-06] Quality gates
    [ETL-05] Longevity feature engineering · [PM-03] Git traceability
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

CYCLES: Dict[str, str] = {"2017_2018": "2017-2018", "2019_2020": "2019-2020"}

LAB_PREFIXES: List[str] = ["cbc", "biopro", "trigly", "ghb", "hdl"]

SAS_MISSING: List[int] = [7, 9, 77, 99, 777, 999, 7777, 9999]

# Clinical valid ranges  (NHANES variable: (min, max))
RANGE_RULES: Dict[str, Tuple[float, float]] = {
    "LBXGH":    (2.0,   20.0),
    "LBXTC":    (50.0,  600.0),
    "LBDHDL":   (5.0,   200.0),
    "LBXTR":    (10.0,  3000.0),
    "LBXSCR":   (0.1,   20.0),
    "LBXSGL":   (30.0,  600.0),
    "LBXWBCSI": (0.1,   90.0),
    "LBXHGB":   (3.0,   25.0),
}

# Longevity feature definitions (name: (column, threshold, direction))
# direction: "above" = risk if value > threshold; "below" = risk if value < threshold
LONGEVITY_FEATURES: Dict[str, Tuple[str, float, str]] = {
    "hba1c_risk":      ("LBXGH",    6.5,   "above"),
    "cholesterol_risk":("LBXTC",    200.0, "above"),
    "hdl_low_risk":    ("LBDHDL",   40.0,  "below"),
    "triglyceride_risk":("LBXTR",   150.0, "above"),
    "renal_risk":      ("LBXSCR",   1.2,   "above"),
    "glucose_risk":    ("LBXSGL",   100.0, "above"),
    "leukocytosis_risk":("LBXWBCSI",11.0,  "above"),
    "anemia_risk":     ("LBXHGB",   12.0,  "below"),
}

FEATURE_WEIGHTS: Dict[str, float] = {
    "hba1c_risk":       0.20,
    "cholesterol_risk": 0.10,
    "hdl_low_risk":     0.10,
    "triglyceride_risk":0.10,
    "renal_risk":       0.20,
    "glucose_risk":     0.15,
    "leukocytosis_risk":0.05,
    "anemia_risk":      0.10,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

@dataclass
class QualityReport:
    """Accumulates data quality metrics across pipeline steps."""

    dataset: str
    total_rows: int = 0
    valid_rows: int = 0
    rejected_rows: int = 0
    rejection_breakdown: Dict[str, int] = field(default_factory=dict)
    null_rates: Dict[str, float] = field(default_factory=dict)
    imputed_cols: List[str] = field(default_factory=list)

    def rejection_rate(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return round(self.rejected_rows / self.total_rows * 100, 2)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([{
            "dataset":         self.dataset,
            "total_rows":      self.total_rows,
            "valid_rows":      self.valid_rows,
            "rejected_rows":   self.rejected_rows,
            "rejection_rate_%":self.rejection_rate(),
            "rejection_breakdown": str(self.rejection_breakdown),
            "imputed_cols":    ", ".join(self.imputed_cols),
        }])


def _load_parquet(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        logger.warning("File not found, skipping: %s", path)
        return pd.DataFrame()
    df = pd.read_parquet(path)
    logger.debug("Loaded %s → %d rows × %d cols", path, *df.shape)
    return df


def _replace_sas_missing(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include="number").columns
    return df.assign(**{c: df[c].replace(SAS_MISSING, np.nan) for c in num_cols})


def _apply_range_rules(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, int]]:
    rejection_reasons: Dict[int, List[str]] = {i: [] for i in df.index}

    for col, (lo, hi) in RANGE_RULES.items():
        if col not in df.columns:
            continue
        mask = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
        for idx in df.index[mask]:
            rejection_reasons[idx].append(f"{col}∉[{lo},{hi}]")

    mask_seqn = df["SEQN"].isna() if "SEQN" in df.columns else pd.Series(False, index=df.index)
    for idx in df.index[mask_seqn]:
        rejection_reasons[idx].append("SEQN=null")

    rejected_idx = [i for i, r in rejection_reasons.items() if r]
    valid_idx    = list(set(df.index) - set(rejected_idx))

    breakdown: Dict[str, int] = {}
    for reasons in rejection_reasons.values():
        for r in reasons:
            breakdown[r] = breakdown.get(r, 0) + 1

    df_rej          = df.loc[rejected_idx].copy()
    df_rej["rejection_reason"] = [
        " | ".join(rejection_reasons[i]) for i in rejected_idx
    ]

    return df.loc[valid_idx].copy(), df_rej, breakdown


def _impute_by_cycle_median(df: pd.DataFrame, cols: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    imputed: List[str] = []
    for col in cols:
        if col not in df.columns:
            continue
        before = df[col].isna().sum()
        df[col] = df.groupby("cycle_year")[col].transform(
            lambda x: x.fillna(x.median())
        )
        after = df[col].isna().sum()
        if before > after:
            imputed.append(col)
            logger.debug("Imputed %d nulls in %s via cycle median.", before - after, col)
    return df, imputed


# ---------------------------------------------------------------------------
# NODE 1 — BRONZE: Ingest laboratory raw files
# ---------------------------------------------------------------------------

def ingest_laboratory_bronze(ingestion_status: str) -> pd.DataFrame:
    """Read and consolidate raw NHANES laboratory Parquet files into Bronze.

    Merges CBC, BIOPRO, TRIGLY, GHB and HDL files for cycles 2017-2018
    and 2019-2020 via outer join on ``SEQN``, preserving every respondent
    even when only partial lab panels are available.

    Args:
        ingestion_status (str): DAG control signal from the upstream
            ingestion node confirming raw files have been downloaded.

    Returns:
        pd.DataFrame: Consolidated Bronze dataset with ``cycle_year`` label.
            Empty DataFrame if no source files are found.
    """
    raw = "data/01_raw"
    frames: List[pd.DataFrame] = []

    for cycle_key, cycle_label in CYCLES.items():
        cycle_df: pd.DataFrame | None = None

        for prefix in LAB_PREFIXES:
            path = os.path.join(raw, f"{prefix}_{cycle_key}.parquet")
            partial = _load_parquet(path)
            if partial.empty:
                continue

            partial["SEQN"] = partial["SEQN"].astype(int)

            if cycle_df is None:
                cycle_df = partial.copy()
            else:
                extra = [c for c in partial.columns if c != "SEQN"]
                cycle_df = cycle_df.merge(partial[["SEQN"] + extra],
                                          on="SEQN", how="outer")

        if cycle_df is not None and not cycle_df.empty:
            cycle_df["cycle_year"] = cycle_label
            frames.append(cycle_df)
            logger.info("[Bronze-Lab] %s → %d rows × %d cols",
                        cycle_label, *cycle_df.shape)

    if not frames:
        logger.error("[Bronze-Lab] No lab files found. Run ingest_matias_nhanes.py first.")
        return pd.DataFrame(columns=["SEQN", "cycle_year"])

    result = pd.concat(frames, ignore_index=True)
    logger.info("[Bronze-Lab] Total consolidated: %d rows.", len(result))
    return result


# ---------------------------------------------------------------------------
# NODE 2 — BRONZE: Ingest mortality / limited-access files
# ---------------------------------------------------------------------------

def ingest_limited_access_bronze(ingestion_status: str) -> pd.DataFrame:
    """Read NCHS public-use mortality files into Bronze.

    Args:
        ingestion_status (str): DAG control signal.

    Returns:
        pd.DataFrame: Combined mortality dataset with ``cycle_year``.
    """
    raw = "data/01_raw"
    frames: List[pd.DataFrame] = []

    for cycle_key, cycle_label in CYCLES.items():
        path = os.path.join(raw, f"mort_{cycle_key}.parquet")
        df = _load_parquet(path)
        if df.empty:
            continue
        if "SEQN" in df.columns:
            df["SEQN"] = df["SEQN"].astype(int)
        df["cycle_year"] = cycle_label
        frames.append(df)
        logger.info("[Bronze-Ltd] %s → %d rows", cycle_label, len(df))

    if not frames:
        logger.warning("[Bronze-Ltd] No mortality files found.")
        return pd.DataFrame(columns=["SEQN", "cycle_year"])

    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# NODE 3 — BRONZE: Data dictionary
# ---------------------------------------------------------------------------

def extract_data_dictionary(ingestion_status: str) -> pd.DataFrame:
    """Build the canonical variable dictionary for Laboratory & Limited Access.

    Documents each NHANES variable with its code, section, clinical
    description, measurement unit, valid range, and justification for
    its inclusion in the longevity analysis pipeline.

    Args:
        ingestion_status (str): DAG control signal.

    Returns:
        pd.DataFrame: Data dictionary with one row per variable.
    """
    entries = [
        ("SEQN",      "ID",             "Respondent sequence number",         "ID",        None,  None,   "Primary key — mandatory"),
        ("LBXGH",     "Laboratory",     "Glycohemoglobin HbA1c",              "%",         2.0,   20.0,   "High — chronic glucose, DM2 mortality predictor"),
        ("LBXTC",     "Laboratory",     "Total Cholesterol",                  "mg/dL",     50.0,  600.0,  "High — cardiovascular risk"),
        ("LBDHDL",    "Laboratory",     "HDL Cholesterol",                    "mg/dL",     5.0,   200.0,  "High — cardioprotective, inversely related to CVD"),
        ("LBXTR",     "Laboratory",     "Triglycerides",                      "mg/dL",     10.0,  3000.0, "Medium-High — metabolic syndrome"),
        ("LBXSCR",    "Laboratory",     "Creatinine, serum",                  "mg/dL",     0.1,   20.0,   "High — chronic kidney disease marker"),
        ("LBXSGL",    "Laboratory",     "Glucose, serum",                     "mg/dL",     30.0,  600.0,  "High — diabetes / pre-diabetes"),
        ("LBXWBCSI",  "Laboratory",     "White blood cell count",             "1000c/µL",  0.1,   90.0,   "Medium — systemic inflammation"),
        ("LBXHGB",    "Laboratory",     "Hemoglobin",                         "g/dL",      3.0,   25.0,   "Medium — anemia linked to mortality"),
        ("MORTSTAT",  "Limited Access", "Final mortality status",             "0/1",       0.0,   1.0,    "Critical — outcome variable"),
        ("PERMTH_EXM","Limited Access", "Person-months from exam date",       "months",    0.0,   400.0,  "High — survival time"),
        ("UCOD_LEADING","Limited Access","Leading underlying cause of death", "ICD code",  None,  None,   "High — cause-specific analysis"),
        ("DIABETES",  "Limited Access", "Diabetes as contributing cause",     "0/1",       0.0,   1.0,    "High — chronic disease attribution"),
        ("HYPERTEN",  "Limited Access", "Hypertension as contributing cause", "0/1",       0.0,   1.0,    "High — chronic disease attribution"),
    ]

    df = pd.DataFrame(entries, columns=[
        "nhanes_code", "section", "description",
        "unit", "range_min", "range_max", "longevity_relevance"
    ])
    logger.info("[DATA-02] Data dictionary built: %d variables.", len(df))
    return df


# ---------------------------------------------------------------------------
# NODE 4 — SILVER: Validate and clean laboratory data
# ---------------------------------------------------------------------------

def process_laboratory_silver(
    df_bronze: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Clean, validate and impute NHANES Laboratory Bronze data.

    Pipeline:

    1. **SAS missing replacement** — codes 7, 9, 77, 99, 777, 999 → ``NaN``.
    2. **Range validation** — per-column clinical boundaries (see ``RANGE_RULES``).
    3. **SEQN completeness** — records without a valid respondent ID are rejected.
    4. **Rejection separation** — anomalous records captured with ``rejection_reason``
       for full auditability (ETL-06); they are never deleted.
    5. **Cycle-median imputation** — remaining nulls in lab columns filled
       with the median of their own survey cycle (ETL-04).

    Args:
        df_bronze (pd.DataFrame): Raw laboratory Bronze dataset.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            - **df_silver**: Valid, cleaned and imputed records.
            - **df_rejected**: Anomalous records with ``rejection_reason`` column.

    Note:
        Quality metrics are emitted via ``logging.INFO`` and can be captured
        by Kedro's logging pipeline for reporting purposes.
    """
    if df_bronze.empty:
        logger.warning("[Silver-Lab] Empty Bronze input. Returning empty datasets.")
        return pd.DataFrame(), pd.DataFrame()

    qr = QualityReport(dataset="laboratory_silver", total_rows=len(df_bronze))

    df = _replace_sas_missing(df_bronze.copy())
    qr.null_rates = {
        c: round(df[c].isna().mean() * 100, 2)
        for c in df.select_dtypes(include="number").columns
    }

    df_valid, df_rejected, breakdown = _apply_range_rules(df)
    qr.valid_rows        = len(df_valid)
    qr.rejected_rows     = len(df_rejected)
    qr.rejection_breakdown = breakdown

    lab_cols = [c for c in RANGE_RULES if c in df_valid.columns]
    df_valid, qr.imputed_cols = _impute_by_cycle_median(df_valid, lab_cols)

    logger.info(
        "[Silver-Lab] valid=%d | rejected=%d (%.1f%%) | imputed_cols=%s",
        qr.valid_rows, qr.rejected_rows, qr.rejection_rate(),
        qr.imputed_cols,
    )

    return df_valid, df_rejected


# ---------------------------------------------------------------------------
# NODE 5 — SILVER: Validate limited-access / mortality data
# ---------------------------------------------------------------------------

def process_limited_access_silver(
    df_bronze: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Clean and validate NCHS public-use mortality Bronze data.

    Validation rules:
        - ``SEQN`` must not be null.
        - ``MORTSTAT`` must be in ``{0, 1}`` when present.
        - ``PERMTH_EXM`` must be ``≥ 0`` when present.

    Args:
        df_bronze (pd.DataFrame): Mortality Bronze dataset.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            - **df_silver**: Valid mortality records.
            - **df_rejected**: Records violating constraints.
    """
    if df_bronze.empty:
        logger.warning("[Silver-Ltd] Empty Bronze input.")
        return pd.DataFrame(), pd.DataFrame()

    df = _replace_sas_missing(df_bronze.copy())
    rejection_reasons: Dict[int, List[str]] = {i: [] for i in df.index}

    if "SEQN" in df.columns:
        for idx in df.index[df["SEQN"].isna()]:
            rejection_reasons[idx].append("SEQN=null")

    if "MORTSTAT" in df.columns:
        mask = df["MORTSTAT"].notna() & ~df["MORTSTAT"].isin([0.0, 1.0])
        for idx in df.index[mask]:
            rejection_reasons[idx].append("MORTSTAT∉{0,1}")

    if "PERMTH_EXM" in df.columns:
        mask = df["PERMTH_EXM"].notna() & (df["PERMTH_EXM"] < 0)
        for idx in df.index[mask]:
            rejection_reasons[idx].append("PERMTH_EXM<0")

    rejected_idx = [i for i, r in rejection_reasons.items() if r]
    valid_idx    = list(set(df.index) - set(rejected_idx))

    df_rej = df.loc[rejected_idx].copy()
    df_rej["rejection_reason"] = [
        " | ".join(rejection_reasons[i]) for i in rejected_idx
    ]

    logger.info("[Silver-Ltd] valid=%d | rejected=%d", len(valid_idx), len(rejected_idx))
    return df.loc[valid_idx].copy(), df_rej


# ---------------------------------------------------------------------------
# NODE 6 — GOLD: Feature engineering for longevity
# ---------------------------------------------------------------------------

def build_laboratory_gold(
    df_lab_silver: pd.DataFrame,
    df_ltd_silver: pd.DataFrame,
) -> pd.DataFrame:
    """Engineer longevity features from validated laboratory data (Gold layer).

    Feature catalogue:

    Binary risk flags (1 = at risk, 0 = normal):
        ``hba1c_risk``, ``cholesterol_risk``, ``hdl_low_risk``,
        ``triglyceride_risk``, ``renal_risk``, ``glucose_risk``,
        ``leukocytosis_risk``, ``anemia_risk``

    Composite scores:
        - ``metabolic_score``: weighted mean of glycaemic and lipid risks (0-1).
        - ``renal_inflammatory_score``: combined kidney + WBC risk (0-1).
        - ``longevity_risk_index``: weighted sum of all risk flags, scaled 0-100.
          Higher values indicate greater all-cause mortality risk.

    Mortality linkage:
        Left-joined with ``df_ltd_silver`` on ``SEQN``.
        Mortality columns (``MORTSTAT``, ``PERMTH_EXM``) are kept as
        **context only** and must not be used as model features to avoid
        data leakage.

    Args:
        df_lab_silver (pd.DataFrame): Validated laboratory Silver dataset.
        df_ltd_silver (pd.DataFrame): Validated mortality Silver dataset.

    Returns:
        pd.DataFrame: Gold dataset ready for dashboard and ML consumption.
    """
    if df_lab_silver.empty:
        logger.warning("[Gold] Empty lab Silver input. Cannot build Gold layer.")
        return pd.DataFrame()

    df = df_lab_silver.copy()

    # ── Binary risk flags ────────────────────────────────────────────────────
    for feat, (col, threshold, direction) in LONGEVITY_FEATURES.items():
        if col not in df.columns:
            df[feat] = np.nan
            continue
        if direction == "above":
            df[feat] = (df[col] > threshold).astype("float32")
        else:
            df[feat] = (df[col] < threshold).astype("float32")

    # ── Metabolic composite score ─────────────────────────────────────────────
    metabolic_flags = ["hba1c_risk", "glucose_risk", "triglyceride_risk",
                       "cholesterol_risk", "hdl_low_risk"]
    available = [f for f in metabolic_flags if f in df.columns]
    df["metabolic_score"] = (
        df[available].mean(axis=1) if available else np.nan
    )

    # ── Renal + inflammatory composite ───────────────────────────────────────
    renal_inf = ["renal_risk", "leukocytosis_risk"]
    available_ri = [f for f in renal_inf if f in df.columns]
    df["renal_inflammatory_score"] = (
        df[available_ri].mean(axis=1) if available_ri else np.nan
    )

    # ── Longevity Risk Index (0-100, higher = worse prognosis) ───────────────
    df["longevity_risk_index"] = sum(
        df[feat].fillna(0) * w
        for feat, w in FEATURE_WEIGHTS.items()
        if feat in df.columns
    ) * 100.0
    df["longevity_risk_index"] = df["longevity_risk_index"].round(2).astype("float32")

    # ── Risk tier classification ──────────────────────────────────────────────
    def _tier(score: float) -> str:
        if score < 20:   return "Low"
        elif score < 45: return "Moderate"
        elif score < 70: return "High"
        return "Critical"

    df["risk_tier"] = df["longevity_risk_index"].apply(_tier)

    # ── Mortality linkage (context only, no leakage) ──────────────────────────
    if not df_ltd_silver.empty and "SEQN" in df_ltd_silver.columns:
        mort_cols = ["SEQN"] + [
            c for c in ("MORTSTAT", "PERMTH_EXM", "DIABETES", "HYPERTEN")
            if c in df_ltd_silver.columns
        ]
        df = df.merge(
            df_ltd_silver[mort_cols].drop_duplicates("SEQN"),
            on="SEQN", how="left",
        )
        logger.info("[Gold] Mortality data joined on SEQN.")

    # ── Audit columns ─────────────────────────────────────────────────────────
    df["pipeline_member"]  = "member3_matias_retamal"
    df["pipeline_version"] = "2.0.0"
    df["data_sections"]    = "laboratory|limited_access"

    logger.info("[Gold] Built: %d rows × %d cols | LRI mean=%.1f",
                len(df), df.shape[1], df["longevity_risk_index"].mean())
    return df


# ---------------------------------------------------------------------------
# NODE 7 — GOLD: Quality report
# ---------------------------------------------------------------------------

def generate_quality_report(
    df_lab_silver: pd.DataFrame,
    df_lab_rejected: pd.DataFrame,
    df_ltd_silver: pd.DataFrame,
    df_ltd_rejected: pd.DataFrame,
) -> pd.DataFrame:
    """Produce a consolidated data quality report across Silver layers.

    Computes per-dataset metrics: row counts, rejection rates, null
    rates per column, and imputation coverage. Designed to be exported
    as CSV for dashboard consumption and academic evidence.

    Args:
        df_lab_silver (pd.DataFrame):   Valid laboratory records.
        df_lab_rejected (pd.DataFrame): Rejected laboratory records.
        df_ltd_silver (pd.DataFrame):   Valid mortality records.
        df_ltd_rejected (pd.DataFrame): Rejected mortality records.

    Returns:
        pd.DataFrame: Quality report with one row per dataset.
    """
    rows = []
    for name, valid, rejected in [
        ("laboratory",     df_lab_silver, df_lab_rejected),
        ("limited_access", df_ltd_silver, df_ltd_rejected),
    ]:
        total = len(valid) + len(rejected)
        null_summary = {
            c: round(valid[c].isna().mean() * 100, 2)
            for c in valid.select_dtypes(include="number").columns
        } if not valid.empty else {}

        rows.append({
            "dataset":         name,
            "total_input":     total,
            "valid_rows":      len(valid),
            "rejected_rows":   len(rejected),
            "rejection_rate_%":round(len(rejected) / max(total, 1) * 100, 2),
            "null_rates_summary": str(null_summary),
        })

    df_report = pd.DataFrame(rows)
    logger.info("[QualityReport] Generated for %d datasets.", len(df_report))
    return df_report


# ---------------------------------------------------------------------------
# NODE 8 — EXPORT: Write Gold to PostgreSQL
# ---------------------------------------------------------------------------

def export_gold_to_postgres(
    df_gold: pd.DataFrame,
    credentials: dict,
) -> str:
    """Export the Gold dataset to PostgreSQL via SQLAlchemy.

    Writes ``df_gold`` to table ``public.nhanes_lab_gold`` using
    ``IF EXISTS REPLACE`` semantics and chunked inserts for efficiency.

    Args:
        df_gold (pd.DataFrame): Gold-layer dataset.
        credentials (dict): Keys: ``host``, ``port``, ``database``,
            ``user``, ``password``. Loaded from ``conf/local/parameters.yml``.

    Returns:
        str: Human-readable confirmation message with row count.

    Raises:
        RuntimeError: On connection failure or write error.
    """
    if df_gold.empty:
        msg = "[PostgreSQL] Gold dataset is empty — nothing exported."
        logger.warning(msg)
        return msg

    conn_str = (
        "postgresql+psycopg2://"
        f"{credentials['user']}:{credentials['password']}"
        f"@{credentials.get('host','localhost')}:{credentials.get('port',5432)}"
        f"/{credentials['database']}"
    )

    try:
        engine = create_engine(conn_str, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(f"[PostgreSQL] Connection failed: {exc}") from exc

    try:
        df_gold.to_sql(
            name="nhanes_lab_gold",
            con=engine,
            schema="public",
            if_exists="replace",
            index=False,
            chunksize=500,
            method="multi",
        )
        n   = len(df_gold)
        msg = f"[PostgreSQL] {n:,} rows → public.nhanes_lab_gold"
        logger.info(msg)
        return msg
    except Exception as exc:
        raise RuntimeError(f"[PostgreSQL] Write error: {exc}") from exc
    finally:
        engine.dispose()
