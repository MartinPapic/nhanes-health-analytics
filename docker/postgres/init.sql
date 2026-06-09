-- Inicialización de la Base de Datos para NHANES Health Analytics
-- Este script se ejecutará automáticamente la primera vez que se levante el contenedor Docker.

-- ==============================================================================
-- CAPA GOLD: DATA MART PRINCIPAL
-- ==============================================================================
-- Esta tabla está diseñada (desnormalizada) para ser leída a máxima velocidad
-- por el Frontend (Next.js) a través de los endpoints de Spring Boot.

CREATE TABLE IF NOT EXISTS gold_analytics_master (
    seqn INTEGER PRIMARY KEY,
    
    -- Metadatos y Demografía (Aportados por el Pipeline de Ingreso / Member 1)
    survey_cycle VARCHAR(20) NOT NULL,
    age_years INTEGER,
    gender VARCHAR(20),
    longevity_group VARCHAR(50),
    
    -- Métricas Analíticas (Puntajes de 0 a 100)
    -- Generado por el pipeline 'data_science_member1'
    healthy_aging_score NUMERIC(5, 2),
    
    -- Reservados para pipelines de los otros miembros del equipo
    cardio_risk_score NUMERIC(5, 2),
    nutritional_quality_score NUMERIC(5, 2),
    
    -- Tiempos de actualización
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas rápidas en el Dashboard Frontend
CREATE INDEX idx_gold_longevity ON gold_analytics_master(longevity_group);
CREATE INDEX idx_gold_cycle ON gold_analytics_master(survey_cycle);

-- ==============================================================================
-- TABLAS DE DICCIONARIO (OPCIONALES PARA EL FRONTEND)
-- ==============================================================================
-- Tabla auxiliar para que el backend sepa interpretar los grupos

CREATE TABLE IF NOT EXISTS dicc_longevity_groups (
    group_name VARCHAR(50) PRIMARY KEY,
    description TEXT,
    risk_level INTEGER
);

INSERT INTO dicc_longevity_groups (group_name, description, risk_level) VALUES
('Longevidad Base (<65)', 'Adultos jóvenes y de mediana edad', 1),
('Longevidad Alta (65-79)', 'Adultos mayores', 2),
('Longevidad Extrema (80+)', 'Población anciana con top-coding de privacidad', 3)
ON CONFLICT (group_name) DO NOTHING;
