-- Datos quincenales necesarios para personal jornalizado UOCRA.
-- Son parte de la novedad mensual existente y conservan su RLS/auditoría.
BEGIN;

ALTER TABLE public.novedad_mensual
  ADD COLUMN IF NOT EXISTS horas_normales_q1 numeric(8,2),
  ADD COLUMN IF NOT EXISTS horas_normales_q2 numeric(8,2),
  ADD COLUMN IF NOT EXISTS asistencia_perfecta_q1 boolean,
  ADD COLUMN IF NOT EXISTS asistencia_perfecta_q2 boolean,
  ADD COLUMN IF NOT EXISTS feriados_habilitados_q1 integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS feriados_habilitados_q2 integer NOT NULL DEFAULT 0;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_novedad_horas_quincenales') THEN
    ALTER TABLE public.novedad_mensual ADD CONSTRAINT ck_novedad_horas_quincenales
      CHECK (
        (horas_normales_q1 IS NULL OR horas_normales_q1 BETWEEN 0 AND 200)
        AND (horas_normales_q2 IS NULL OR horas_normales_q2 BETWEEN 0 AND 200)
      );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_novedad_feriados_habilitados') THEN
    ALTER TABLE public.novedad_mensual ADD CONSTRAINT ck_novedad_feriados_habilitados
      CHECK (
        feriados_habilitados_q1 >= 0 AND feriados_habilitados_q2 >= 0
        AND feriados_habilitados_q1 + feriados_habilitados_q2 <= feriados_no_trabajados
      );
  END IF;
END $$;

COMMIT;
