FROM eclipse-temurin:17-jdk-alpine AS builder

WORKDIR /app

# Copiar el wrapper y dependencias para aprovechar la caché de Docker
COPY .mvn/ .mvn
COPY mvnw pom.xml ./
# Dar permisos de ejecución al wrapper y arreglar finales de línea (CRLF a LF en Windows)
RUN sed -i 's/\r$//' mvnw && chmod +x ./mvnw
# Copiar el código fuente y compilar
COPY src ./src
RUN ./mvnw clean package -DskipTests

# Imagen de producción
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app
COPY --from=builder /app/target/health-analytics-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
