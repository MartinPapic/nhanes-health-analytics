# Guía de Despliegue con Docker

Este proyecto ha sido dockerizado para facilitar su orquestación local y asegurar que todos los servicios (Base de datos, Backend y Frontend) levanten con las configuraciones correctas de manera unificada.

## Requisitos Previos
- Docker instalado en la máquina (`Docker Desktop` en Windows/Mac, o Docker Engine en Linux).
- Docker Compose.

## Pasos para Despliegue Local (End-to-End)

El repositorio cuenta con un archivo `docker-compose.yml` en la raíz, configurado con las imágenes de base de datos y los `Dockerfile` del backend (Spring Boot) y frontend (Next.js).

### 1. Variables de Entorno (Opcional)
Por defecto, el archivo `docker-compose.yml` utiliza variables por defecto seguras para desarrollo local (ej: `nhanes2024` para la base de datos). Si deseas sobreescribirlas, puedes crear un archivo `.env` en la raíz del proyecto. **Nota:** El archivo `.env` está en el `.gitignore` por razones de seguridad.

Ejemplo de `.env`:
```env
POSTGRES_USER=mi_usuario_secreto
POSTGRES_PASSWORD=mi_password_secreto
POSTGRES_DB=nhanes
```

### 2. Construir y Levantar los Servicios

Abre una terminal en la raíz del repositorio (`nhanes-health-analytics`) y ejecuta:

```bash
docker compose up -d --build
```

El parámetro `-d` levanta los contenedores en modo "detached" (en segundo plano) y `--build` fuerza la reconstrucción de las imágenes del backend y frontend asegurando que incluyan tus últimos cambios en el código local.

### 3. Verificar que los servicios estén arriba

Puedes verificar el estado de los contenedores ejecutando:

```bash
docker compose ps
```

Deberías ver los siguientes servicios corriendo:
- `nhanes_postgres` (PostgreSQL en puerto `5432`)
- `nhanes_pgadmin` (PgAdmin en puerto `5050`)
- `nhanes_backend` (Spring Boot API en puerto `8081`)
- `nhanes_frontend` (Next.js App en puerto `3000`)

### 4. Acceso a las Aplicaciones
Una vez levantado todo el stack:
- **Dashboard Principal:** Abre en tu navegador [http://localhost:3000](http://localhost:3000)
- **API REST Backend:** Puedes comprobar su estado en [http://localhost:8081/api/v1/analytics](http://localhost:8081/api/v1/analytics)
- **Base de Datos (PgAdmin):** [http://localhost:5050](http://localhost:5050)

### 5. Detener los servicios

Para detener y borrar los contenedores (conservando los datos de Postgres en un volumen local persistente):

```bash
docker compose down
```

Para detener, borrar los contenedores y **destruir la base de datos** (eliminar el volumen):

```bash
docker compose down -v
```
