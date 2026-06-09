import pandas as pd
import numpy as np

def calculate_healthy_aging_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el Healthy Aging Score utilizando la metodología del Frailty Index (Índice de Acumulación de Déficit).
    
    Lógica:
    1. Se definen N factores de riesgo (Déficits).
    2. Si el paciente presenta el riesgo = 1, si no (o nulo) = 0.
    3. Frailty Index = Suma de déficits / N
    4. Healthy Aging Score = (1 - Frailty Index) * 100
    """
    df_gold = df.copy()
    
    # Déficit 1: Diabetes (DIQ010 == 1 significa que un médico le diagnosticó diabetes)
    # Lógica de imputación: Si es nulo, asumimos ausencia de diabetes (0)
    if 'DIQ010' in df_gold.columns:
        df_gold['deficit_diabetes'] = np.where(df_gold['DIQ010'] == 1.0, 1.0, 0.0)
    else:
        df_gold['deficit_diabetes'] = 0.0
        
    # Déficit 2: Síntomas Depresivos (DPQ020: Frecuencia de sentirse deprimido. 1, 2 o 3 indican presencia)
    if 'DPQ020' in df_gold.columns:
        df_gold['deficit_depression'] = np.where(df_gold['DPQ020'].isin([1.0, 2.0, 3.0]), 1.0, 0.0)
    else:
        df_gold['deficit_depression'] = 0.0

    # Déficit 3: Tabaquismo (SMQ020 == 1 significa que ha fumado al menos 100 cigarros en su vida)
    if 'SMQ020' in df_gold.columns:
        df_gold['deficit_smoking'] = np.where(df_gold['SMQ020'] == 1.0, 1.0, 0.0)
    else:
        df_gold['deficit_smoking'] = 0.0

    # Cálculo matemático
    total_deficits_evaluated = 3.0
    
    # Acumulamos déficits
    df_gold['total_deficits'] = (
        df_gold['deficit_diabetes'] + 
        df_gold['deficit_depression'] + 
        df_gold['deficit_smoking']
    )
    
    # Aplicamos Frailty Index y lo invertimos para que sea un Score de "Salud"
    frailty_index = df_gold['total_deficits'] / total_deficits_evaluated
    df_gold['healthy_aging_score'] = (1.0 - frailty_index) * 100.0
    
    # Limpiamos columnas temporales
    df_gold = df_gold.drop(columns=['deficit_diabetes', 'deficit_depression', 'deficit_smoking', 'total_deficits'])
    
    return df_gold

def define_longevity_groups(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica a los pacientes en grupos de longevidad basándose en su edad (RIDAGEYR).
    Respeta el Top-Coding del CDC (>=80 años).
    """
    def categorize_age(age):
        if pd.isna(age):
            return "Desconocido"
        elif age >= 80:
            return "Longevidad Extrema (80+)"
        elif age >= 65:
            return "Longevidad Alta (65-79)"
        else:
            return "Longevidad Base (<65)"

    if 'RIDAGEYR' in df.columns:
        df['longevity_group'] = df['RIDAGEYR'].apply(categorize_age)
    
    return df
