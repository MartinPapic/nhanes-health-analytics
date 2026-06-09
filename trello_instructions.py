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
    
    # 1. Obtener tableros
    boards = api_request("GET", "/members/me/boards", auth)
    board_id = next((b["id"] for b in boards if b["name"] == BOARD_NAME), None)
    
    if not board_id:
        print("Tablero no encontrado.")
        return

    # 2. Obtener lista "En progreso"
    lists = api_request("GET", f"/boards/{board_id}/lists", auth)
    progreso_list_id = next((l["id"] for l in lists if "En progreso" in l["name"] or "In Progress" in l["name"]), None)

    if not progreso_list_id:
        print("Lista 'En progreso' no encontrada.")
        return

    # Instrucciones Claras
    descripcion = """**Hola equipo!** La arquitectura base de Kedro ya está implementada y alojada en la rama `develop`. Para que no nos pisemos el código, por favor sigan estrictamente estos pasos:

### 1. Preparar el repositorio local
Abran la terminal y asegúrense de traer lo último:
`git checkout develop`
`git pull origin develop`

### 2. Crear su propia rama
NUNCA programen directamente en develop. Creen su rama:
Claudio: `git checkout -b feat/claudio-data`
Matías: `git checkout -b feat/matias-data`

### 3. Activar Kedro
Entren a la carpeta de kedro y activen el ambiente:
`cd kedro-pipeline`
`.\\.venv\\Scripts\\activate` (en Windows) o `source .venv/bin/activate` (en Mac/Linux)
`pip install -r requirements.txt`

### 4. Dónde poner el código de Descarga (Ingesta)
NO CREEN SCRIPTS SUELTOS. Abran el archivo:
`src/nhanes_pipeline/pipelines/data_ingestion/nodes.py`
Ahí verán la función `download_nhanes_files`. Simplemente agreguen las URLs de los archivos XPT que les tocó procesar a ustedes dentro de la lista que ya existe. Yo (Martín) ya puse las mías de Demografía y Cuestionarios.

### 5. Dónde poner el código de Cruce y Limpieza
Dentro de `src/nhanes_pipeline/pipelines/` verán la carpeta `data_processing_member1`. 
1. Dupliquen o imiten esa estructura para crear `data_processing_member2` (Claudio) y `data_processing_member3` (Matías).
2. Escriban su lógica de limpieza en sus respectivos `nodes.py`.
3. Registren su pipeline en `src/nhanes_pipeline/pipeline_registry.py`.

### 6. Ejecutar todo
Cuando terminen, prueben su código corriendo el comando mágico desde la carpeta kedro-pipeline:
`kedro run`

Si corre sin errores, hagan *Commit*, *Push* de su rama a GitHub, y avisen para fusionarlo a `develop`."""

    # 3. Crear Tarjeta
    params = {
        **auth,
        "idList": progreso_list_id,
        "name": "[URGENTE] INSTRUCCIONES PARA EL EQUIPO: CÓMO USAR KEDRO",
        "desc": descripcion,
        "pos": "top" # Ponerla arriba de todo
    }
    
    result = api_request("POST", "/cards", params)
    if result:
        print("Instrucciones publicadas con éxito como una nueva tarjeta en Trello.")

if __name__ == "__main__":
    main()
