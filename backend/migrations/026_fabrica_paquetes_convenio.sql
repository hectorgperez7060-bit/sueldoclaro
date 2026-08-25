-- Registro técnico de cada paquete normativo instalado.
-- Los datos legales continúan en sus tablas versionadas; esta tabla aporta
-- huella, resumen y trazabilidad de instalación.
BEGIN;

CREATE TABLE IF NOT EXISTS public.cct_paquete_version (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cct_numero varchar(20) NOT NULL,
  paquete_version varchar(40) NOT NULL,
  hash_sha256 varchar(64) NOT NULL,
  estado varchar(20) NOT NULL DEFAULT 'INSTALADO'
    CHECK (estado IN ('BORRADOR','VALIDADO','INSTALADO','BLOQUEADO')),
  resumen jsonb NOT NULL DEFAULT '{}'::jsonb,
  fuente_manifest text NOT NULL DEFAULT '',
  instalado_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (cct_numero, paquete_version)
);

CREATE INDEX IF NOT EXISTS ix_cct_paquete_version_cct
  ON public.cct_paquete_version (cct_numero, instalado_at DESC);

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sueldoclaro') THEN
    GRANT SELECT ON public.cct_paquete_version TO sueldoclaro;
  END IF;
END $$;

COMMIT;
