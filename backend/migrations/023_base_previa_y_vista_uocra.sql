-- Base auditable para la contribución empresaria UOCRA del 2%.
BEGIN;

ALTER TABLE public.novedad_mensual
  ADD COLUMN IF NOT EXISTS base_contribucion_uocra_mes_anterior numeric(14,2);

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname='ck_novedad_base_uocra_anterior_no_negativa'
  ) THEN
    ALTER TABLE public.novedad_mensual
      ADD CONSTRAINT ck_novedad_base_uocra_anterior_no_negativa
      CHECK (
        base_contribucion_uocra_mes_anterior IS NULL
        OR base_contribucion_uocra_mes_anterior >= 0
      );
  END IF;
END $$;

COMMIT;
