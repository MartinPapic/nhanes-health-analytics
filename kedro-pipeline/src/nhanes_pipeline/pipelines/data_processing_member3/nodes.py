"""Nodos Kedro — Miembro 3: Laboratory & Limited Access Data.

Author:
    Matías Retamal

Descripción:
    Implementa el pipeline ETL completo bajo arquitectura Medallion:

    Bronze → Silver → Gold → PostgreSQL

    Cubre tarjetas de Trello:
        - [DATA-01][DATA-04]: Ingesta Bronze de datos de laboratorio y acceso limitado.
        - [DATA-02]:          Extracción del diccionario de variables.
        - [ETL-03]:           Pipelines modulares Kedro.
        - [ETL-04][ETL-06]:   Validación de esquemas y separación de anómalos.
        - [ETL-05]:           Feature Engineering para longevidad en capa Gold.
"""

from __future__ import annotations

import logging
import os
from typing import Tuple

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes del módulo
# ---------------------------------------------------------------------------

# Sufijos NHANES por ciclo → usados para leer desde 01_raw
CYCLES = {
    "2017_2018": "2017_2018",
    "2019_2020": "2019_2020",
}

# Archivos de laboratorio a fusionar (uno por SEQN)
LAB_FILE_PREFIXES = ["cbc", "biopro", "trigly", "ghb", "hdl"]

# Archivos de acceso limitado
LIMITED_FILE_PREFIXES = ["mort"]

# Códigos SAS que representan "No sabe / No responde" → tratar como NaN
SAS_MISSING_CODES = [7, 9, 77, 99, 777, 999, 7777, 9999]

# Reglas de validación para capa Silver (columna: (min, max))
VALIDATION_RULES: dict[str, tuple[float, float]] = {
    "LBXGH":   (2.0,  20.0),   # HbA1c (%)
    "LBXTC":   (50.0, 600.0),  # Colesterol Total (mg/dL)
    "LBDHDL":  (5.0,  200.0),  # HDL (mg/dL)
    "LBXTR":   (10.0, 3000.0), # Triglicéridos (mg/dL)
    "LBXSCR":  (0.1,  20.0),   # Creatinina sérica (mg/dL)
    "LBXSGL":  (30.0, 600.0),  # Glucosa sérica (mg/dL)
    "LBXWBCSI":(0.1,  90.0),   # Glóbulos blancos
    "LBXHGB":  (3.0,  25.0),   # Hemoglobina (g/dL)
}

# Variables obligatorias para que un registro sea válido
REQUIRED_COLS = ["SEQN"]

# Umbrales clínicos para feature engineering en Gold
CLINICAL_THRESHOLDS = {
    "hba1c_risk":       ("LBXGH",   6.5),
    "hdl_low_risk":     ("LBDHDL",  40.0),
    "trig_risk":        ("LBXTR",   150.0),
    "creatinine_risk":  ("LBXSCR",  1.2),
    "glucose_risk":     ("LBXSGL",  100.0),
    "wbc_high_risk":    ("LBXWBCSI",11.0),
    "anemia_risk":      ("LBXHGB",  12.0),
}


# ==============================================================================
# NODO 1 — BRONZE: Ingesta y consolidación de datos crudos
# ==============================================================================

def ingest_laboratory_bronze(ingestion_status: str) -> pd.DataFrame:
    """Ingesta y fusión de archivos de Laboratorio en capa Bronze.

    Lee los archivos Parquet crudos de laboratorio (cbc, biopro, trigly, ghb,
    hdl) para los ciclos 2017-2018 y 2019-2020 y los consolida en un único
    DataFrame sin modificar los valores originales.

    Args:
        ingestion_status: Salida del nodo de ingesta previo (señal de control
            del DAG, indica que los archivos raw ya fueron descargados).

    Returns:
        pd.DataFrame: Dataset Bronze consolidado con columna ``cycle_year``.

    Raises:
        ValueError: Si no se encontró ningún archivo de laboratorio válido.

    Note:
        Los archivos deben existir en ``data/01_raw/`` con el patrón
        ``{prefix}_{cycle}.parquet``.
    """
    RAW_DIR = "data/01_raw"
    frames: list[pd.DataFrame] = []

    for cycle_key, cycle_label in CYCLES.items():
        cycle_frame: pd.DataFrame | None = None

        for prefix in LAB_FILE_PREFIXES:
            path = os.path.join(RAW_DIR, f"{prefix}_{cycle_key}.parquet")
            if not os.path.exists(path):
                logger.warning("[Bronze-Lab] Archivo no encontrado: %s — se omite.", path)
                continue

            df_partial = pd.read_parquet(path)
            df_partial["SEQN"] = df_partial["SEQN"].astype(int)

            if cycle_frame is None:
                cycle_frame = df_partial.copy()
            else:
                # Merge externo para no perder registros con datos parciales
                extra_cols = [c for c in df_partial.columns if c != "SEQN"]
                cycle_frame = cycle_frame.merge(
                    df_partial[["SEQN"] + extra_cols],
                    on="SEQN",
                    how="outer",
                )

        if cycle_frame is not None and not cycle_frame.empty:
            cycle_frame["cycle_year"] = cycle_label.replace("_", "-")
            frames.append(cycle_frame)
            logger.info(
                "[Bronze-Lab] Ciclo %s → %d filas, %d columnas.",
                cycle_label, len(cycle_frame), cycle_frame.shape[1],
            )

    if not frames:
        logger.error("[Bronze-Lab] No se encontraron datos. Verifica la ingesta previa.")
        return pd.DataFrame(columns=["SEQN", "cycle_year"])

    df_bronze = pd.concat(frames, ignore_index=True)
    logger.info("[Bronze-Lab] Total consolidado: %d filas.", len(df_bronze))
    return df_bronze


