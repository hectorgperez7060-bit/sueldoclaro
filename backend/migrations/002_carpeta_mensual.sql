-- Carpeta mensual versionada por empresa y período.
-- La revisión profesional se aplicará en una migración posterior.

BEGIN;

CREATE TABLE public.carpeta_mensual (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL,
  periodo varchar(7) NOT NULL,
  version integer NOT NULL DEFAULT 1,
  estado varchar(20) NOT NULL DEFAULT 'borrador',
  contenido jsonb NOT NULL DEFAULT '{}'::jsonb,
  hash_sha256 varchar(64),
  liquidacion_id uuid REFERENCES public.liquidacion(id),
  comprobante_presentacion text NOT NULL DEFAULT '',
  comprobante_aceptacion text NOT NULL DEFAULT '',
  comprobante_pago text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT uq_carpeta_tenant_periodo_version
    UNIQUE (tenant_id, periodo, version),
  CONSTRAINT ck_carpeta_periodo
    CHECK (periodo ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
  CONSTRAINT ck_carpeta_version_positiva
    CHECK (version >= 1),
  CONSTRAINT ck_carpeta_estado_valido
    CHECK (estado IN ('borrador','calculada','revisada','presentada','aceptada','pagada')),
  CONSTRAINT ck_carpeta_hash_sha256
    CHECK (hash_sha256 IS NULL OR hash_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE INDEX ix_carpeta_mensual_tenant_id
  ON public.carpeta_mensual (tenant_id);
CREATE INDEX ix_carpeta_mensual_liquidacion_id
  ON public.carpeta_mensual (liquidacion_id);

ALTER TABLE public.carpeta_mensual ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.carpeta_mensual FORCE ROW LEVEL SECURITY;

CREATE POLICY carpeta_mensual_tenant_isolation
ON public.carpeta_mensual
USING (
  tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid
)
WITH CHECK (
  tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid
);

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sueldoclaro') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE
    ON public.carpeta_mensual
    TO sueldoclaro;
  END IF;
END
$$;

COMMIT;
