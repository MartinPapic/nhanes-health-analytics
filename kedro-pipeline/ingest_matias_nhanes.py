"""
Script de Ingesta NHANES — Matías Retamal (Miembro 3)
======================================================
Descarga y convierte a Parquet los datasets asignados:
  · Laboratory Data:       CBC, BIOPRO, TRIGLY, GHB, HDL
  · Limited Access (Mort): Archivo de mortalidad pública NCHS

Ciclos: 2017-2018 (_J) y 2019-2020 (_P)

Uso:
    cd kedro-pipeline
    python ingest_matias_nhanes.py

Dependencias: requests, pandas, pyarrow
"""

import os
import sys
import time
import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
RAW_DIR  = os.path.join(os.path.dirname(__file__), "data", "01_raw")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "data", "temp_xpt")
os.makedirs(RAW_DIR,  exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# URL base oficial del CDC para archivos XPT
CDC_BASE = "https://wwwn.cdc.gov/Nchs/Nhanes"

# ---------------------------------------------------------------------------
# Archivos de Laboratorio por ciclo
# Formato: (prefijo_archivo, sufijo_ciclo, año_inicio_ciclo)
# ---------------------------------------------------------------------------
LAB_FILES = [
    # ── Ciclo 2017-2018 (sufijo _J) ──────────────────────────────────────
    ("CBC",    "_J", "2017-2018"),   # Complete Blood Count
    ("BIOPRO", "_J", "2017-2018"),   # Standard Biochemistry Profile
    ("TRIGLY", "_J", "2017-2018"),   # Cholesterol - LDL & Triglycerides
    ("GHB",    "_J", "2017-2018"),   # Glycohemoglobin (HbA1c)
    ("HDL",    "_J", "2017-2018"),   # Cholesterol - HDL
    # ── Ciclo 2019-2020 (sufijo _P) ──────────────────────────────────────
    ("CBC",    "_P", "2019-2020"),
    ("BIOPRO", "_P", "2019-2020"),
    ("TRIGLY", "_P", "2019-2020"),
    ("GHB",    "_P", "2019-2020"),
    ("HDL",    "_P", "2019-2020"),
]

# ---------------------------------------------------------------------------
# Archivos de Mortalidad (Limited Access — versión pública NCHS)
# Se descargan desde FTP del CDC como archivos .dat de ancho fijo
# ---------------------------------------------------------------------------
MORT_FILES = [
    {
        "url": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality/NHANES_2017_2018_MORT_2019_PUBLIC.dat",
        "parquet_name": "mort_2017_2018.parquet",
        "cycle": "2017-2018",
    },
    {
        "url": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality/NHANES_2019_2020_MORT_2019_PUBLIC.dat",
        "parquet_name": "mort_2019_2020.parquet",
        "cycle": "2019-2020",
    },
]

# Especificación del formato de ancho fijo del archivo de mortalidad NCHS
# Fuente: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality/
MORT_COLSPECS = [
    (0,  6,  "SEQN"),          # Respondent sequence number
    (14, 15, "ELIGSTAT"),      # Eligibility status
    (15, 16, "MORTSTAT"),      # Final mortality status (0=alive, 1=deceased)
    (16, 19, "UCOD_LEADING"), # Underlying cause of death
    (19, 20, "DIABETES"),      # Diabetes flag
    (20, 21, "HYPERTEN"),      # Hypertension flag
    (42, 46, "PERMTH_INT"),    # Person months from interview
    (46, 50, "PERMTH_EXM"),    # Person months from exam
]

# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def download_file(url: str, dest_path: str, label: str) -> bool:
    """Descarga un archivo con reintentos y barra de progreso simple."""
    if os.path.exists(dest_path):
        size = os.path.getsize(dest_path)
        if size > 5000:
            print(f"  ✅ Ya existe ({size/1024:.0f} KB): {label}")
            return True

    print(f"  ⬇️  Descargando {label}...")
    for attempt in range(1, 4):
        try:
            resp = requests.get(url, stream=True, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r     {pct:.0f}%  ({downloaded/1024:.0f} KB)", end="", flush=True)
            print()
            return True
        except Exception as exc:
            print(f"\n  ⚠️  Intento {attempt}/3 fallido: {exc}")
            time.sleep(2 * attempt)

    print(f"  ❌ No se pudo descargar: {label}")
    return False


def is_html(path: str) -> bool:
    """Verifica si el archivo descargado es en realidad una página HTML de error."""
    try:
        with open(path, "rb") as f:
            return b"<html" in f.read(500).lower()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Descarga de archivos de Laboratorio (XPT → Parquet)
# ---------------------------------------------------------------------------

def ingest_lab_files():
    print("\n" + "="*60)
    print("  LABORATORIO — XPT → Parquet")
    print("="*60)
    ok, skip, fail = 0, 0, 0

    for prefix, suffix, cycle in LAB_FILES:
        filename     = f"{prefix}{suffix}.XPT"
        cycle_tag    = cycle.replace("-", "_")
        parquet_name = f"{prefix.lower()}_{cycle_tag}.parquet"
        parquet_path = os.path.join(RAW_DIR, parquet_name)
        xpt_path     = os.path.join(TEMP_DIR, filename)
        url          = f"{CDC_BASE}/{cycle}/DataFiles/{filename}"

        if os.path.exists(parquet_path) and os.path.getsize(parquet_path) > 5000:
            print(f"  ✅ Ya existe: {parquet_name}")
            skip += 1
            continue

        downloaded = download_file(url, xpt_path, f"{prefix} {cycle}")
        if not downloaded:
            fail += 1
            continue

        if is_html(xpt_path):
            print(f"  ❌ Respuesta HTML (archivo no existe en CDC): {filename}")
            os.remove(xpt_path)
            fail += 1
            continue

        try:
            df = pd.read_sas(xpt_path, format="xport", encoding="utf-8")
            df.to_parquet(parquet_path, engine="pyarrow", index=False)
            size_kb = os.path.getsize(parquet_path) / 1024
            print(f"  💾 Guardado: {parquet_name} ({df.shape[0]:,} filas · {df.shape[1]} cols · {size_kb:.0f} KB)")
            ok += 1
        except Exception as exc:
            print(f"  ❌ Error convirtiendo {filename}: {exc}")
            fail += 1
        finally:
            if os.path.exists(xpt_path):
                os.remove(xpt_path)

    print(f"\n  Laboratorio → OK: {ok} | Ya existían: {skip} | Fallidos: {fail}")


# ---------------------------------------------------------------------------
# Descarga de archivos de Mortalidad (DAT ancho fijo → Parquet)
# ---------------------------------------------------------------------------

def parse_mort_dat(dat_path: str, cycle: str) -> pd.DataFrame:
    """Parsea el archivo de ancho fijo de mortalidad NCHS."""
    colspecs = [(s, e) for s, e, _ in MORT_COLSPECS]
    names    = [n for _, _, n in MORT_COLSPECS]

    df = pd.read_fwf(dat_path, colspecs=colspecs, names=names, dtype=str)

    # Conversiones numéricas
    num_cols = ["SEQN", "ELIGSTAT", "MORTSTAT", "DIABETES",
                "HYPERTEN", "PERMTH_INT", "PERMTH_EXM"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.strip(), errors="coerce")

    df["cycle_year"] = cycle
    return df


def ingest_mortality_files():
    print("\n" + "="*60)
    print("  MORTALIDAD (Limited Access) — DAT → Parquet")
    print("="*60)

    for spec in MORT_FILES:
        parquet_path = os.path.join(RAW_DIR, spec["parquet_name"])
        dat_path     = os.path.join(TEMP_DIR, spec["parquet_name"].replace(".parquet", ".dat"))

        if os.path.exists(parquet_path) and os.path.getsize(parquet_path) > 1000:
            print(f"  ✅ Ya existe: {spec['parquet_name']}")
            continue

        downloaded = download_file(spec["url"], dat_path, f"Mortalidad {spec['cycle']}")
        if not downloaded:
            continue

        try:
            df = parse_mort_dat(dat_path, spec["cycle"])
            df.to_parquet(parquet_path, engine="pyarrow", index=False)
            size_kb = os.path.getsize(parquet_path) / 1024
            print(f"  💾 Guardado: {spec['parquet_name']} ({df.shape[0]:,} filas · {df.shape[1]} cols · {size_kb:.0f} KB)")
        except Exception as exc:
            print(f"  ❌ Error procesando {spec['parquet_name']}: {exc}")
        finally:
            if os.path.exists(dat_path):
                os.remove(dat_path)


# ---------------------------------------------------------------------------
# Verificación final
# ---------------------------------------------------------------------------

def verify_output():
    print("\n" + "="*60)
    print("  VERIFICACIÓN FINAL — data/01_raw/")
    print("="*60)
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".parquet")]
    if not files:
        print("  ⚠️  No hay archivos Parquet en data/01_raw/")
        return
    total_mb = 0
    for fname in sorted(files):
        path = os.path.join(RAW_DIR, fname)
        try:
            df   = pd.read_parquet(path)
            size = os.path.getsize(path) / (1024**2)
            total_mb += size
            print(f"  📦 {fname:<40} {df.shape[0]:>8,} filas · {df.shape[1]:>3} cols · {size:.2f} MB")
        except Exception as exc:
            print(f"  ❌ {fname}: {exc}")
    print(f"\n  Total: {len(files)} archivos · {total_mb:.2f} MB")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n🔬 NHANES — Ingesta Matías Retamal (Member 3)")
    print("   Laboratory + Limited Access · 2017-2018 & 2019-2020")
    print("=" * 60)

    ingest_lab_files()
    ingest_mortality_files()
    verify_output()

    print("\n✅ Ingesta completada. Puedes ejecutar:")
    print("   kedro run --pipeline=processing_m3\n")
