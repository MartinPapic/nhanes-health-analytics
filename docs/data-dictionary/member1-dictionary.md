# Diccionario de Datos - Miembro 1 (Demographics & Questionnaire)

Este documento contiene la descripción de las 12 fuentes de datos principales extraídas de NHANES (Ciclos 2015-2016 y 2017-2018) para el análisis de longevidad.

## 1. Demografía
*   **`DEMO` (Demographics Data):** Contiene las variables base de todos los participantes.
    *   `SEQN`: Número de secuencia del participante (Llave primaria para hacer Join con todo el resto).
    *   `RIDAGEYR`: Edad en años.
    *   `RIAGENDR`: Género (1 = Masculino, 2 = Femenino).
    *   `INDFMPIR`: Ratio de ingresos familiares respecto al nivel de pobreza.
    *   `DMDEDUC2`: Nivel educacional (Adultos 20+).

## 2. Enfermedades Crónicas (Questionnaire)
*   **`MCQ` (Medical Conditions):** Diagnósticos previos por un doctor.
    *   `MCQ160A`: Artritis.
    *   `MCQ220`: Cáncer o tumor maligno.
    *   `MCQ160L`: Problemas al hígado.
*   **`DIQ` (Diabetes):**
    *   `DIQ010`: Un doctor le ha dicho que tiene diabetes.
    *   `DIQ050`: Está tomando insulina.
*   **`BPQ` (Blood Pressure & Cholesterol):**
    *   `BPQ020`: Hipertensión.
    *   `BPQ080`: Colesterol alto.
*   **`CDQ` (Cardiovascular Disease):**
    *   `CDQ001`: Dolor en el pecho al caminar en pendiente o rápido.
    *   `CDQ010`: Dolor severo en el pecho durante más de media hora.

## 3. Hábitos de Vida (Questionnaire)
*   **`SMQ` (Smoking - Cigarette Use):**
    *   `SMQ020`: Ha fumado al menos 100 cigarros en su vida.
    *   `SMQ040`: Fuma actualmente.
*   **`ALQ` (Alcohol Use):**
    *   `ALQ130`: Promedio de tragos alcohólicos al día (los días que bebe).
    *   `ALQ151`: Frecuencia en que bebe 4/5 tragos al día.
*   **`PAQ` (Physical Activity):**
    *   `PAQ605`: Realiza actividad física vigorosa en el trabajo.
    *   `PAQ650`: Realiza actividad física vigorosa recreacional.
*   **`SLQ` (Sleep Disorders):**
    *   `SLD012`: Horas de sueño por noche (días de semana).
    *   `SLQ050`: Alguna vez le han dicho a un doctor sobre problemas para dormir.
*   **`WHQ` (Weight History):**
    *   `WHD020`: Peso actual autopercibido.
    *   `WHQ070`: Ha intentado perder peso en el último año.

## 4. Salud Mental y Funcionalidad
*   **`DPQ` (Mental Health - Depression Screener):** Basado en el cuestionario PHQ-9.
    *   `DPQ010`: Frecuencia en que se siente sin interés o placer al hacer cosas (últimas 2 semanas).
    *   `DPQ020`: Frecuencia en que se siente deprimido o desesperanzado.
*   **`PFQ` (Physical Functioning):**
    *   `PFQ061B`: Dificultad para caminar un cuarto de milla.
    *   `PFQ061C`: Dificultad para subir 10 escalones sin descansar.
