# NHANES Health Analytics

Este proyecto es una plataforma full-stack para el análisis de longevidad basada en los datos de la encuesta NHANES. Integra tres fuentes de datos complejas mediante un robusto pipeline ETL en Kedro, las orquesta en una base de datos PostgreSQL, expone los datos vía una API en Java Spring Boot, y finaliza con un Dashboard frontend interactivo desarrollado en Next.js.

## 📖 Documentación Completa del Sistema

Para entender a profundidad cada capa del proyecto, consulta nuestra documentación técnica:

1. **[Arquitectura del Sistema](docs/architecture/architecture.md)**: Diagramas Mermaid del flujo de datos end-to-end.
2. **[Documentación de la API (Endpoints)](docs/api/endpoints.md)**: Especificación de la API RESTful de Spring Boot.
3. **[Guía de Despliegue Docker](docs/deployment/docker-guide.md)**: Instrucciones detalladas para levantar el proyecto con `docker-compose`.
4. **[Manual de Usuario del Dashboard](docs/user-manual/dashboard-guide.md)**: Guía sobre cómo interactuar con las visualizaciones y filtros para usuarios generales y clínicos.
5. **[Diccionario de Datos Miembro 1](docs/data-dictionary/member1-dictionary.md)**: Glosario de variables demográficas.
6. **[Diccionario de Datos Dieta](diccionario_dieta_claudio.md)**: Glosario de variables nutricionales.

## 🚀 Inicio Rápido (Quickstart)

Todo el proyecto está dockerizado para que con un solo comando se levanten todos los servicios y se interconecten correctamente.

### 1. Levantar los Servicios

Abre una terminal en la raíz de este proyecto y ejecuta:

```bash
docker compose up -d --build
```

Esto levantará:
- `nhanes_postgres`: La base de datos relacional (expuesta localmente en el puerto 5432).
- `nhanes_pgadmin`: Interfaz para la base de datos (expuesta en el puerto 5050).
- `nhanes_backend`: El servidor de Java Spring Boot (expuesto en el puerto 8081).
- `nhanes_frontend`: La interfaz de usuario Next.js (expuesta en el puerto 3000).

*(Consulta la [Guía de Despliegue](docs/deployment/docker-guide.md) para configuraciones avanzadas o uso de archivo `.env`).*

### 2. Ejecutar las Pruebas Unitarias

El pipeline analítico de Kedro cuenta con pruebas unitarias desarrolladas en `pytest`:

```bash
pytest tests/
```

### 3. Visualizar el Dashboard

Abre tu navegador de preferencia y visita:
👉 **[http://localhost:3000](http://localhost:3000)**

Si todo ha salido bien, verás el Dashboard interactivo mostrando los KPIs de salud, gráficos de Plotly y distribuciones por audiencias.