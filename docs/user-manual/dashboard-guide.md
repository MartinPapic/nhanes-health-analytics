# Manual de Usuario del Dashboard NHANES

El dashboard "NHANES Longevity Dashboard" está diseñado para ofrecer una vista integral y analítica de los datos de salud poblacional recolectados por la encuesta NHANES. Su objetivo es comunicar métricas claves de manera visualmente clara, para dos tipos principales de audiencias: perfil público general / ejecutivo, y perfil clínico especializado.

## Acceso
Una vez desplegada la aplicación, accede al dashboard abriendo un navegador web moderno en la dirección:
`http://localhost:3000`

---

## 1. Barra de Filtros Global (Header)
En la parte superior de la página, encontrarás un panel de filtros que impacta todos los gráficos y KPIs en pantalla. Al interactuar con ellos, la información se recalcula instantáneamente.
- **Ciclo:** Filtra los datos según la ola de la encuesta (ej. 2015-2016, 2017-2018).
- **Grupo Longevidad:** Permite ver la población agrupada por rangos (Base <65, Alta 65-79, Extrema 80+).
- **Género:** Segmenta por sexo biológico (Hombre / Mujer).
- **Rango de Edad:** Control deslizante doble para delimitar el análisis a un margen etario específico (0 a 120 años).

---

## 2. Sección Clínica y de Laboratorio (Miembro 3)
Inmediatamente debajo del título, encontrarás un cuadro destacado llamado **"Análisis Clínico y de Longevidad"**. Este módulo está pensado específicamente para profesionales médicos:
- **KPIs Clínicos:** Muestra promedios poblacionales críticos como Índice de Riesgo, HbA1c y Colesterol Total.
- **Distribución de Categorías de Riesgo:** Gráfico de barras indicando cuántos pacientes clasifican como "Low", "Moderate", "High" o "Critical" en base a marcadores biológicos reales.
- **Gráfico HbA1c vs Riesgo:** Un gráfico de dispersión (scatter) que revela la correlación existente entre los niveles de glucosa (Hemoglobina Glicosilada) y el riesgo de deterioro o muerte prematura.

---

## 3. Navegación por Pestañas (Público General/Ejecutivo)
Debajo del análisis clínico se encuentran las métricas más genéricas organizadas por pestañas:

### Pestaña "Resumen"
Orientada a la visualización ejecutiva:
- **KPIs Superiores:** Tarjetas con el total de pacientes filtrados, riesgos promedio y conteo de pacientes "críticos".
- **Scatter (Nutrición vs Riesgo Cardio):** Permite ver a simple vista cómo la calidad nutricional afecta el riesgo cardíaco de los encuestados. En **rojo** se resaltan los pacientes críticos (riesgo cardio > 80 y nutrición < 40).
- **Evolución por Ciclo:** Gráfico de barras que compara los puntajes promedio históricos a través del tiempo.
- **Distribución Demográfica:** Gráficos de anillo mostrando proporciones por género y rangos de longevidad.

### Pestaña "Análisis"
Contiene vistas estadísticas para un entendimiento más profundo de los segmentos:
- **Histograma de Edades:** Muestra la pirámide poblacional en los filtros seleccionados, coloreada por el "Grupo de Longevidad".
- **Box Plot (Riesgo Cardio):** Diagrama de cajas que expone estadísticos (mediana, rango intercuartil y casos atípicos) del riesgo de salud según la edad del paciente.
- **Distribución de Calidad Nutricional:** Histograma general de toda la población filtrada respecto a sus hábitos alimenticios.

### Pestaña "Tabla"
Provee acceso directo a los registros individuales:
- Se muestra la data cruda y paginada (20 pacientes por vista).
- Útil para identificar **SEQN** (identificadores de pacientes) particulares, especialmente los marcados en rojo (críticos).
- **Botón "Exportar CSV":** Permite descargar la data actual (con filtros aplicados) a un archivo `.csv` para análisis externo en Excel, R o Python.