def ingest_limited_access_bronze(ingestion_status: str) -> pd.DataFrame:
    """Ingesta de datos de Acceso Limitado (mortalidad sintética) en Bronze.

    Args:
        ingestion_status: Señal de control del DAG.

    Returns:
        pd.DataFrame: Dataset de mortalidad consolidado con ``cycle_year``.
    """
    RAW_DIR = "data/01_raw"
    frames: list[pd.DataFrame] = []

    for cycle_key, cycle_label in CYCLES.items():
        for prefix in LIMITED_FILE_PREFIXES:
            path = os.path.join(RAW_DIR, f"{prefix}_{cycle_key}.parquet")
            if not os.path.exists(path):
                logger.warning("[Bronze-Ltd] Archivo no encontrado: %s — se omite.", path)
                continue

            df_partial = pd.read_parquet(path)
            if "SEQN" in df_partial.columns:
                df_partial["SEQN"] = df_partial["SEQN"].astype(int)
            df_partial["cycle_year"] = cycle_label.replace("_", "-")
            frames.append(df_partial)
            logger.info("[Bronze-Ltd] %s cargado: %d filas.", path, len(df_partial))

    if not frames:
        logger.warning("[Bronze-Ltd] Sin datos de acceso limitado. DataFrame vacío retornado.")
        return pd.DataFrame(columns=["SEQN", "cycle_year"])

    return pd.concat(frames, ignore_index=True)


def extract_data_dictionary(ingestion_status: str) -> pd.DataFrame:
    """Construye el diccionario de variables para Laboratory & Limited Access.

    Genera un DataFrame documentando cada variable NHANES con su código,
    descripción clínica, unidades, rango esperado y justificación para
    su inclusión en el análisis de longevidad.

    Args:
        ingestion_status: Señal de control del DAG.

    Returns:
        pd.DataFrame: Diccionario de variables estructurado.
    """
    dictionary = [
        # --- Laboratorio ---
        {"codigo": "SEQN",     "seccion": "Identificador", "descripcion": "Respondent sequence number",
         "unidad": "ID",       "rango_min": None, "rango_max": None, "relevancia_longevidad": "Llave primaria"},
        {"codigo": "LBXGH",    "seccion": "Laboratorio",   "descripcion": "Glycohemoglobin (HbA1c)",
         "unidad": "%",        "rango_min": 2.0,  "rango_max": 20.0, "relevancia_longevidad": "Alta — predictor de DM2 y mortalidad"},
        {"codigo": "LBXTC",    "seccion": "Laboratorio",   "descripcion": "Total Cholesterol",
         "unidad": "mg/dL",    "rango_min": 50.0, "rango_max": 600.0,"relevancia_longevidad": "Alta — riesgo cardiovascular"},
        {"codigo": "LBDHDL",   "seccion": "Laboratorio",   "descripcion": "HDL Cholesterol",
         "unidad": "mg/dL",    "rango_min": 5.0,  "rango_max": 200.0,"relevancia_longevidad": "Alta — factor protector cardio"},
        {"codigo": "LBXTR",    "seccion": "Laboratorio",   "descripcion": "Triglycerides",
         "unidad": "mg/dL",    "rango_min": 10.0, "rango_max": 3000.0,"relevancia_longevidad": "Media-Alta — síndrome metabólico"},
        {"codigo": "LBXSCR",   "seccion": "Laboratorio",   "descripcion": "Creatinine, serum",
         "unidad": "mg/dL",    "rango_min": 0.1,  "rango_max": 20.0, "relevancia_longevidad": "Alta — función renal"},
        {"codigo": "LBXSGL",   "seccion": "Laboratorio",   "descripcion": "Glucose, serum",
         "unidad": "mg/dL",    "rango_min": 30.0, "rango_max": 600.0,"relevancia_longevidad": "Alta — riesgo diabético"},
        {"codigo": "LBXWBCSI", "seccion": "Laboratorio",   "descripcion": "White blood cell count",
         "unidad": "1000c/µL", "rango_min": 0.1,  "rango_max": 90.0, "relevancia_longevidad": "Media — marcador inflamatorio"},
        {"codigo": "LBXHGB",   "seccion": "Laboratorio",   "descripcion": "Hemoglobin",
         "unidad": "g/dL",     "rango_min": 3.0,  "rango_max": 25.0, "relevancia_longevidad": "Media — anemia y mortalidad"},
        # --- Acceso Limitado ---
        {"codigo": "MORTSTAT", "seccion": "Limited Access", "descripcion": "Final mortality status",
         "unidad": "0=vivo,1=fallecido", "rango_min": 0, "rango_max": 1, "relevancia_longevidad": "Crítica — variable objetivo"},
        {"codigo": "PERMTH_EXM","seccion": "Limited Access","descripcion": "Permth from exam date",
         "unidad": "meses",    "rango_min": 0, "rango_max": 400, "relevancia_longevidad": "Alta — tiempo hasta evento"},
    ]

    df_dict = pd.DataFrame(dictionary)
    logger.info("[DATA-02] Diccionario generado: %d variables documentadas.", len(df_dict))
    return df_dict


