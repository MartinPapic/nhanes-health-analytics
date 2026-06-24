import pandas as pd
from tpot import TPOTRegressor
from sklearn.model_selection import train_test_split
import logging

logger = logging.getLogger(__name__)

def merge_and_feature_engineer(m1: pd.DataFrame, m2: pd.DataFrame, m3: pd.DataFrame) -> pd.DataFrame:
    """
    Une los datasets Gold de los 3 miembros cruzando por el SEQN.
    Calcula las variables predictoras (features) y la variable objetivo (target).
    """
    logger.info("Realizando JOIN de las 3 capas Gold (M1, M2, M3) por SEQN...")
    
    # Convertir SEQN a int para un join seguro
    m1['SEQN'] = m1['SEQN'].astype(int)
    m2['SEQN'] = m2['SEQN'].astype(int)
    m3['SEQN'] = m3['SEQN'].astype(int)
    
    df = m1.merge(m2, on='SEQN', how='inner')
    df = df.merge(m3, on='SEQN', how='inner')
    
    logger.info(f"Dataset consolidado con {len(df)} registros.")
    
    # 1. Edades y Género (M1)
    # Al hacer merge, si hay columnas duplicadas pandas agrega _x o _y.
    age_col = [c for c in df.columns if 'RIDAGEYR' in c or 'age_years' in c][0]
    gender_col = [c for c in df.columns if 'RIAGENDR' in c or 'gender' in c][0]
    
    df['age_years'] = df[age_col]
    
    # Manejar codificación de género numérico o texto
    if df[gender_col].dtype == object:
        df['gender_encoded'] = df[gender_col].apply(lambda x: 1 if x in ['Hombre', 'Masculino'] else 0)
    else:
        df['gender_encoded'] = df[gender_col].apply(lambda x: 1 if x == 1.0 else 0)
    
    # 2. Nutrición (M2) - Replicar lógica del script de postgres para consistencia
    def calc_nutri_quality(row):
        score = 100
        kcal = row.get('AVG_KCAL', 2000)
        if pd.isna(kcal): kcal = 2000
        if kcal > 3500 or kcal < 800:
            score -= 40
        elif kcal > 2800 or kcal < 1200:
            score -= 20
        prot = row.get('AVG_PROT', 60)
        if pd.isna(prot): prot = 60
        if prot < 40:
            score -= 30
        return max(0, score)

    df['nutritional_quality_score'] = df.apply(calc_nutri_quality, axis=1)
    
    # 3. BMI (M2)
    df['bmi'] = df['BMXBMI'].fillna(df['BMXBMI'].median())
    
    # 4. Glucosa (M3)
    df['glucose'] = df['LBXSGL'].fillna(df['LBXSGL'].median())
    
    # Target: healthy_aging_score (M1)
    # Manejar nulos en el target
    df = df.dropna(subset=['healthy_aging_score'])
    
    # Seleccionar solo las variables para el modelo
    final_cols = ['age_years', 'gender_encoded', 'nutritional_quality_score', 'bmi', 'glucose', 'healthy_aging_score']
    df_final = df[final_cols].copy()
    
    logger.info("Feature Engineering completado.")
    return df_final

def train_tpot_automl(df: pd.DataFrame):
    """
    Entrena el modelo TPOT usando el dataset unificado de longevidad.
    """
    logger.info("Iniciando entrenamiento de TPOT AutoML (Longevity Model)...")
    
    from tpot import TPOTRegressor
    
    X = df[['age_years', 'gender_encoded', 'nutritional_quality_score', 'bmi', 'glucose']]
    y = df['healthy_aging_score']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Restauramos TPOT. Usamos n_jobs=1 para evitar TimeoutError de Dask en Windows
    tpot = TPOTRegressor(
        max_time_mins=1, 
        generations=2,
        population_size=10, 
        random_state=42,
        n_jobs=1
    )
    
    tpot.fit(X_train, y_train)
    
    # Evaluar con el pipeline ajustado de forma segura
    from sklearn.metrics import r2_score
    preds = tpot.predict(X_test)
    score = r2_score(y_test, preds)
    logger.info(f"Entrenamiento AutoML con TPOT finalizado. Score R2 en test: {score}")
    
    return tpot.fitted_pipeline_
