-- Cierre profesional común a todos los convenios.
BEGIN;

CREATE TABLE IF NOT EXISTS public.obligacion_pago_mensual (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES public.tenant(id),
  carpeta_id uuid NOT NULL REFERENCES public.carpeta_mensual(id),
  tipo varchar(30) NOT NULL CHECK (tipo IN ('ARCA_F931','SINDICAL','OBRA_SOCIAL','SEGURO','OTRA')),
  cct_numero varchar(20),
  destino_pago varchar(200) NOT NULL,
  codigo_boleta varchar(120) NOT NULL,
  importe numeric(15,2) CHECK (importe IS NULL OR importe >= 0),
  vencimiento date,
  canal_pago text,
  url_pago text,
  fuente_pago text,
  estado varchar(20) NOT NULL DEFAULT 'pendiente'
    CHECK (estado IN ('pendiente','generada','pagada','verificada')),
  comprobante text NOT NULL DEFAULT '',
  pagada_at timestamptz,
  verificada_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, carpeta_id, tipo, codigo_boleta, destino_pago)
);

CREATE INDEX IF NOT EXISTS ix_obligacion_pago_carpeta
  ON public.obligacion_pago_mensual(tenant_id, carpeta_id);

ALTER TABLE public.obligacion_pago_mensual ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.obligacion_pago_mensual FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS obligacion_pago_mensual_tenant_isolation ON public.obligacion_pago_mensual;
CREATE POLICY obligacion_pago_mensual_tenant_isolation
  ON public.obligacion_pago_mensual
  USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid);

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_role') THEN
    GRANT SELECT, INSERT, UPDATE ON public.obligacion_pago_mensual TO app_role;
    REVOKE DELETE, TRUNCATE ON public.obligacion_pago_mensual FROM app_role;
  END IF;
END
$$;

COMMIT;
