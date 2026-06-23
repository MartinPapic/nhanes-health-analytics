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
    
    # Lista de variables y sus reglas para sumar un punto de déficit
    deficits_rules = {
        'DIQ010': lambda x: np.where(x == 1.0, 1.0, 0.0), # Diabetes
        'DPQ020': lambda x: np.where(x.isin([1.0, 2.0, 3.0]), 1.0, 0.0), # Depresión
        'SMQ020': lambda x: np.where(x == 1.0, 1.0, 0.0), # Tabaquismo
        'MCQ160A': lambda x: np.where(x == 1.0, 1.0, 0.0), # Artritis
        'MCQ220': lambda x: np.where(x == 1.0, 1.0, 0.0), # Cáncer
        'MCQ160L': lambda x: np.where(x == 1.0, 1.0, 0.0), # Hígado
        'BPQ020': lambda x: np.where(x == 1.0, 1.0, 0.0), # Hipertensión
        'BPQ080': lambda x: np.where(x == 1.0, 1.0, 0.0), # Colesterol alto
        'CDQ001': lambda x: np.where(x == 1.0, 1.0, 0.0), # Dolor pecho
        'SLQ050': lambda x: np.where(x == 1.0, 1.0, 0.0), # Problemas dormir
        'PFQ061B': lambda x: np.where(x.isin([2.0, 3.0, 4.0]), 1.0, 0.0), # Dificultad para caminar
        'PFQ061C': lambda x: np.where(x.isin([2.0, 3.0, 4.0]), 1.0, 0.0) # Dificultad para subir escalones
    }

    df_gold['total_deficits'] = 0.0
    total_deficits_evaluated = len(deficits_rules)
    
    for col, rule in deficits_rules.items():
        if col in df_gold.columns:
            df_gold['total_deficits'] += rule(df_gold[col])

    # Aplicamos Frailty Index y lo invertimos para que sea un Score de "Salud"
    frailty_index = df_gold['total_deficits'] / total_deficits_evaluated
    df_gold['healthy_aging_score'] = (1.0 - frailty_index) * 100.0
    
    # Limpiamos
    df_gold = df_gold.drop(columns=['total_deficits'])
    
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
