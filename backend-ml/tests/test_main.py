import pytest
from fastapi.testclient import TestClient
import sys
import os

# Asegurar que la ruta base esté en sys.path para importar main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

client = TestClient(app)

def test_health_check_no_model(monkeypatch):
    """
    Prueba el endpoint /health cuando el modelo no está cargado.
    Debería retornar un estado 'degraded'.
    """
    import main
    monkeypatch.setattr(main, "model_pipeline", None)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "message": "API corriendo pero modelo NO cargado"}

def test_predict_no_model(monkeypatch):
    """
    Prueba el endpoint /predict cuando el modelo no está disponible.
    Debería levantar una excepción 503.
    """
    import main
    monkeypatch.setattr(main, "model_pipeline", None)
    payload = {
        "ageYears": 45,
        "gender": "Masculino",
        "nutritionalQualityScore": 85.5
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 503
    assert response.json()["detail"] == "El modelo no está disponible."

def test_health_check_with_model(monkeypatch):
    """
    Prueba el endpoint /health cuando el modelo está operativo.
    """
    class DummyModel:
        def predict(self, df):
            return [25.5]
            
    import main
    monkeypatch.setattr(main, "model_pipeline", DummyModel())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "message": "API y Modelo ML operativos"}

def test_predict_with_model(monkeypatch):
    """
    Prueba el endpoint /predict enviando datos correctos de un paciente.
    Verifica que la respuesta calcule correctamente el riesgo y la longevidad.
    """
    class DummyModel:
        def predict(self, df):
            return [25.5] # Retorna un riesgo falso del 25.5%
            
    import main
    monkeypatch.setattr(main, "model_pipeline", DummyModel())
    payload = {
        "ageYears": 45,
        "gender": "Femenino",
        "nutritionalQualityScore": 85.5
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predictedCardioRiskScore" in data
    assert "healthyAgingProbability" in data
    assert data["predictedCardioRiskScore"] == 25.5
    assert data["healthyAgingProbability"] == 74.5

def test_predict_validation_error():
    """
    Prueba el endpoint /predict con datos faltantes.
    Debería retornar un código 422 de Unprocessable Entity (Validación fallida).
    """
    payload = {
        "ageYears": 45,
        "nutritionalQualityScore": 85.5
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
