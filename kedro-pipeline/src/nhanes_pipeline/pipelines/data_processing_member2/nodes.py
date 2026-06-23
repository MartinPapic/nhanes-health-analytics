import pandas as pd
import numpy as np
import os


def merge_and_clean_silver_layer(ingestion_status: str) -> pd.DataFrame:
    """
    Une datos NHANES de dieta y examen físico.
    Genera capa silver para análisis de longevidad.
    """

    RAW_DIR = "data/01_raw"

    def process_cycle(suffix, label):

        demo_path = os.path.join(
            RAW_DIR,
            f"demo_{suffix}.parquet"
        )

        if not os.path.exists(demo_path):
            return pd.DataFrame()

        demo = pd.read_parquet(demo_path)

        # Adultos para análisis de longevidad
        demo = demo[
            demo["RIDAGEYR"] >= 20
        ]

        demo["SEQN"] = demo["SEQN"].astype(int)


        # ----------------
        # Dieta día 1
        # ----------------

        diet1_path = os.path.join(
            RAW_DIR,
            f"dr1tot_{suffix}.parquet"
        )

        if os.path.exists(diet1_path):

            diet1 = pd.read_parquet(diet1_path)

            diet1["SEQN"] = (
                diet1["SEQN"]
                .astype(int)
            )

            cols = [
                "SEQN",
                "DR1TKCAL",
                "DR1TPROT",
                "DR1TCARB",
                "DR1TTFAT"
            ]

            diet1 = diet1[
                [c for c in cols if c in diet1]
            ]

            demo = demo.merge(
                diet1,
                on="SEQN",
                how="left"
            )


        # ----------------
        # Dieta día 2
        # ----------------

        diet2_path = os.path.join(
            RAW_DIR,
            f"dr2tot_{suffix}.parquet"
        )

        if os.path.exists(diet2_path):

            diet2 = pd.read_parquet(diet2_path)

            diet2["SEQN"] = (
                diet2["SEQN"]
                .astype(int)
            )

            cols = [
                "SEQN",
                "DR2TKCAL",
                "DR2TPROT",
                "DR2TCARB",
                "DR2TTFAT"
            ]

            diet2 = diet2[
                [c for c in cols if c in diet2]
            ]

            demo = demo.merge(
                diet2,
                on="SEQN",
                how="left"
            )


        # ----------------
        # Medidas corporales
        # ----------------

        bmx_path = os.path.join(
            RAW_DIR,
            f"bmx_{suffix}.parquet"
        )

        if os.path.exists(bmx_path):

            bmx = pd.read_parquet(bmx_path)

            bmx["SEQN"] = (
                bmx["SEQN"]
                .astype(int)
            )

            demo = demo.merge(
                bmx[
                    [
                    "SEQN",
                    "BMXWT",
                    "BMXHT",
                    "BMXBMI"
                    ]
                ],
                on="SEQN",
                how="left"
            )


        # ----------------
        # Presión Arterial
        # ----------------

        bpx_path = os.path.join(
            RAW_DIR,
            f"bpx_{suffix}.parquet"
        )

        if os.path.exists(bpx_path):

            bpx = pd.read_parquet(bpx_path)

            bpx["SEQN"] = (
                bpx["SEQN"]
                .astype(int)
            )

            demo = demo.merge(
                bpx[
                    [
                    "SEQN",
                    "BPXSY1",
                    "BPXDI1"
                    ]
                ],
                on="SEQN",
                how="left"
            )


        demo["cycle_year"] = label

        return demo


    df1 = process_cycle(
        "2015_2016",
        "2015-2016"
    )

    df2 = process_cycle(
        "2017_2018",
        "2017-2018"
    )


    return pd.concat(
        [df1, df2],
        ignore_index=True
    )

def transform_silver_to_gold(df_silver: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Toma la capa silver de Claudio, limpia valores nulos, crea promedios 
    para la dieta y genera categorías para análisis (Capa Gold).
    Además extrae los registros anómalos para auditoría.
    """
    df = df_silver.copy()
    
    # 1. Eliminar duplicados
    df = df.drop_duplicates(subset=['SEQN'])
    
    # 2. Promediar días de dieta (Día 1 y Día 2)
    # Si un paciente solo tiene el día 1, nos quedamos con ese valor
    df['AVG_KCAL'] = df[['DR1TKCAL', 'DR2TKCAL']].mean(axis=1)
    df['AVG_PROT'] = df[['DR1TPROT', 'DR2TPROT']].mean(axis=1)
    df['AVG_CARB'] = df[['DR1TCARB', 'DR2TCARB']].mean(axis=1)
    df['AVG_FAT']  = df[['DR1TTFAT', 'DR2TTFAT']].mean(axis=1)
    
    # Botar las columnas de días individuales
    cols_to_drop = ['DR1TKCAL', 'DR2TKCAL', 'DR1TPROT', 'DR2TPROT', 
                    'DR1TCARB', 'DR2TCARB', 'DR1TTFAT', 'DR2TTFAT']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    # 3. Limpieza de NaNs en variables clave de salud y Detección de Anomalías
    # Separamos los registros inválidos
    mask_invalid = df['BMXBMI'].isna() | df['BPXSY1'].isna() | df['BPXDI1'].isna() | (df['BPXSY1'] > 250)
    
    df_rejected = df[mask_invalid].copy()
    df_rejected['REJECTION_REASON'] = 'Valores nulos en signos vitales o fuera de rango lógico'
    
    # Nos quedamos con los datos limpios
    df = df[~mask_invalid].copy()
    
    # 4. Crear categorías para el BMI
    def categorize_bmi(bmi):
        if bmi < 18.5: return 'Bajo peso'
        elif bmi < 25: return 'Normal'
        elif bmi < 30: return 'Sobrepeso'
        else: return 'Obesidad'
        
    df['BMI_CATEGORY'] = df['BMXBMI'].apply(categorize_bmi)
    
    # 5. Rellenar nulos restantes en dieta con la mediana
    diet_cols = ['AVG_KCAL', 'AVG_PROT', 'AVG_CARB', 'AVG_FAT']
    for col in diet_cols:
        df[col] = df[col].fillna(df[col].median())
        
    return df, df_rejected