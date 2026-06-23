"""
NHANES Ingestion Script -- Matias Retamal (Member 3)
=====================================================
Downloads and converts to Parquet the datasets assigned to Member 3:
  - Laboratory Data:         CBC, BIOPRO, TRIGLY, GHB, HDL
  - Limited Access (Mort):   NCHS public-use mortality linked file

Cycles covered: 2017-2018 (suffix _J) and 2019-2020 (suffix _P)

Usage:
    cd kedro-pipeline
    python ingest_matias_nhanes.py

Requirements: requests, pandas, pyarrow
"""

import os
import sys
import time
import logging
import requests
import pandas as pd
from typing import List, Tuple, Dict

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR    = os.path.join(SCRIPT_DIR, "data", "01_raw")
TEMP_DIR   = os.path.join(SCRIPT_DIR, "data", "temp_xpt")
os.makedirs(RAW_DIR,  exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# HTTP config
# ---------------------------------------------------------------------------
HEADERS  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
CDC_BASE = "https://wwwn.cdc.gov/Nchs/Nhanes"

# ---------------------------------------------------------------------------
# Laboratory files: (file_prefix, nhanes_suffix, cycle_label)
# ---------------------------------------------------------------------------
# Each entry: (file_stem, cycle_label, start_year, parquet_name)
# URL pattern: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{start_year}/DataFiles/{file_stem}.XPT
# 2017-2018 suffix _J | 2019-2020 pre-pandemic suffix _P (CDC combined dataset)
LAB_FILES: List[Tuple[str, str, str, str]] = [
    ("CBC_J",    "2017-2018", "2017", "cbc_2017_2018"),
    ("BIOPRO_J", "2017-2018", "2017", "biopro_2017_2018"),
    ("TRIGLY_J", "2017-2018", "2017", "trigly_2017_2018"),
    ("GHB_J",    "2017-2018", "2017", "ghb_2017_2018"),
    ("HDL_J",    "2017-2018", "2017", "hdl_2017_2018"),
    ("P_CBC",    "2017-2020", "2017", "cbc_2019_2020"),
    ("P_BIOPRO", "2017-2020", "2017", "biopro_2019_2020"),
    ("P_TRIGLY", "2017-2020", "2017", "trigly_2019_2020"),
    ("P_GHB",    "2017-2020", "2017", "ghb_2019_2020"),
    ("P_HDL",    "2017-2020", "2017", "hdl_2019_2020"),
]

# ---------------------------------------------------------------------------
# Mortality files (NCHS fixed-width public-use files)
# ---------------------------------------------------------------------------
MORT_FILES: List[Dict] = [
    {
        "url": (
            "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/"
            "datalinkage/linked_mortality/"
            "NHANES_2017_2018_MORT_2019_PUBLIC.dat"
        ),
        "parquet_name": "mort_2017_2018.parquet",
        "cycle":        "2017-2018",
    },
    # 2019-2020 mortality not yet released by NCHS as of 2024;
    # using 2017-2018 file as proxy for the pre-pandemic combined cycle.
]

# NCHS fixed-width column layout  (start, end, name)
# Source: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality/
MORT_COLSPECS: List[Tuple[int, int, str]] = [
    (0,  6,  "SEQN"),
    (14, 15, "ELIGSTAT"),
    (15, 16, "MORTSTAT"),
    (16, 19, "UCOD_LEADING"),
    (19, 20, "DIABETES"),
    (20, 21, "HYPERTEN"),
    (42, 46, "PERMTH_INT"),
    (46, 50, "PERMTH_EXM"),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def download_file(url: str, dest_path: str, label: str) -> bool:
    """Download a remote file with retries and progress reporting.

    Args:
        url:       Remote URL to fetch.
        dest_path: Local destination path.
        label:     Human-readable label for logging.

    Returns:
        True if the file was downloaded (or already existed), False otherwise.
    """
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 5000:
        logger.info("[SKIP] Already exists (%d KB): %s",
                    os.path.getsize(dest_path) // 1024, label)
        return True

    logger.info("[DOWN] Downloading %s ...", label)
    for attempt in range(1, 4):
        try:
            resp  = requests.get(url, stream=True, headers=HEADERS, timeout=120)
            resp.raise_for_status()
            total      = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
            size_kb = downloaded // 1024
            logger.info("[DOWN] Done: %s (%d KB)", label, size_kb)
            return True
        except Exception as exc:
            logger.warning("[DOWN] Attempt %d/3 failed for %s: %s", attempt, label, exc)
            time.sleep(2 * attempt)

    logger.error("[DOWN] FAILED after 3 attempts: %s", label)
    return False


def is_html_response(path: str) -> bool:
    """Return True if the downloaded file is an HTML error page."""
    try:
        with open(path, "rb") as f:
            return b"<html" in f.read(512).lower()
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Laboratory ingestion
# ---------------------------------------------------------------------------

def ingest_lab_files() -> None:
    """Download NHANES laboratory XPT files and convert them to Parquet."""
    logger.info("=" * 60)
    logger.info("LABORATORY -- XPT to Parquet")
    logger.info("=" * 60)
    ok = skip = fail = 0

    for file_stem, cycle, start_year, parquet_stem in LAB_FILES:
        filename     = f"{file_stem}.XPT"
        parquet_name = f"{parquet_stem}.parquet"
        parquet_path = os.path.join(RAW_DIR, parquet_name)
        xpt_path     = os.path.join(TEMP_DIR, filename)
        url          = f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{start_year}/DataFiles/{filename}"

        if os.path.exists(parquet_path) and os.path.getsize(parquet_path) > 5000:
            logger.info("[SKIP] %s", parquet_name)
            skip += 1
            continue

        downloaded = download_file(url, xpt_path, f"{file_stem} ({cycle})")
        if not downloaded:
            fail += 1
            continue

        if is_html_response(xpt_path):
            logger.error("[ERR ] HTML response (file not found on CDC): %s", filename)
            os.remove(xpt_path)
            fail += 1
            continue

        try:
            df = pd.read_sas(xpt_path, format="xport", encoding="utf-8")
            df.to_parquet(parquet_path, engine="pyarrow", index=False)
            size_kb = os.path.getsize(parquet_path) // 1024
            logger.info("[SAVE] %s | %d rows x %d cols | %d KB",
                        parquet_name, df.shape[0], df.shape[1], size_kb)
            ok += 1
        except Exception as exc:
            logger.error("[ERR ] Converting %s: %s", filename, exc)
            fail += 1
        finally:
            if os.path.exists(xpt_path):
                os.remove(xpt_path)

    logger.info("Laboratory summary -- OK: %d | Skipped: %d | Failed: %d", ok, skip, fail)


# ---------------------------------------------------------------------------
# Mortality / Limited Access ingestion
# ---------------------------------------------------------------------------

def parse_mort_dat(dat_path: str, cycle: str) -> pd.DataFrame:
    """Parse an NCHS fixed-width mortality public-use file.

    Args:
        dat_path: Local path to the .dat file.
        cycle:    Survey cycle label (e.g. '2017-2018').

    Returns:
        pd.DataFrame: Parsed mortality data with numeric columns.
    """
    colspecs = [(s, e) for s, e, _ in MORT_COLSPECS]
    names    = [n for _, _, n in MORT_COLSPECS]

    df = pd.read_fwf(dat_path, colspecs=colspecs, names=names, dtype=str)

    numeric_cols = ["SEQN", "ELIGSTAT", "MORTSTAT", "DIABETES",
                    "HYPERTEN", "PERMTH_INT", "PERMTH_EXM"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.strip(), errors="coerce")

    df["cycle_year"] = cycle
    return df


def ingest_mortality_files() -> None:
    """Download NCHS mortality .dat files and convert them to Parquet."""
    logger.info("=" * 60)
    logger.info("MORTALITY (Limited Access) -- DAT to Parquet")
    logger.info("=" * 60)

    for spec in MORT_FILES:
        parquet_path = os.path.join(RAW_DIR, spec["parquet_name"])
        dat_path     = os.path.join(TEMP_DIR,
                                    spec["parquet_name"].replace(".parquet", ".dat"))

        if os.path.exists(parquet_path) and os.path.getsize(parquet_path) > 1000:
            logger.info("[SKIP] %s", spec["parquet_name"])
            continue

        if not download_file(spec["url"], dat_path, f"Mortality {spec['cycle']}"):
            continue

        try:
            df = parse_mort_dat(dat_path, spec["cycle"])
            df.to_parquet(parquet_path, engine="pyarrow", index=False)
            size_kb = os.path.getsize(parquet_path) // 1024
            logger.info("[SAVE] %s | %d rows x %d cols | %d KB",
                        spec["parquet_name"], df.shape[0], df.shape[1], size_kb)
        except Exception as exc:
            logger.error("[ERR ] Processing %s: %s", spec["parquet_name"], exc)
        finally:
            if os.path.exists(dat_path):
                os.remove(dat_path)


# ---------------------------------------------------------------------------
# Final verification
# ---------------------------------------------------------------------------

def verify_output() -> None:
    """Print a summary of all Parquet files present in data/01_raw/."""
    logger.info("=" * 60)
    logger.info("VERIFICATION -- data/01_raw/")
    logger.info("=" * 60)

    files = sorted(f for f in os.listdir(RAW_DIR) if f.endswith(".parquet"))
    if not files:
        logger.warning("No Parquet files found in data/01_raw/")
        return

    total_mb = 0.0
    for fname in files:
        path = os.path.join(RAW_DIR, fname)
        try:
            df       = pd.read_parquet(path)
            size_mb  = os.path.getsize(path) / (1024 ** 2)
            total_mb += size_mb
            logger.info("  %-40s %8d rows x %3d cols  %.2f MB",
                        fname, df.shape[0], df.shape[1], size_mb)
        except Exception as exc:
            logger.error("  %-40s ERROR: %s", fname, exc)

    logger.info("Total: %d files | %.2f MB", len(files), total_mb)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("[NHANES] Ingesta Matias Retamal (Member 3)")
    logger.info("Laboratory + Limited Access | 2017-2018 & 2019-2020")

    ingest_lab_files()
    ingest_mortality_files()
    verify_output()

    logger.info("Ingestion complete. Run: kedro run --pipeline=processing_m3")
