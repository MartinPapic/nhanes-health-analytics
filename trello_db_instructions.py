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
    if not board_id: return

    lists = api_request("GET", f"/boards/{board_id}/lists", auth)
    progreso_list_id = next((l["id"] for l in lists if "En progreso" in l["name"] or "In Progress" in l["name"]), None)
    if not progreso_list_id: return

    descripcion = """**¡Hola equipo de Backend (Spring Boot)!** 

Ya está configurada la infraestructura de Base de Datos para conectar sus endpoints de Spring Boot con los datos científicos de Kedro.

### Instrucciones para levantar la Base de Datos Local:
1. Abran su terminal en la raíz del proyecto.
2. Ejecuten: `docker compose up -d`
3. ¡Listo! Docker descargará PostgreSQL y ejecutará nuestro script de inicialización de forma automática.

### Credenciales para el `application.properties` de Spring Boot:
* **URL:** `jdbc:postgresql://localhost:5432/nhanes_analytics`
* **Usuario:** `postgres`
* **Contraseña:** `admin`

### Estructura del Data Mart (Tabla Gold)
La tabla principal a la que deben mapear sus entidades JPA se llama `gold_analytics_master`. Ya está optimizada con índices para consultas rápidas del Frontend.
Tiene la llave primaria `seqn`, variables demográficas (`survey_cycle`, `age_years`, `gender`, `longevity_group`), y las columnas para los scores de salud que estamos desarrollando en Kedro (`healthy_aging_score`, etc).

Una vez que Kedro envíe los datos a esta tabla, ustedes solo deben construir los endpoints GET para que Next.js los consuma."""

    params = {
        **auth,
        "idList": progreso_list_id,
        "name": "[INFRAESTRUCTURA] Instrucciones de Conexión a Base de Datos",
        "desc": descripcion,
        "pos": "top"
    }
    
    result = api_request("POST", "/cards", params)
    if result:
        print("Instrucciones de Base de Datos publicadas con éxito en Trello.")

if __name__ == "__main__":
    main()
