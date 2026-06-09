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
        with open(env_path, "r") as f:
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
    
    if not api_key or not token or api_key == "tu_api_key_aqui":
        print("ERROR: Por favor pega tus credenciales reales en el archivo .env primero.")
        return

    auth = {"key": api_key, "token": token}
    print("Conectando a Trello...")

    # 1. Obtener tableros
    boards = api_request("GET", "/members/me/boards", auth)
    board_id = next((b["id"] for b in boards if b["name"] == BOARD_NAME), None)
    
    if not board_id:
        print(f"No se encontró el tablero '{BOARD_NAME}'")
        return

    # 2. Obtener listas
    lists = api_request("GET", f"/boards/{board_id}/lists", auth)
    terminado_list_id = next((l["id"] for l in lists if "Terminado" in l["name"] or "Done" in l["name"]), None)
    progreso_list_id = next((l["id"] for l in lists if "En progreso" in l["name"] or "In Progress" in l["name"]), None)

    # 3. Obtener tarjetas
    cards = api_request("GET", f"/boards/{board_id}/cards", auth)
    
    # PM-01, PM-02, PM-04 son configuraciones iniciales únicas, esas sí están "Terminadas".
    terminado_prefixes = ["PM-01", "PM-02", "PM-04", "ETL-01"]
    
    # DATA y ETL son compartidas. Como el Miembro 2 y 3 deben aportar, van a "En progreso".
    progreso_prefixes = ["DATA-01", "DATA-02", "DATA-04", "ETL-02", "ETL-03"]
    
    for card in cards:
        name = card["name"]
        
        # Mover a Terminado
        if any(prefix in name for prefix in terminado_prefixes) and card["idList"] != terminado_list_id and terminado_list_id:
            params = {**auth, "idList": terminado_list_id}
            api_request("PUT", f"/cards/{card['id']}", params)
            print(f"[EXITO] Movida a Terminado: {name}")

        # Mover a En Progreso
        if any(prefix in name for prefix in progreso_prefixes) and card["idList"] != progreso_list_id and progreso_list_id:
            params = {**auth, "idList": progreso_list_id}
            api_request("PUT", f"/cards/{card['id']}", params)
            print(f"[PROGRESO] Movida a En Progreso (Esperando al resto del equipo): {name}")

        # Comentario Arquitectónico en DATA-04
        if "DATA-04" in name:
            comentario = """⚠️ **NUEVO ESTÁNDAR DE ARQUITECTURA KEDRO** ⚠️
@equipo: Para garantizar la mantenibilidad y no tener conflictos de código en Git, a partir de ahora **NO usaremos scripts sueltos**.
Toda la lógica de ingesta y limpieza debe programarse estrictamente como **Nodos de Kedro**.
Yo ya implementé la estructura base en `src/nhanes_pipeline/pipelines/`.
- La descarga va en `data_ingestion`.
- El cruce matemático va en carpetas modulares por miembro (ej. `data_processing_member1`).
¡Por favor, sigan este patrón para sus secciones de NHANES y actualicen sus tarjetas!"""
            
            # Verificamos que no hayamos publicado esto ya
            comments = api_request("GET", f"/cards/{card['id']}/actions", {**auth, "filter": "commentCard"})
            already_commented = any("NUEVO ESTÁNDAR" in c["data"]["text"] for c in comments)
            
            if not already_commented:
                params = {**auth, "text": comentario}
                api_request("POST", f"/cards/{card['id']}/actions/comments", params)
                print(f"[EXITO] Comentario publicado en: {name}")

    print("¡Sincronización con Trello finalizada con éxito!")

if __name__ == "__main__":
    main()
