-- Perfil laboral explícito por empresa y parámetros oficiales de agosto 2026.
BEGIN;

ALTER TABLE public.tenant
  ADD COLUMN IF NOT EXISTS modo_liquidacion varchar(20) NOT NULL DEFAULT 'PRUEBA',
  ADD COLUMN IF NOT EXISTS actividad_sector varchar(30) NOT NULL DEFAULT 'PENDIENTE',
  ADD COLUMN IF NOT EXISTS condicion_mipyme varchar(30) NOT NULL DEFAULT 'PENDIENTE',
  ADD COLUMN IF NOT EXISTS certificado_mipyme_vigente_hasta date,
  ADD COLUMN IF NOT EXISTS respaldo_regimen_patronal text NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS regimen_contribucion_patronal varchar(30) NOT NULL DEFAULT 'PENDIENTE',
  ADD COLUMN IF NOT EXISTS fundamento_regimen_patronal text NOT NULL DEFAULT '';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_tenant_modo_liquidacion'
  ) THEN
    ALTER TABLE public.tenant ADD CONSTRAINT ck_tenant_modo_liquidacion
      CHECK (modo_liquidacion IN ('PRUEBA', 'PRODUCCION'));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_tenant_actividad_sector'
  ) THEN
    ALTER TABLE public.tenant ADD CONSTRAINT ck_tenant_actividad_sector
      CHECK (actividad_sector IN (
        'PENDIENTE', 'COMERCIO', 'SERVICIOS', 'INDUSTRIA',
        'CONSTRUCCION', 'AGRO', 'MINERIA', 'OTRO'
      ));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_tenant_condicion_mipyme'
  ) THEN
    ALTER TABLE public.tenant ADD CONSTRAINT ck_tenant_condicion_mipyme
      CHECK (condicion_mipyme IN (
        'PENDIENTE', 'CERTIFICADO_VIGENTE', 'SUPERA_LIMITES'
      ));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_tenant_regimen_contribucion_patronal'
  ) THEN
    ALTER TABLE public.tenant ADD CONSTRAINT ck_tenant_regimen_contribucion_patronal
      CHECK (regimen_contribucion_patronal IN (
        'PENDIENTE', 'PRIVADO_18', 'SERVICIOS_COMERCIO_204'
      ));
  END IF;
END
$$;

-- En agosto de 2026 la Ley 23.660 mantiene el 5%. El 6% de la Ley 27.802
-- comienza con las contribuciones devengadas desde el 1 de enero de 2027.
UPDATE public.parametro_legal
SET valor = 0.05,
    valid_to = CASE
      WHEN valid_to IS NULL OR valid_to > DATE '2026-12-31' THEN DATE '2026-12-31'
      ELSE valid_to
    END,
    is_verified = true,
    estado_fuente = 'VERIFICADA_OFICIAL',
    fuente = 'Ley 23.660, art. 16 inc. a (texto vigente en 2026): contribución patronal 5%. Ley 27.802, art. 165: 6% desde 2027-01-01. https://biblioteca.arca.gob.ar/dcp/LEY_C_023660_1988_12_29'
WHERE codigo = 'CONTRIB_OBRA_SOCIAL'
  AND cct_numero IS NULL
  AND valid_from <= DATE '2026-08-31'
  AND (valid_to IS NULL OR valid_to >= DATE '2026-08-01');

INSERT INTO public.parametro_legal (
  id, codigo, valor, unidad, ambito, valid_from, valid_to,
  fuente, estado_fuente, is_verified, version, cct_numero, incidencias
)
SELECT
  gen_random_uuid(), 'CONTRIB_OBRA_SOCIAL', 0.06, '%', 'empleador',
  DATE '2027-01-01', NULL,
  'Ley 27.802, art. 165: contribución patronal de obra social 6% desde 2027-01-01. https://biblioteca.arca.gob.ar/dcp/LEY_C_027802_2026_02_27',
  'VERIFICADA_OFICIAL', true, 2, NULL, '{}'::jsonb
WHERE NOT EXISTS (
  SELECT 1 FROM public.parametro_legal
  WHERE codigo = 'CONTRIB_OBRA_SOCIAL'
    AND cct_numero IS NULL
    AND valid_from = DATE '2027-01-01'
);

-- Tope previsional exacto del período devengado agosto de 2026.
UPDATE public.parametro_legal
SET valor = 4594798.23,
    valid_from = DATE '2026-08-01',
    valid_to = DATE '2026-08-31',
    is_verified = true,
    estado_fuente = 'VERIFICADA_OFICIAL',
    fuente = 'Resolución ANSES 232/2026, art. 3: base imponible máxima $4.594.798,23 para agosto de 2026. https://www.boletinoficial.gob.ar/detalleAviso/primera/345155/20260730'
WHERE codigo = 'TOPE_SIPA'
  AND cct_numero IS NULL
  AND valid_from <= DATE '2026-08-31'
  AND (valid_to IS NULL OR valid_to >= DATE '2026-08-01');

COMMIT;