# ==============================================================================
# NODO 2 — SILVER: Validación, limpieza e imputación
# ==============================================================================

def process_laboratory_silver(
    df_bronze: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Limpieza, validación y Quality Gates para datos de Laboratorio.

    Pasos:
        1. Reemplazar códigos SAS de no-respuesta por NaN.
        2. Validar rango numérico por columna (ver ``VALIDATION_RULES``).
        3. Separar registros que violan reglas en ``df_rejected``.
        4. Imputar medianas por ciclo en registros válidos.
        5. Estandarizar nombres de columnas a snake_case.

    Args:
        df_bronze: DataFrame Bronze de laboratorio (sin modificar).

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            - df_silver:   Registros válidos, limpios e imputados.
            - df_rejected: Registros anómalos con columna ``rejection_reason``.

    Note:
        Se conservan **todos** los registros rechazados para auditoría.
        No se eliminan datos; se separan en un reporte independiente.
    """
    if df_bronze.empty:
        logger.warning("[Silver-Lab] DataFrame Bronze vacío. Retornando vacíos.")
        return pd.DataFrame(), pd.DataFrame()

    df = df_bronze.copy()

    # --- Paso 1: Reemplazar códigos SAS ---
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    df[numeric_cols] = df[numeric_cols].replace(SAS_MISSING_CODES, np.nan)
    logger.info("[Silver-Lab] Códigos SAS reemplazados por NaN.")

    # --- Paso 2 y 3: Validaciones por columna ---
    rejection_reasons: dict[int, list[str]] = {i: [] for i in df.index}

    # 2a. SEQN obligatorio
    mask_seqn = df["SEQN"].isna()
    for idx in df.index[mask_seqn]:
        rejection_reasons[idx].append("SEQN nulo")

    # 2b. Rango numérico por variable
    for col, (vmin, vmax) in VALIDATION_RULES.items():
        if col not in df.columns:
            continue
        out_of_range = df[col].notna() & ((df[col] < vmin) | (df[col] > vmax))
        for idx in df.index[out_of_range]:
            rejection_reasons[idx].append(f"{col} fuera de rango [{vmin},{vmax}]")

    # Separar válidos / rechazados
    rejected_idx = [idx for idx, reasons in rejection_reasons.items() if reasons]
    valid_idx    = [idx for idx in df.index if idx not in rejected_idx]

    df_rejected = df.loc[rejected_idx].copy()
    df_rejected["rejection_reason"] = [
        " | ".join(rejection_reasons[i]) for i in rejected_idx
    ]

    df_silver = df.loc[valid_idx].copy()
    logger.info(
        "[Silver-Lab] Válidos: %d | Rechazados: %d (%.1f%%)",
        len(df_silver), len(df_rejected),
        100 * len(df_rejected) / max(len(df), 1),
    )

    # --- Paso 4: Imputación por mediana agrupada por ciclo ---
    lab_cols = [c for c in VALIDATION_RULES.keys() if c in df_silver.columns]
    for col in lab_cols:
        df_silver[col] = df_silver.groupby("cycle_year")[col].transform(
            lambda x: x.fillna(x.median())
        )

    logger.info("[Silver-Lab] Imputación por mediana completada.")
    return df_silver, df_rejected


def process_limited_access_silver(
    df_bronze: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Limpieza y validación de datos de Acceso Limitado (mortalidad).

    Valida que ``MORTSTAT`` esté en {0, 1} y que ``PERMTH_EXM`` sea >= 0.
    Registros que no cumplan son separados en ``df_rejected``.

    Args:
        df_bronze: DataFrame Bronze de acceso limitado.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            - df_silver:   Registros válidos.
            - df_rejected: Registros anómalos con razón de rechazo.
    """
    if df_bronze.empty:
        logger.warning("[Silver-Ltd] DataFrame Bronze vacío.")
        return pd.DataFrame(), pd.DataFrame()

    df = df_bronze.copy()
    df[df.select_dtypes(include="number").columns] = \
        df.select_dtypes(include="number").replace(SAS_MISSING_CODES, np.nan)

    rejection_reasons: dict[int, list[str]] = {i: [] for i in df.index}

    if "SEQN" in df.columns:
        for idx in df.index[df["SEQN"].isna()]:
            rejection_reasons[idx].append("SEQN nulo")

    if "MORTSTAT" in df.columns:
        invalid_mort = df["MORTSTAT"].notna() & ~df["MORTSTAT"].isin([0, 1])
        for idx in df.index[invalid_mort]:
            rejection_reasons[idx].append("MORTSTAT inválido (esperado 0 o 1)")

    if "PERMTH_EXM" in df.columns:
        neg_months = df["PERMTH_EXM"].notna() & (df["PERMTH_EXM"] < 0)
        for idx in df.index[neg_months]:
            rejection_reasons[idx].append("PERMTH_EXM negativo")

    rejected_idx = [i for i, r in rejection_reasons.items() if r]
    valid_idx    = [i for i in df.index if i not in rejected_idx]

    df_rejected = df.loc[rejected_idx].copy()
    df_rejected["rejection_reason"] = [
        " | ".join(rejection_reasons[i]) for i in rejected_idx
    ]

    logger.info(
        "[Silver-Ltd] Válidos: %d | Rechazados: %d",
        len(valid_idx), len(rejected_idx),
    )
    return df.loc[valid_idx].copy(), df_rejected


# ==============================================================================
# NODO 3 — GOLD: Feature Engineering para Longevidad
# ==============================================================================

def build_laboratory_gold(
    df_lab_silver: pd.DataFrame,
    df_ltd_silver: pd.DataFrame,
) -> pd.DataFrame:
    """Feature Engineering — Capa Gold para predicción de longevidad.

    Genera los siguientes features a partir de biomarcadores de laboratorio:

    - Flags binarios de riesgo clínico por umbral (ej. ``hba1c_risk``).
    - Índice compuesto de riesgo metabólico (``metabolic_risk_score``).
    - Índice de riesgo renal (``renal_risk_score``).
    - Índice de inflamación sistémica (``inflammation_score``).
    - Score global de longevidad (``longevity_risk_index``, 0-100).

    Se une (left join) con datos de mortalidad para enriquecer el dataset
    sin introducir data leakage (mortalidad solo como contexto, no feature).

    Args:
        df_lab_silver: Dataset Silver de laboratorio validado.
        df_ltd_silver: Dataset Silver de acceso limitado (mortalidad).

    Returns:
        pd.DataFrame: Dataset Gold con features analíticas para dashboard
            y modelos de ML.
    """
    if df_lab_silver.empty:
        logger.warning("[Gold] df_lab_silver vacío. No se puede construir Gold.")
        return pd.DataFrame()

    df = df_lab_silver.copy()

    # --- Feature 1: Flags de riesgo binario por umbral clínico ---
    for feature_name, (col, threshold) in CLINICAL_THRESHOLDS.items():
        if col not in df.columns:
            df[feature_name] = np.nan
            continue
        if feature_name == "hdl_low_risk":
            # HDL: riesgo si BAJO del umbral
            df[feature_name] = (df[col] < threshold).astype(float)
        elif feature_name == "anemia_risk":
            df[feature_name] = (df[col] < threshold).astype(float)
        else:
            df[feature_name] = (df[col] > threshold).astype(float)

    # --- Feature 2: Score metabólico (HbA1c + Triglicéridos + Glucosa) ---
    metabolic_flags = ["hba1c_risk", "trig_risk", "glucose_risk"]
    available_metabolic = [f for f in metabolic_flags if f in df.columns]
    if available_metabolic:
        df["metabolic_risk_score"] = df[available_metabolic].sum(axis=1) / len(available_metabolic)
    else:
        df["metabolic_risk_score"] = np.nan

    # --- Feature 3: Score renal (Creatinina) ---
    df["renal_risk_score"] = df.get("creatinine_risk", pd.Series(np.nan, index=df.index))

    # --- Feature 4: Score inflamatorio (WBC) ---
    if "LBXWBCSI" in df.columns:
        # Normalización min-max dentro del rango clínico
        wbc_min, wbc_max = 0.1, 90.0
        df["inflammation_score"] = ((df["LBXWBCSI"] - wbc_min) / (wbc_max - wbc_min)).clip(0, 1)
    else:
        df["inflammation_score"] = np.nan

    # --- Feature 5: Índice Global de Riesgo para Longevidad (0-100) ---
    # Suma ponderada de riesgos → escala de 0 (saludable) a 100 (alto riesgo)
    weights = {
        "metabolic_risk_score": 0.35,
        "renal_risk_score":     0.25,
        "inflammation_score":   0.20,
        "hdl_low_risk":         0.10,
        "anemia_risk":          0.10,
    }
    score_cols = [c for c in weights if c in df.columns]
    if score_cols:
        df["longevity_risk_index"] = sum(
            df[col].fillna(0) * w
            for col, w in weights.items() if col in df.columns
        ) * 100
        df["longevity_risk_index"] = df["longevity_risk_index"].round(2)

    # --- Unión con mortalidad (solo contexto, NO target leakage) ---
    if not df_ltd_silver.empty and "SEQN" in df_ltd_silver.columns:
        mortality_cols = ["SEQN"]
        if "MORTSTAT" in df_ltd_silver.columns:
            mortality_cols.append("MORTSTAT")
        if "PERMTH_EXM" in df_ltd_silver.columns:
            mortality_cols.append("PERMTH_EXM")

        df_mort = df_ltd_silver[mortality_cols].drop_duplicates("SEQN")
        df = df.merge(df_mort, on="SEQN", how="left")
        logger.info("[Gold] Dataset de mortalidad unido correctamente.")

    # Columna de auditoría
    df["pipeline_version"] = "member3-v1.0"
    df["data_section"]     = "laboratory_limited_access"

    logger.info(
        "[Gold] Dataset Gold construido: %d filas, %d columnas.",
        len(df), df.shape[1],
    )
    return df


# ==============================================================================
# NODO 4 — EXPORT: Ingesta en PostgreSQL
# ==============================================================================

def export_gold_to_postgres(
    df_gold: pd.DataFrame,
    credentials: dict,
) -> str:
    """Exporta el dataset Gold a PostgreSQL usando SQLAlchemy.

    Crea o reemplaza la tabla ``nhanes_lab_gold`` en el esquema ``public``.
    Utiliza ``chunksize=1000`` para escritura eficiente en lotes.

    Args:
        df_gold:     Dataset Gold listo para producción.
        credentials: Diccionario con claves ``host``, ``port``, ``database``,
                     ``user`` y ``password`` (proveniente de ``credentials.yml``).

    Returns:
        str: Mensaje de confirmación con número de registros insertados.

    Raises:
        RuntimeError: Si la conexión a PostgreSQL falla o el DataFrame está vacío.
    """
    if df_gold.empty:
        msg = "[PostgreSQL] Dataset Gold vacío. No se exportó nada."
        logger.warning(msg)
        return msg

    host     = credentials.get("host", "localhost")
    port     = credentials.get("port", 5432)
    database = credentials.get("database", "nhanes")
    user     = credentials.get("user", "postgres")
    password = credentials.get("password", "")

    conn_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

    try:
        engine = create_engine(conn_str, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # health-check
        logger.info("[PostgreSQL] Conexión exitosa a %s:%s/%s", host, port, database)
    except Exception as exc:
        raise RuntimeError(
            f"[PostgreSQL] No se pudo conectar: {exc}"
        ) from exc

    try:
        df_gold.to_sql(
            name="nhanes_lab_gold",
            con=engine,
            schema="public",
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi",
        )
        n = len(df_gold)
        msg = f"[PostgreSQL] ✅ {n:,} registros insertados en public.nhanes_lab_gold."
        logger.info(msg)
        return msg
    except Exception as exc:
        raise RuntimeError(f"[PostgreSQL] Error en escritura: {exc}") from exc
    finally:
        engine.dispose()
