import os
import requests
import pandas as pd

# Ciclos y sus respectivos sufijos
CYCLES = {
    "2015-2016": "_I",
    "2017-2018": "_J"
}

# Archivos a descargar (Prefijo)
FILES = [
    "DEMO", # Demographics
    "MCQ",  # Medical Conditions
    "DIQ",  # Diabetes
    "BPQ",  # Blood Pressure & Cholesterol
    "CDQ",  # Cardiovascular Disease
    "SMQ",  # Smoking
    "ALQ",  # Alcohol Use
    "PAQ",  # Physical Activity
    "SLQ",  # Sleep Disorders
    "WHQ",  # Weight History
    "DPQ",  # Mental Health - Depression
    "PFQ"   # Physical Functioning
]

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"
RAW_DIR = "data/01_raw"
TEMP_DIR = "data/temp_xpt"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def download_and_convert():
    total_files = len(CYCLES) * len(FILES)
    current = 1
    
    for cycle_year, suffix in CYCLES.items():
        for file_prefix in FILES:
            # Extraer el año de inicio (ej: "2015" de "2015-2016")
            start_year = cycle_year.split('-')[0]
            filename = f"{file_prefix}{suffix}.xpt"
            url = f"{BASE_URL}/{start_year}/DataFiles/{filename}"
            xpt_path = os.path.join(TEMP_DIR, filename)
            parquet_filename = f"{file_prefix.lower()}_{cycle_year.replace('-', '_')}.parquet"
            parquet_path = os.path.join(RAW_DIR, parquet_filename)
            
            print(f"[{current}/{total_files}] Procesando {filename}...")
            current += 1
            
            # 1. Descargar el archivo XPT
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
                response = requests.get(url, stream=True, headers=headers)
                response.raise_for_status()
                with open(xpt_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            except requests.exceptions.RequestException as e:
                print(f"  [ERROR] Error descargando {url}: {e}")
                continue
                
            # Verificar si el archivo es un 404 disfrazado de 200
            if os.path.getsize(xpt_path) < 10000:
                with open(xpt_path, 'rb') as f:
                    if b'html' in f.read(500).lower():
                        print(f"  [ERROR] {url} retornó una página web, no un archivo XPT.")
                        os.remove(xpt_path)
                        continue
                
            # 2. Convertir a Parquet usando Pandas
            try:
                df = pd.read_sas(xpt_path, format='xport')
                # Optimización: reducir el tamaño de las columnas flotantes de SAS a enteros donde aplique
                # (Opcional, pero SAS guarda todo como float64)
                df.to_parquet(parquet_path, engine='pyarrow', index=False)
                print(f"  [OK] Guardado como {parquet_filename}")
            except Exception as e:
                print(f"  [ERROR] Error convirtiendo {filename} a Parquet: {e}")
                
            # 3. Limpiar XPT temporal para ahorrar espacio
            if os.path.exists(xpt_path):
                os.remove(xpt_path)

    print("\n[EXITO] ¡Ingesta completada! Todos los archivos están en formato Parquet en data/01_raw/")

if __name__ == "__main__":
    download_and_convert()
