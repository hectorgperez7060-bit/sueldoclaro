-- Datos contractuales de ART por establecimiento. No se cargan valores por
-- defecto: la alícuota y suma fija deben surgir del contrato del empleador.
BEGIN;

ALTER TABLE public.establecimiento
  ADD COLUMN IF NOT EXISTS art_nombre varchar(160) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS art_alicuota_pct numeric(8,4),
  ADD COLUMN IF NOT EXISTS art_suma_fija numeric(14,2),
  ADD COLUMN IF NOT EXISTS art_vigencia_desde date,
  ADD COLUMN IF NOT EXISTS art_vigencia_hasta date,
  ADD COLUMN IF NOT EXISTS art_comprobante_ref text NOT NULL DEFAULT '';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_establecimiento_art_alicuota'
  ) THEN
    ALTER TABLE public.establecimiento
      ADD CONSTRAINT ck_establecimiento_art_alicuota
      CHECK (art_alicuota_pct IS NULL OR art_alicuota_pct BETWEEN 0 AND 100);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_establecimiento_art_suma_fija'
  ) THEN
    ALTER TABLE public.establecimiento
      ADD CONSTRAINT ck_establecimiento_art_suma_fija
      CHECK (art_suma_fija IS NULL OR art_suma_fija >= 0);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_establecimiento_art_vigencia'
  ) THEN
    ALTER TABLE public.establecimiento
      ADD CONSTRAINT ck_establecimiento_art_vigencia
      CHECK (
        art_vigencia_desde IS NULL OR art_vigencia_hasta IS NULL
        OR art_vigencia_hasta >= art_vigencia_desde
      );
  END IF;
END
$$;

COMMIT;
