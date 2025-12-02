-- ============================================================================
-- Sistema de Monitoreo Glucémico - Script de Inicialización de Base de Datos
-- ============================================================================
-- Base de datos: PostgreSQL
-- Versión: 12+
-- Fecha: 2025-11-24
-- ============================================================================

-- Eliminar tablas existentes (en orden inverso por dependencias)
DROP TABLE IF EXISTS cluster_assignments CASCADE;
DROP TABLE IF EXISTS daily_metrics CASCADE;
DROP TABLE IF EXISTS glucose_readings CASCADE;
DROP TABLE IF EXISTS patients CASCADE;

-- Eliminar tipos enum si existen
DROP TYPE IF EXISTS diabetes_type_enum CASCADE;

-- ============================================================================
-- TIPOS PERSONALIZADOS
-- ============================================================================

-- Tipo enum para tipos de diabetes
CREATE TYPE diabetes_type_enum AS ENUM (
    'Type 1',
    'Type 2'
);

-- ============================================================================
-- TABLA: patients
-- ============================================================================
-- Almacena información básica de los pacientes con diabetes
-- ============================================================================

CREATE TABLE patients (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL CHECK (age > 0 AND age <= 120),
    diabetes_type diabetes_type_enum NOT NULL,
    diagnosis_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    current_cluster INTEGER,
    last_analysis_date TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_diagnosis_date CHECK (diagnosis_date <= CURRENT_TIMESTAMP),
    CONSTRAINT chk_cluster_range CHECK (current_cluster BETWEEN 0 AND 4)
);

-- Índices para patients
CREATE INDEX idx_patients_created_at ON patients(created_at);
CREATE INDEX idx_patients_current_cluster ON patients(current_cluster);
CREATE INDEX idx_patients_diabetes_type ON patients(diabetes_type);

-- Comentarios para patients
COMMENT ON TABLE patients IS 'Tabla principal de pacientes con diabetes';
COMMENT ON COLUMN patients.id IS 'Identificador único del paciente (ej: PAT001)';
COMMENT ON COLUMN patients.name IS 'Nombre completo del paciente';
COMMENT ON COLUMN patients.age IS 'Edad del paciente en años';
COMMENT ON COLUMN patients.diabetes_type IS 'Tipo de diabetes diagnosticada';
COMMENT ON COLUMN patients.diagnosis_date IS 'Fecha del diagnóstico inicial';
COMMENT ON COLUMN patients.current_cluster IS 'ID del cluster actual (0-4), asignado por ML';
COMMENT ON COLUMN patients.last_analysis_date IS 'Última fecha de análisis completo';

-- ============================================================================
-- TABLA: glucose_readings
-- ============================================================================
-- Almacena todas las lecturas de glucosa de los pacientes
-- ============================================================================

CREATE TABLE glucose_readings (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value FLOAT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_glucose_patient FOREIGN KEY (patient_id) 
        REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_glucose_value CHECK (value >= 20 AND value <= 600),
    CONSTRAINT chk_glucose_timestamp CHECK (timestamp <= CURRENT_TIMESTAMP + INTERVAL '1 hour')
);

-- Índices para glucose_readings
CREATE INDEX idx_glucose_patient_id ON glucose_readings(patient_id);
CREATE INDEX idx_glucose_timestamp ON glucose_readings(timestamp);
CREATE INDEX idx_glucose_patient_timestamp ON glucose_readings(patient_id, timestamp DESC);
CREATE INDEX idx_glucose_created_at ON glucose_readings(created_at);

-- Comentarios para glucose_readings
COMMENT ON TABLE glucose_readings IS 'Registro de todas las mediciones de glucosa';
COMMENT ON COLUMN glucose_readings.patient_id IS 'ID del paciente (FK a patients)';
COMMENT ON COLUMN glucose_readings.timestamp IS 'Momento exacto de la medición';
COMMENT ON COLUMN glucose_readings.value IS 'Valor de glucosa en mg/dL (rango: 20-600)';
COMMENT ON COLUMN glucose_readings.created_at IS 'Fecha de inserción en el sistema';

-- ============================================================================
-- TABLA: daily_metrics
-- ============================================================================
-- Almacena métricas calculadas diariamente para cada paciente
-- ============================================================================

CREATE TABLE daily_metrics (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    mean_glucose FLOAT NOT NULL,
    std_glucose FLOAT NOT NULL,
    cv FLOAT NOT NULL,
    tir FLOAT NOT NULL,
    tbr FLOAT NOT NULL,
    tbr_severe FLOAT NOT NULL,
    tar FLOAT NOT NULL,
    tar_severe FLOAT NOT NULL,
    gmi FLOAT NOT NULL,
    glucose_range FLOAT NOT NULL,
    n_readings INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_metrics_patient FOREIGN KEY (patient_id) 
        REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_mean_glucose CHECK (mean_glucose > 0),
    CONSTRAINT chk_std_glucose CHECK (std_glucose >= 0),
    CONSTRAINT chk_cv CHECK (cv >= 0),
    CONSTRAINT chk_tir CHECK (tir >= 0 AND tir <= 100),
    CONSTRAINT chk_tbr CHECK (tbr >= 0 AND tbr <= 100),
    CONSTRAINT chk_tbr_severe CHECK (tbr_severe >= 0 AND tbr_severe <= 100),
    CONSTRAINT chk_tar CHECK (tar >= 0 AND tar <= 100),
    CONSTRAINT chk_tar_severe CHECK (tar_severe >= 0 AND tar_severe <= 100),
    CONSTRAINT chk_gmi CHECK (gmi >= 0),
    CONSTRAINT chk_glucose_range CHECK (glucose_range >= 0),
    CONSTRAINT chk_n_readings CHECK (n_readings >= 10),
    CONSTRAINT uq_patient_date UNIQUE (patient_id, date)
);

