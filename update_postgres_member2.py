import pandas as pd
from sqlalchemy import create_engine, text

def main():
    print("1. Leyendo los datos de la capa Gold (Member 2)...")
    parquet_path = "kedro-pipeline/data/03_primary/member2_gold.parquet"
    df = pd.read_parquet(parquet_path)
    
    print("2. Calculando scores de Riesgo Cardiovascular y Calidad Nutricional...")
    
    # Función simple para calcular riesgo cardiovascular (0-100, mayor es más riesgo)
    def calc_cardio_risk(row):
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

    # Función simple para calcular calidad nutricional (0-100, mayor es mejor)
    def calc_nutri_quality(row):
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
    
    print("3. Conectando a la base de datos PostgreSQL...")
    engine = create_engine('postgresql://postgres:admin@localhost:5434/nhanes_analytics')
    
    print("4. Actualizando los registros existentes (UPDATE)...")
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
        
        print(f"¡Se han actualizado los scores de riesgo y nutrición exitosamente en la base de datos!")

if __name__ == "__main__":
    main()
