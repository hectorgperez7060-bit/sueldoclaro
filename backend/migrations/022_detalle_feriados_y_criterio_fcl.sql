-- Detalle auditable UOCRA dentro de la novedad mensual existente.
BEGIN;

ALTER TABLE public.novedad_mensual
  ADD COLUMN IF NOT EXISTS feriados_uocra_detalle jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS fcl_criterio_aniversario varchar(24),
  ADD COLUMN IF NOT EXISTS fcl_aprobado_por varchar(200),
  ADD COLUMN IF NOT EXISTS fcl_fundamento text;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_novedad_feriados_uocra_json') THEN
    ALTER TABLE public.novedad_mensual ADD CONSTRAINT ck_novedad_feriados_uocra_json
      CHECK (jsonb_typeof(feriados_uocra_detalle)='array');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_novedad_fcl_criterio') THEN
    ALTER TABLE public.novedad_mensual ADD CONSTRAINT ck_novedad_fcl_criterio
      CHECK (fcl_criterio_aniversario IS NULL OR fcl_criterio_aniversario IN
        ('MES_COMPLETO_12','MES_COMPLETO_8','PRORRATEO_DIAS'));
  END IF;
END $$;

COMMIT;
