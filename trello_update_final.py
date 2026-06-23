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
    if not boards: return
    board_id = next((b["id"] for b in boards if b["name"] == BOARD_NAME), None)
    
    if not board_id:
        print("Tablero no encontrado")
        return

    cards = api_request("GET", f"/boards/{board_id}/cards", auth)

    frontend_comment = """**Actualización de Integración:**
Estructura del proyecto Next.js creada, Proxy con el backend solucionado, y tabla de datos en crudo (Capa Gold) ya renderizándose y paginando correctamente.

**Siguientes pasos para el equipo:**
Añadir librerías de gráficos (ej. Recharts o Chart.js) para crear visualizaciones (gráficos de barra, torta o dispersión) basadas en las edades y el 'Healthy Aging Score'."""

    backend_comment = """**Actualización de Integración:**
API RESTful en Spring Boot funcionando en el puerto 8081 con paginación (`/api/v1/analytics`). Base de datos PostgreSQL levantada y poblada con ~11,288 registros desde el archivo parquet a través de Python.

**Siguientes pasos para el equipo:**
Crear endpoints adicionales si se requieren filtros específicos por género o ciclo de encuesta, o aplicar seguridad avanzada si es necesario."""

    for card in cards:
        name = card["name"].lower()
        if "frontend" in name or "next" in name:
            params = {**auth, "text": frontend_comment}
            api_request("POST", f"/cards/{card['id']}/actions/comments", params)
            print(f"Comentado en Frontend: {card['name']}")
        
        if "gold" in name or "postgres" in name or "java" in name:
            params = {**auth, "text": backend_comment}
            api_request("POST", f"/cards/{card['id']}/actions/comments", params)
            print(f"Comentado en Backend/Gold: {card['name']}")

if __name__ == "__main__":
    main()
