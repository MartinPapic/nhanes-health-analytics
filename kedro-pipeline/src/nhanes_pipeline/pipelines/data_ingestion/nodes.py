import os
import requests
import pandas as pd

def download_cdc_data() -> str:
    """Descarga los datos crudos del CDC y los convierte a Parquet."""
    
    CYCLES = {"2015-2016": "_I", "2017-2018": "_J"}
    FILES = ["DEMO", "MCQ", "DIQ", "BPQ", "CDQ", "SMQ", "ALQ", "PAQ", "SLQ", "WHQ", "DPQ", "PFQ", "DR1TOT", "DR2TOT", "BPX", "BMX"]
    BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"
    RAW_DIR = "data/01_raw"
    TEMP_DIR = "data/temp_xpt"

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for cycle_year, suffix in CYCLES.items():
        start_year = cycle_year.split('-')[0]
        for file_prefix in FILES:
            filename = f"{file_prefix}{suffix}.xpt"
            url = f"{BASE_URL}/{start_year}/DataFiles/{filename}"
            xpt_path = os.path.join(TEMP_DIR, filename)
            parquet_filename = f"{file_prefix.lower()}_{cycle_year.replace('-', '_')}.parquet"
            parquet_path = os.path.join(RAW_DIR, parquet_filename)
            
            if os.path.exists(parquet_path):
                continue
                
            try:
                response = requests.get(url, stream=True, headers=headers)
                response.raise_for_status()
                with open(xpt_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            except requests.exceptions.RequestException as e:
                print(f"  [ERROR] Error descargando {url}: {e}")
                continue
                
            if os.path.getsize(xpt_path) < 10000:
                with open(xpt_path, 'rb') as f:
                    if b'html' in f.read(500).lower():
                        os.remove(xpt_path)
                        continue
                
            try:
                df = pd.read_sas(xpt_path, format='xport')
                df.to_parquet(parquet_path, engine='pyarrow', index=False)
            except Exception as e:
                print(f"  [ERROR] Error convirtiendo {filename} a Parquet: {e}")
                
            if os.path.exists(xpt_path):
                os.remove(xpt_path)
                
    return "Ingesta completada"
