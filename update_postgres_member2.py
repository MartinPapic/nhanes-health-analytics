import pandas as pd
from sqlalchemy import create_engine, text
import logging

# Configurar logging profesional
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Ejecuta el proceso de actualización de la Capa Gold para el Miembro 2.
    Lee los datos desde formato Parquet, calcula scores analíticos (Riesgo Cardiovascular 
    y Calidad Nutricional) y actualiza la tabla maestra 'gold_analytics_master' 
    en PostgreSQL usando los SEQN correspondientes.
    """
    logging.info("1. Leyendo los datos de la capa Gold (Member 2)...")
    parquet_path = "kedro-pipeline/data/03_primary/member2_gold.parquet"
    df = pd.read_parquet(parquet_path)
    
    logging.info("2. Calculando scores de Riesgo Cardiovascular y Calidad Nutricional...")
    
    def calc_cardio_risk(row):
        """
        Calcula el puntaje de riesgo cardiovascular (0-100).
        Penaliza presiones sistólicas altas y un índice de masa corporal (BMI) elevado.
        """
        risk = 20 # Riesgo base
        
        # Penalización por presión arterial alta
        sys = row.get('BPXSY1', 120)
        if sys > 140: risk += 40
        elif sys > 130: risk += 20
        
        # Penalización por BMI (Índice de Masa Corporal)
        bmi = row.get('BMXBMI', 22)
        if bmi > 30: risk += 40 # Obesidad
        elif bmi > 25: risk += 15 # Sobrepeso
        
        return min(100, max(0, risk))

    def calc_nutri_quality(row):
        """
        Calcula el puntaje de calidad nutricional (0-100).
        Penaliza déficits o excesos calóricos extremos y dietas bajas en proteínas.
        """
        score = 100
        
        kcal = row.get('AVG_KCAL', 2000)
        # Penalización por exceso o déficit calórico severo
        if kcal > 3500 or kcal < 800:
            score -= 40
        elif kcal > 2800 or kcal < 1200:
            score -= 20
            
        # Penalización por baja proteína
        prot = row.get('AVG_PROT', 60)
        if prot < 40:
            score -= 30
            
        return max(0, score)

    df['cardio_risk_score'] = df.apply(calc_cardio_risk, axis=1)
    df['nutritional_quality_score'] = df.apply(calc_nutri_quality, axis=1)
    
    # Preparamos el dataframe solo con lo que vamos a actualizar
    df_update = df[['SEQN', 'cardio_risk_score', 'nutritional_quality_score']].copy()
    df_update.rename(columns={'SEQN': 'seqn'}, inplace=True)
    df_update.dropna(inplace=True)
    
    logging.info("3. Conectando a la base de datos PostgreSQL...")
    engine = create_engine('postgresql://postgres:nhanes2024@localhost:5434/nhanes')
    
    logging.info("4. Actualizando los registros existentes (UPDATE)...")
    with engine.begin() as conn:
        # Subimos los datos temporalmente
        df_update.to_sql('temp_member2_scores', conn, if_exists='replace', index=False)
        
        # Hacemos el UPDATE cruzando con el SEQN (ID del paciente)
        update_query = text('''
            UPDATE gold_analytics_master g
            SET cardio_risk_score = t.cardio_risk_score,
                nutritional_quality_score = t.nutritional_quality_score
            FROM temp_member2_scores t
            WHERE g.seqn = t.seqn;
        ''')
        result = conn.execute(update_query)
        
        # Limpiamos la tabla temporal
        conn.execute(text("DROP TABLE temp_member2_scores;"))
        
        logging.info("¡Se han actualizado los scores de riesgo y nutrición exitosamente en la base de datos!")

if __name__ == "__main__":
    main()
