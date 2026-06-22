import pandas as pd
from sqlalchemy import create_engine

def load_data():
    # 1. Leer el archivo Parquet de la capa Gold
    parquet_path = "kedro-pipeline/data/03_primary/member1_gold.parquet"
    print(f"Leyendo datos desde: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    
    # 2. Renombrar y derivar columnas
    df_db = df.rename(columns={
        "SEQN": "seqn",
        "RIDAGEYR": "age_years",
        "RIAGENDR": "gender",
        "longevity_group": "longevity_group",
        "healthy_aging_score": "healthy_aging_score"
    })
    
    # Mapear ciclo
    df_db['survey_cycle'] = df['SDDSRVYR'].map({9.0: '2015-2016', 10.0: '2017-2018'}).fillna('Unknown')
    
    # Transformar género de numérico a string para mayor claridad si es necesario,
    # O mantenerlo. En la tabla es VARCHAR. 1 = Male, 2 = Female.
    df_db['gender'] = df_db['gender'].map({1.0: 'Hombre', 2.0: 'Mujer'}).fillna('Desconocido')
    
    # Seleccionar solo las columnas necesarias
    cols_to_insert = ["seqn", "survey_cycle", "age_years", "gender", "longevity_group", "healthy_aging_score"]
    df_db = df_db[cols_to_insert]
    
    # 3. Conectar a PostgreSQL
    engine = create_engine('postgresql://postgres:admin@localhost:5432/nhanes_analytics')
    
    # 4. Insertar en la tabla gold_analytics_master
    print("Insertando datos en PostgreSQL...")
    df_db.to_sql('gold_analytics_master', engine, if_exists='append', index=False)
    print(f"¡Se han insertado {len(df_db)} registros exitosamente!")

if __name__ == "__main__":
    load_data()
