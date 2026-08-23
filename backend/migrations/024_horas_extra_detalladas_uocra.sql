-- Detalle horario auditable para clasificar recargos UOCRA sin inferencias.
BEGIN;

ALTER TABLE public.novedad_mensual
  ADD COLUMN IF NOT EXISTS horas_extra_uocra_detalle jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS horas_extra_uocra_acumuladas_anio numeric(8,2) NOT NULL DEFAULT 0;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_novedad_he_uocra_json') THEN
    ALTER TABLE public.novedad_mensual ADD CONSTRAINT ck_novedad_he_uocra_json
      CHECK (jsonb_typeof(horas_extra_uocra_detalle)='array');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_novedad_he_uocra_anio') THEN
    ALTER TABLE public.novedad_mensual ADD CONSTRAINT ck_novedad_he_uocra_anio
      CHECK (horas_extra_uocra_acumuladas_anio >= 0 AND horas_extra_uocra_acumuladas_anio <= 200);
  END IF;
END $$;

COMMIT;
