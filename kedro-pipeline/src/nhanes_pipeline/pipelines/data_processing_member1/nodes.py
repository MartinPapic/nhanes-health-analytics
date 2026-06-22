import pandas as pd
import numpy as np
import os

def merge_and_clean_silver_layer(ingestion_status: str) -> pd.DataFrame:
    """Cruza los 12 archivos de cada ciclo y filtra a los menores de edad."""
    RAW_DIR = "data/01_raw"
    QUESTIONNAIRES = ["mcq", "diq", "bpq", "cdq", "smq", "alq", "paq", "slq", "whq", "dpq", "pfq"]

    def process_cycle(cycle_suffix, cycle_label):
        demo_path = os.path.join(RAW_DIR, f"demo_{cycle_suffix}.parquet")
        if not os.path.exists(demo_path):
            return pd.DataFrame()
            
        df_base = pd.read_parquet(demo_path)
        if 'RIDAGEYR' in df_base.columns:
            df_base = df_base[df_base['RIDAGEYR'] >= 20]

        df_base['SEQN'] = df_base['SEQN'].astype(int)
        
        for q_prefix in QUESTIONNAIRES:
            q_path = os.path.join(RAW_DIR, f"{q_prefix}_{cycle_suffix}.parquet")
            if os.path.exists(q_path):
                df_q = pd.read_parquet(q_path)
                df_q['SEQN'] = df_q['SEQN'].astype(int)
                # Limpiar respuestas SAS (NaN)
                df_q = df_q.replace([7, 9, 77, 99, 777, 999, 7777, 9999], np.nan)
                df_base = df_base.merge(df_q, on='SEQN', how='left')
        
        df_base['cycle_year'] = cycle_label
        return df_base

    df_15_16 = process_cycle("2015_2016", "2015-2016")
    df_17_18 = process_cycle("2017_2018", "2017-2018")
    
    if not df_15_16.empty and not df_17_18.empty:
        df_silver = pd.concat([df_15_16, df_17_18], ignore_index=True)
    else:
        df_silver = pd.DataFrame()
        
    return df_silver

def validate_silver_layer(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Realiza validaciones de esquema, rangos y valores nulos (ETL-04).
    Genera un reporte de registros rechazados (ETL-06).
    """
    if df.empty:
        return df, pd.DataFrame()
        
    # Reglas de validación:
    # 1. SEQN no debe ser nulo
    # 2. RIDAGEYR debe estar entre 20 y 120
    # 3. RIAGENDR debe ser 1 o 2
    
    invalid_mask = (
        df['SEQN'].isna() |
        (df['RIDAGEYR'] < 20) | (df['RIDAGEYR'] > 120) |
        (~df['RIAGENDR'].isin([1.0, 2.0]))
    )
    
    df_valid = df[~invalid_mask].copy()
    df_rejected = df[invalid_mask].copy()
    
    # Añadir motivo de rechazo
    if not df_rejected.empty:
        df_rejected['rejection_reason'] = "Fallo de validación en SEQN, Edad o Género"
        
    return df_valid, df_rejected
