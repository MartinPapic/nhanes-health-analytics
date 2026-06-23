# Diccionario de Datos - NHANES (Dieta y Exámenes Físicos)
**Autor:** Claudio (Member 2)
**Descripción:** Este documento describe las variables extraídas de los datasets crudos del CDC (NHANES) y las variables de ingeniería (features) creadas en la Capa Gold.

## 1. Variables Crudas Extraídas (Capa Bronze/Silver)
| Variable Original | Archivo CDC | Descripción | Tipo de Dato |
|-------------------|-------------|-------------|--------------|
| `SEQN`            | Todos       | Número de secuencia del encuestado (ID Único). | Integer |
| `DR1TKCAL`        | DR1TOT      | Día 1: Ingesta total de energía (Kcal). | Float |
| `DR1TPROT`        | DR1TOT      | Día 1: Ingesta total de proteínas (gramos). | Float |
| `DR1TCARB`        | DR1TOT      | Día 1: Ingesta total de carbohidratos (gramos). | Float |
| `DR1TTFAT`        | DR1TOT      | Día 1: Ingesta total de grasas (gramos). | Float |
| `BMXWT`           | BMX         | Peso corporal (Kg). | Float |
| `BMXHT`           | BMX         | Altura (cm). | Float |
| `BMXBMI`          | BMX         | Índice de Masa Corporal (Kg/m2). | Float |
| `BPXSY1`          | BPX         | Lectura de Presión Arterial Sistólica 1 (mmHg). | Float |
| `BPXDI1`          | BPX         | Lectura de Presión Arterial Diastólica 1 (mmHg). | Float |

## 2. Variables Calculadas y Limpiadas (Capa Gold)
| Variable Creada | Origen | Descripción | Tipo de Dato | Reglas de Nulos |
|-----------------|--------|-------------|--------------|-----------------|
| `AVG_KCAL`      | Dieta  | Promedio de calorías consumidas entre el Día 1 y Día 2. | Float | Si falta, imputado por la mediana poblacional. |
| `AVG_PROT`      | Dieta  | Promedio de proteínas consumidas (Día 1 y 2). | Float | Imputado por la mediana. |
| `BMI_CATEGORY`  | BMX    | Categorización del BMI: 'Bajo peso', 'Normal', 'Sobrepeso', 'Obesidad'. | String | Registros sin BMI son extraídos al reporte de rechazados. |

## 3. Reglas de Calidad y Rechazo
* Los registros que no poseen lectura de Presión Arterial o Índice de Masa Corporal son considerados **inválidos** para el cálculo de longevidad.
* Estos registros son separados por el pipeline de Kedro y exportados a `data/08_reporting/member2_rejected_records.csv` para auditoría.
