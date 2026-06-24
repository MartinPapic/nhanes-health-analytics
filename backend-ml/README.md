# Longevity Predictive Model API (Backend ML)

Microservicio de Machine Learning desarrollado con FastAPI, encargado de predecir el Riesgo Cardiovascular y la Probabilidad de Envejecimiento Saludable de los pacientes del proyecto NHANES.

## Arquitectura

El microservicio está diseñado bajo los siguientes principios:
- **API RESTful**: Expuesta con FastAPI por su alto rendimiento y generación automática de documentación Swagger/OpenAPI.
- **AutoML**: El entrenamiento utiliza TPOT (optimización basada en algoritmos genéticos) para explorar el mejor pipeline posible (o un fallback a Random Forest).
- **Desacoplamiento**: Este servicio únicamente realiza inferencia sobre un modelo entrenado previamente, independiente del ETL principal.

## Instalación y Configuración (Local)

1. Crear un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux/Mac
   .\.venv\Scripts\activate   # En Windows
   ```
2. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar el servidor:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

La documentación Swagger estará disponible en: `http://localhost:8000/docs`.

## Entrenamiento del Modelo

Para generar o actualizar el modelo, asegúrate de que la base de datos PostgreSQL (Capa Gold) esté levantada, y ejecuta:
```bash
python train_automl.py
```
Esto generará el archivo `models/longevity_model.pkl` necesario para las predicciones.

## Endpoints

### `GET /health`
Verifica si el servicio está levantado y si el modelo `.pkl` ha sido cargado exitosamente en memoria.
- **Respuesta Exitosa**: `{"status": "healthy", "message": "API y Modelo ML operativos"}`
- **Respuesta Degradada**: `{"status": "degraded", ...}` (Si el modelo no se encuentra).

### `POST /predict`
Recibe los datos del paciente y devuelve la inferencia matemática.

**Request Payload:**
```json
{
  "ageYears": 45.0,
  "gender": "Femenino",
  "nutritionalQualityScore": 85.5
}
```

**Response Payload:**
```json
{
  "predictedCardioRiskScore": 12.5,
  "healthyAgingProbability": 87.5,
  "model_type": "AutoML_TPOT_Pipeline"
}
```

## Pruebas Unitarias (Testing)

El servicio cuenta con un suite de pruebas automatizadas construidas con `pytest` y `TestClient` de FastAPI. Las pruebas verifican respuestas exitosas, manejo de errores y validaciones de esquema de entrada.

Para ejecutar las pruebas:
```bash
pytest tests/ -v
```

## Despliegue (Docker)

Para correr el servicio de forma contenida en Docker:

1. Construir la imagen:
   ```bash
   docker build -t nhanes-backend-ml .
   ```
2. Correr el contenedor:
   ```bash
   docker run -d -p 8000:8000 nhanes-backend-ml
   ```
