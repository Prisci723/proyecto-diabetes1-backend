-- ============================================================================
-- Script para actualizar la restricción de glucosa de mg/dL a mmol/L
-- ============================================================================

-- Eliminar la restricción antigua que usa mg/dL (20-600)
ALTER TABLE glucose_readings DROP CONSTRAINT IF EXISTS chk_glucose_value;

-- Crear nueva restricción para mmol/L (2.0-25.0)
ALTER TABLE glucose_readings ADD CONSTRAINT chk_glucose_value CHECK (value >= 2.0 AND value <= 25.0);

-- Actualizar el comentario de la columna
COMMENT ON COLUMN glucose_readings.value IS 'Valor de glucosa en mmol/L (rango: 2.0-25.0)';

-- Verificar que la restricción se aplicó correctamente
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conname = 'chk_glucose_value';
