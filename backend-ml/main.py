from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os
import logging
from fastapi.middleware.cors import CORSMiddleware

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NHANES Longevity Predictive Model API",
    description="Microservicio de ML para predecir el Riesgo Cardiovascular usando el mejor modelo de TPOT (AutoML).",
    version="1.0.0"
)

# CORS para que Next.js pueda consumir
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definir la estructura de entrada
class PredictionInput(BaseModel):
    ageYears: float
    gender: str
    nutritionalQualityScore: float
    bmi: float
    glucose: float

# Variable global para el modelo
model_pipeline = None

@app.on_event("startup")
def load_model():
    """
    Se ejecuta al iniciar la aplicación FastAPI.
    Intenta cargar el modelo serializado en memoria para que esté listo para las predicciones.
    """
    global model_pipeline
    model_path = "../kedro-pipeline/data/06_models/longevity_model.pkl"
    if os.path.exists(model_path):
        try:
            model_pipeline = joblib.load(model_path)
            logger.info("¡Modelo AutoML de Kedro cargado exitosamente en memoria!")
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {e}")
    else:
        logger.warning(f"¡Modelo no encontrado en {model_path}! Asegúrate de ejecutar el pipeline de Kedro primero.")

@app.get("/health")
def health_check():
    """
    Endpoint de salud para monitorear si la API está funcionando
    y si el modelo se ha cargado correctamente en memoria.
    """
    if model_pipeline is None:
        return {"status": "degraded", "message": "API corriendo pero modelo NO cargado"}
    return {"status": "healthy", "message": "API y Modelo ML operativos"}

@app.post("/predict")
def predict_cardio_risk(data: PredictionInput):
    """
    Recibe la información clínica del paciente 
    y retorna la predicción de Envejecimiento Saludable (Healthy Aging Score).
    """
    if model_pipeline is None:
        raise HTTPException(status_code=503, detail="El modelo no está disponible.")
    
    # Preprocesamiento
    gender_encoded = 1 if data.gender.lower() in ['hombre', 'masculino', 'm'] else 0
    
    # Crear dataframe para el modelo
    input_df = pd.DataFrame([{
        'age_years': data.ageYears,
        'gender_encoded': gender_encoded,
        'nutritional_quality_score': data.nutritionalQualityScore,
        'bmi': data.bmi,
        'glucose': data.glucose
    }])
    
    try:
        prediction = model_pipeline.predict(input_df)[0]
        
        # El modelo predice el Healthy Aging Score (0-100)
        healthy_score = min(100.0, max(0.0, float(prediction)))
        
        return {
            "healthyAgingScore": round(healthy_score, 1),
            "cardioRiskScore": round(100 - healthy_score, 1), # Se invierte para la UI si es necesario
            "model_type": "Kedro_AutoML_TPOT"
        }
    except Exception as e:
        logger.error(f"Error en la predicción: {e}")
        raise HTTPException(status_code=500, detail=f"Error en la inferencia: {str(e)}")

