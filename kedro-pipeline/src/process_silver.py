import pandas as pd
import numpy as np
import os

# Configuración de carpetas
RAW_DIR = "data/01_raw"
INTERMEDIATE_DIR = "data/02_intermediate"

# Asegurar que el directorio de salida exista
os.makedirs(INTERMEDIATE_DIR, exist_ok=True)

# Lista de cuestionarios a unir por paciente (Excluimos 'demo' porque será la tabla base)
QUESTIONNAIRES = ["mcq", "diq", "bpq", "cdq", "smq", "alq", "paq", "slq", "whq", "dpq", "pfq"]

def process_cycle(cycle_suffix, cycle_label):
    print(f"\n--- Procesando Ciclo {cycle_label} ---")
    
    # 1. Cargar Demografía (Base)
    demo_path = os.path.join(RAW_DIR, f"demo_{cycle_suffix}.parquet")
    if not os.path.exists(demo_path):
        print(f"No se encontró {demo_path}")
        return pd.DataFrame()
        
    df_base = pd.read_parquet(demo_path)
    print(f"Demografía inicial ({cycle_label}): {df_base.shape[0]} pacientes.")

    # 2. Filtrar solo adultos (Metodología para Evitar Missingness Estructural en NHANES)
    # RIDAGEYR es la edad en años.
    if 'RIDAGEYR' in df_base.columns:
        df_base = df_base[df_base['RIDAGEYR'] >= 20]
        print(f"Demografía tras filtro de adultos (>=20): {df_base.shape[0]} pacientes.")
    else:
        print("ADVERTENCIA: No se encontró la columna RIDAGEYR.")

    # Asegurar que SEQN sea entero para evitar problemas en el cruce
    df_base['SEQN'] = df_base['SEQN'].astype(int)
    
    # 3. Unir los 11 cuestionarios
    for q_prefix in QUESTIONNAIRES:
        q_path = os.path.join(RAW_DIR, f"{q_prefix}_{cycle_suffix}.parquet")
        if os.path.exists(q_path):
            df_q = pd.read_parquet(q_path)
            df_q['SEQN'] = df_q['SEQN'].astype(int)
            
            # Limpiar respuestas SAS "Refused" (7, 77, 777) y "Don't know" (9, 99, 999)
            # Reemplazamos todos los 77, 99, etc. por nulos de pandas (NaN)
            # Nota: Esto es un barrido general muy útil. En variables específicas se puede afinar más.
            df_q = df_q.replace([7, 9, 77, 99, 777, 999, 7777, 9999], np.nan)
            
            # Left join: mantenemos todos los adultos, incluso si no tienen este cuestionario
            df_base = df_base.merge(df_q, on='SEQN', how='left')
        else:
            print(f"  Falta cuestionario {q_prefix} para el ciclo {cycle_label}")

    # 4. Agregar etiqueta de ciclo para cuando unamos ambos años
    df_base['cycle_year'] = cycle_label
    
    print(f"Dimensiones finales ciclo {cycle_label}: {df_base.shape}")
    return df_base

def main():
    # Procesar ciclo 2015-2016
    df_15_16 = process_cycle("2015_2016", "2015-2016")
    
    # Procesar ciclo 2017-2018
    df_17_18 = process_cycle("2017_2018", "2017-2018")
    
    # Unir ambos ciclos
    print("\n--- Uniendo Ambos Ciclos ---")
    if not df_15_16.empty and not df_17_18.empty:
        df_silver = pd.concat([df_15_16, df_17_18], ignore_index=True)
        print(f"Súper Tabla Final (Silver): {df_silver.shape[0]} pacientes y {df_silver.shape[1]} variables.")
        
        # Guardar a Parquet
        output_path = os.path.join(INTERMEDIATE_DIR, "member1_silver.parquet")
        df_silver.to_parquet(output_path, engine='pyarrow', index=False)
        print(f"[EXITO] Archivo guardado con éxito en {output_path}")
    else:
        print("[ERROR] Faltan datos para crear la tabla Silver.")

if __name__ == "__main__":
    main()
