import urllib.request
import urllib.parse
import json
import os

BOARD_NAME = "NHANES Longevity Analytics - SCY1101"
BASE_URL = "https://api.trello.com/1"

def load_env():
    env_path = ".env"
    creds = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    creds[key] = val.strip("\"'")
    return creds

def api_request(method, endpoint, params=None):
    if params:
        query = urllib.parse.urlencode(params)
        url = f"{BASE_URL}{endpoint}?{query}"
    else:
        url = f"{BASE_URL}{endpoint}"
        
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error {e.code} en {url}: {e.read().decode()}")
        return None

def main():
    creds = load_env()
    api_key = creds.get("TRELLO_API_KEY")
    token = creds.get("TRELLO_TOKEN")
    
    if not api_key or not token:
        print("Faltan credenciales en .env")
        return

    auth = {"key": api_key, "token": token}
    
    boards = api_request("GET", "/members/me/boards", auth)
    board_id = next((b["id"] for b in boards if b["name"] == BOARD_NAME), None)
    
    if not board_id:
        return

    lists = api_request("GET", f"/boards/{board_id}/lists", auth)
    progreso_list_id = next((l["id"] for l in lists if "En progreso" in l["name"] or "In Progress" in l["name"]), None)

    if not progreso_list_id:
        return

    descripcion = """**¡Hola equipo!** La rama `develop` acaba de ser actualizada con la arquitectura de la **Capa Gold**. Para que mantengamos el rigor científico y nuestro código pueda unirse al final, por favor sigan este estándar al construir su capa Gold:

### 1. Metodología de Imputación (Nulos)
En los cuestionarios de NHANES verán muchos valores nulos por el diseño de la encuesta (Skip Logic). 
**Nuestra regla como equipo es:** Si una variable médica de riesgo es nula (porque el paciente saltó la pregunta), asumimos que el riesgo es `0` (Ausencia de síntoma). No eliminen las filas con nulos, o perderemos demasiados datos.

### 2. Estándar Matemático (Frailty Index)
Para calcular sus propios scores en la Capa Gold, utilizaremos el modelo estándar del **Índice de Acumulación de Déficit** (Frailty Index). 
* **Regla:** Definan cuántas enfermedades evaluarán (ej. N=5). Por cada enfermedad presente, sumen 1 punto de "déficit" al paciente.
* **Cálculo Final:** Score de salud = `1.0 - (Déficits Acumulados / Total de variables evaluadas)`. 

### 3. Código Disponible
Pueden ir a `src/nhanes_pipeline/pipelines/data_science_member1/nodes.py` para ver exactamente cómo lo programé en Python usando NumPy (`np.where`). Copien ese estilo arquitectónico para sus propias ramas. 

¡Mucho éxito con sus algoritmos! Cuando terminen, uniremos todo en un Data Mart final."""

    params = {
        **auth,
        "idList": progreso_list_id,
        "name": "[ESTÁNDAR EQUIPO] Cómo programar la Capa Gold",
        "desc": descripcion,
        "pos": "top"
    }
    
    result = api_request("POST", "/cards", params)
    if result:
        print("Instrucciones de Capa Gold publicadas con éxito en Trello.")

if __name__ == "__main__":
    main()
