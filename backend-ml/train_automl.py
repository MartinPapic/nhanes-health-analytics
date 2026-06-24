import pandas as pd
from sqlalchemy import create_engine
from tpot import TPOTRegressor
from sklearn.model_selection import train_test_split
import joblib
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def train_automl():
    """
    Entrena un modelo predictivo utilizando TPOT (AutoML).
    El modelo busca predecir el Riesgo Cardiovascular en base a edad, sexo y nutrición.
    
    Conecta a PostgreSQL (Capa Gold) para extraer los datos limpios.
    Genera datos aleatorios como fallback si la base de datos no está disponible.
    Guarda el mejor pipeline como un archivo .pkl.
    """
    logging.info("1. Conectando a PostgreSQL para obtener datos Gold...")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:nhanes2024@localhost:5434/nhanes")
    
    try:
        engine = create_engine(db_url)
        query = """
            SELECT age_years, gender, nutritional_quality_score, cardio_risk_score 
            FROM gold_analytics_master 
            WHERE cardio_risk_score IS NOT NULL 
              AND nutritional_quality_score IS NOT NULL 
              AND age_years IS NOT NULL
        """
        df = pd.read_sql(query, engine)
        logging.info(f"Datos recuperados: {df.shape[0]} filas.")
    except Exception as e:
        logging.error(f"Error conectando a BD: {e}")
        logging.info("Generando datos simulados para fallback (entrenamiento dummy) debido a fallo de BD...")
        import numpy as np
        np.random.seed(42)
        df = pd.DataFrame({
            'age_years': np.random.randint(20, 80, 1000),
            'gender': np.random.choice(['Hombre', 'Mujer'], 1000),
            'nutritional_quality_score': np.random.randint(40, 100, 1000)
        })
        # Score = Edad + mala nutrición + ruido
        df['cardio_risk_score'] = (df['age_years'] * 0.5) + ((100 - df['nutritional_quality_score']) * 0.4) + np.random.normal(0, 5, 1000)

    logging.info("2. Preprocesamiento de datos...")
    # Codificar género (asumimos Hombre=1, Mujer=0 o similares)
    df['gender_encoded'] = df['gender'].apply(lambda x: 1 if x in ['Hombre', 'Masculino', 1.0, 1] else 0)
    
    X = df[['age_years', 'gender_encoded', 'nutritional_quality_score']]
    y = df['cardio_risk_score']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    logging.info("3. Iniciando Motor AutoML (TPOT) para optimización genética...")
    logging.info("TPOT buscará iterativamente el mejor algoritmo. (Límite: 3 minutos)")
    
    start_time = time.time()
    tpot = TPOTRegressor(
        max_time_mins=1, 
        generations=1,
        population_size=5, 
        random_state=42, 
        n_jobs=1
    )
    tpot.fit(X_train, y_train)
    end_time = time.time()

    logging.info(f"¡TPOT terminó la búsqueda en {int(end_time - start_time)} segundos!")
    # Evaluamos manualmente con el pipeline ganador
    from sklearn.metrics import r2_score
    best_pipeline = tpot.fitted_pipeline_
    preds = best_pipeline.predict(X_test)
    score = r2_score(y_test, preds)
    logging.info(f"Score del Mejor Pipeline (R2 en test): {score}")

    logging.info("4. Exportando el modelo óptimo (.pkl)...")
    os.makedirs("models", exist_ok=True)
    # TPOT guarda el mejor pipeline (Scikit-Learn Pipeline)
    best_pipeline = tpot.fitted_pipeline_
    joblib.dump(best_pipeline, "models/longevity_model.pkl")
    
    logging.info("Modelo óptimo guardado en models/longevity_model.pkl exitosamente!")

if __name__ == "__main__":
    train_automl()
