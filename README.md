# NHANES Health Analytics

Este proyecto es una plataforma full-stack para el análisis de longevidad basada en los datos de la encuesta NHANES. Está compuesto por una base de datos PostgreSQL, una API en Java Spring Boot, y un Dashboard frontend interactivo desarrollado en Next.js.

## Arquitectura del Proyecto

1. **Base de Datos (PostgreSQL):** Almacena la "Capa Gold" de datos procesados, específicamente la tabla `gold_analytics_master` que contiene los cálculos de "Healthy Aging Score".
2. **Backend (Java Spring Boot 3):** Expone un endpoint de tipo REST (`/api/v1/analytics`) utilizando Spring Data JPA para paginar y entregar los datos al frontend eficientemente.
3. **Frontend (Next.js 14):** Una aplicación React del lado del cliente que consume la API y muestra una tabla interactiva de los resultados. Utiliza un Proxy Rewrite para evitar problemas de CORS y puertos.

## Requisitos Previos

Para lanzar todo el proyecto solo necesitas:
- **Docker** y **Docker Compose** instalados en tu computadora.
- Opcionalmente: **Python 3.x** y la librería `pandas`, `pyarrow` y `psycopg2` si deseas recargar los datos manualmente.

## Cómo Lanzar el Proyecto (Instrucciones)

Todo el proyecto está dockerizado para que con un solo comando se levanten todos los servicios y se interconecten correctamente en una red virtual de Docker.

### 1. Levantar los Servicios

Abre una terminal en la raíz de este proyecto (donde se encuentra `docker-compose.yml`) y ejecuta:

```bash
docker-compose up -d --build
```

Esto levantará 3 contenedores:
- `nhanes_postgres`: La base de datos relacional (expuesta localmente en el puerto 5434).
- `nhanes_backend`: El servidor de Java Spring Boot (expuesto internamente y en el puerto 8081).
- `nhanes_frontend`: La interfaz de usuario Next.js (expuesta en el puerto 3000).

### 2. Cargar los Datos (Capa Gold)

El backend ya está conectado a la base de datos, pero la tabla estará vacía inicialmente. Para cargar los datos procesados (el archivo parquet), ejecuta el script de Python:

```bash
python load_to_postgres.py
```
*Nota: Este script leerá el archivo `member1_gold.parquet` de la carpeta `data-lake/gold/` y lo insertará en PostgreSQL (aproximadamente 11,288 registros).*

### 3. Visualizar el Dashboard

Abre tu navegador de preferencia y visita:
👉 **[http://localhost:3000](http://localhost:3000)**

Si todo ha salido bien, verás el Dashboard con los datos crudos y paginados de la Capa Gold.

## Próximos Pasos (Para el Equipo)

- **Frontend:** Añadir gráficos interactivos (Recharts, Chart.js) para visualizar distribuciones de edades y puntuaciones de envejecimiento saludable.
- **Data Engineering:** Desarrollar las tuberías (Pipelines) de Kedro para procesar la Capa Silver a partir de los datos brutos.
- **Machine Learning:** Conectar Databricks o Jupyter Notebooks para empezar a crear modelos predictivos que consuman esta misma base de datos.