-- Índices para daily_metrics
CREATE INDEX idx_metrics_patient_id ON daily_metrics(patient_id);
CREATE INDEX idx_metrics_date ON daily_metrics(date DESC);
CREATE INDEX idx_metrics_patient_date ON daily_metrics(patient_id, date DESC);
CREATE INDEX idx_metrics_created_at ON daily_metrics(created_at);

-- Comentarios para daily_metrics
COMMENT ON TABLE daily_metrics IS 'Métricas glucémicas calculadas por día';
COMMENT ON COLUMN daily_metrics.patient_id IS 'ID del paciente (FK a patients)';
COMMENT ON COLUMN daily_metrics.date IS 'Fecha del día analizado';
COMMENT ON COLUMN daily_metrics.mean_glucose IS 'Media de glucosa del día (mg/dL)';
COMMENT ON COLUMN daily_metrics.std_glucose IS 'Desviación estándar de glucosa';
COMMENT ON COLUMN daily_metrics.cv IS 'Coeficiente de variación (%)';
COMMENT ON COLUMN daily_metrics.tir IS 'Time In Range - Tiempo en rango 70-180 mg/dL (%)';
COMMENT ON COLUMN daily_metrics.tbr IS 'Time Below Range - Tiempo bajo 70 mg/dL (%)';
COMMENT ON COLUMN daily_metrics.tbr_severe IS 'TBR severo - Tiempo bajo 54 mg/dL (%)';
COMMENT ON COLUMN daily_metrics.tar IS 'Time Above Range - Tiempo sobre 180 mg/dL (%)';
COMMENT ON COLUMN daily_metrics.tar_severe IS 'TAR severo - Tiempo sobre 250 mg/dL (%)';
COMMENT ON COLUMN daily_metrics.gmi IS 'Glucose Management Indicator - Estimación de HbA1c (%)';
COMMENT ON COLUMN daily_metrics.glucose_range IS 'Rango de glucosa (max - min)';
COMMENT ON COLUMN daily_metrics.n_readings IS 'Número de lecturas del día (mínimo 10)';

-- ============================================================================
-- TABLA: cluster_assignments
-- ============================================================================
-- Historial de asignaciones de clusters por Machine Learning
-- ============================================================================

CREATE TABLE cluster_assignments (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    cluster_id INTEGER NOT NULL,
    cluster_name VARCHAR(100) NOT NULL,
    confidence_score FLOAT NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    avg_tir FLOAT NOT NULL,
    avg_cv FLOAT NOT NULL,
    avg_gmi FLOAT NOT NULL,
    
    -- Foreign Keys
    CONSTRAINT fk_cluster_patient FOREIGN KEY (patient_id) 
        REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_cluster_id CHECK (cluster_id BETWEEN 0 AND 4),
    CONSTRAINT chk_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT chk_avg_tir CHECK (avg_tir >= 0 AND avg_tir <= 100),
    CONSTRAINT chk_avg_cv CHECK (avg_cv >= 0),
    CONSTRAINT chk_avg_gmi CHECK (avg_gmi >= 0)
);

-- Índices para cluster_assignments
CREATE INDEX idx_cluster_patient_id ON cluster_assignments(patient_id);
CREATE INDEX idx_cluster_assigned_at ON cluster_assignments(assigned_at DESC);
CREATE INDEX idx_cluster_patient_assigned ON cluster_assignments(patient_id, assigned_at DESC);
CREATE INDEX idx_cluster_id ON cluster_assignments(cluster_id);


-- ============================================================================
-- DATOS DE REFERENCIA
-- ============================================================================

-- Tabla de referencia para clusters (opcional, para documentación)
CREATE TABLE IF NOT EXISTS cluster_reference (
    cluster_id INTEGER PRIMARY KEY,
    cluster_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    tir_min FLOAT,
    tir_max FLOAT,
    cv_min FLOAT,
    cv_max FLOAT
);

INSERT INTO cluster_reference (cluster_id, cluster_name, description, tir_min, tir_max, cv_min, cv_max) VALUES
(0, 'Control Excelente', 'Pacientes con excelente control: TIR >70%, CV <36%, mínima hipoglucemia', 70, 100, 0, 36),
(1, 'Control Moderado', 'Pacientes con control moderado: TIR 50-70%, espacio para optimización', 50, 70, 0, 40),
(2, 'Alta Variabilidad', 'Pacientes con alta variabilidad: CV >40%, requieren ajuste de tratamiento', 0, 100, 40, 100),
(3, 'Riesgo Hipoglucemia', 'Pacientes con riesgo de hipoglucemia: TBR >4%, prioridad reducir insulina', 0, 100, 0, 100),
(4, 'Control Subóptimo', 'Pacientes con control subóptimo: TIR <50%, requieren revisión completa', 0, 50, 0, 100);

COMMENT ON TABLE cluster_reference IS 'Referencia de definición de clusters';

