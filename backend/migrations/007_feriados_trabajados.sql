-- Novedad explícita para liquidar feriados nacionales trabajados.
ALTER TABLE novedad_mensual
    ADD COLUMN IF NOT EXISTS feriados_trabajados integer NOT NULL DEFAULT 0;

ALTER TABLE novedad_mensual
    DROP CONSTRAINT IF EXISTS ck_novedad_mensual_feriados_no_negativos;
ALTER TABLE novedad_mensual
    ADD CONSTRAINT ck_novedad_mensual_feriados_no_negativos
    CHECK (feriados_trabajados >= 0);
