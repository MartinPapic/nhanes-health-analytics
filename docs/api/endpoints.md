# Documentación de la API (Backend Spring Boot)

El backend expone datos analíticos procesados mediante una API RESTful desarrollada en Spring Boot. Esta API es consumida por el frontend Next.js para renderizar los dashboards interactivos.

## URL Base
El servicio corre por defecto en:
`http://localhost:8081`

---

## Endpoints

### 1. Obtener Datos Generales (Riesgo Cardiovascular y Nutricional)

Endpoint principal que retorna los datos integrados del Miembro 1 y Miembro 2, incluyendo el *Healthy Aging Score*, *Cardio Risk Score* y *Nutritional Quality Score*.

- **URL:** `/api/v1/analytics`
- **Método:** `GET`
- **Parámetros de Query (Paginación y Ordenamiento):**
  - `page` (opcional, default `0`): Número de página a solicitar.
  - `size` (opcional, default `20`): Cantidad de registros por página.
  - `sort` (opcional): Campo por el cual ordenar y dirección. (Ej: `surveyCycle,desc`).

#### Respuesta de Ejemplo (200 OK):
```json
{
  "content": [
    {
      "seqn": 83732,
      "surveyCycle": "2015-2016",
      "ageYears": 62,
      "gender": "Hombre",
      "longevityGroup": "Longevidad Base (<65)",
      "healthyAgingScore": 65.4,
      "cardioRiskScore": 52.1,
      "nutritionalQualityScore": 75.3
    }
  ],
  "pageable": {
    "sort": {
      "empty": false,
      "sorted": true,
      "unsorted": false
    },
    "offset": 0,
    "pageNumber": 0,
    "pageSize": 20,
    "unpaged": false,
    "paged": true
  },
  "last": false,
  "totalPages": 50,
  "totalElements": 1000,
  "size": 20,
  "number": 0,
  "first": true,
  "numberOfElements": 20,
  "empty": false
}
```

---

### 2. Obtener Datos Clínicos (Miembro 3 - Laboratorio y Acceso Limitado)

Retorna la data específica de laboratorio procesada por la pipeline del Miembro 3, incluyendo mediciones críticas como HbA1c y el Índice de Riesgo de Longevidad Clínica.

- **URL:** `/api/v1/analytics/member3`
- **Método:** `GET`

#### Respuesta de Ejemplo (200 OK):
```json
[
  {
    "seqn": 83733,
    "lbxgh": 5.8,
    "lbxtc": 195.0,
    "longevityRiskIndex": 12.4,
    "riskTier": "Low"
  },
  {
    "seqn": 83734,
    "lbxgh": 8.2,
    "lbxtc": 240.5,
    "longevityRiskIndex": 75.8,
    "riskTier": "Critical"
  }
]
```
