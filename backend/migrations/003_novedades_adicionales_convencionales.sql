-- Farmacia 414/05: selección auditable de adicionales convencionales.
-- Preparada para revisión. NO ejecutada en Supabase.

BEGIN;

ALTER TABLE public.novedad_mensual
  ADD COLUMN IF NOT EXISTS adicionales_convencionales jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS cantidades_adicionales jsonb NOT NULL DEFAULT '{}'::jsonb;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_novedad_adicionales_array') THEN
    ALTER TABLE public.novedad_mensual
      ADD CONSTRAINT ck_novedad_adicionales_array
      CHECK (jsonb_typeof(adicionales_convencionales) = 'array');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_novedad_cantidades_object') THEN
    ALTER TABLE public.novedad_mensual
      ADD CONSTRAINT ck_novedad_cantidades_object
      CHECK (jsonb_typeof(cantidades_adicionales) = 'object');
  END IF;
END $$;

COMMIT;
