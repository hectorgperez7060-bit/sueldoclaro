-- Cierre profesional común a todos los convenios.
BEGIN;

CREATE TABLE IF NOT EXISTS public.contador_profesional (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id uuid NOT NULL UNIQUE REFERENCES public.usuario(id),
  nombre_apellido varchar(200) NOT NULL,
  cuit varchar(11) NOT NULL,
  matricula varchar(60) NOT NULL,
  jurisdiccion varchar(120) NOT NULL,
  consejo_profesional varchar(200) NOT NULL,
  matricula_vigente boolean NOT NULL DEFAULT false,
  constancia_url text NOT NULL DEFAULT '',
  verificado_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_contador_consejo_matricula
    UNIQUE (consejo_profesional, matricula)
);

CREATE INDEX IF NOT EXISTS ix_contador_profesional_cuit
  ON public.contador_profesional(cuit);
CREATE INDEX IF NOT EXISTS ix_contador_profesional_usuario
  ON public.contador_profesional(usuario_id);

CREATE TABLE IF NOT EXISTS public.revision_profesional (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES public.tenant(id),
  carpeta_id uuid NOT NULL REFERENCES public.carpeta_mensual(id),
  contador_id uuid NOT NULL REFERENCES public.contador_profesional(id),
  usuario_id uuid NOT NULL REFERENCES public.usuario(id),
  nombre_apellido varchar(200) NOT NULL,
  matricula varchar(60) NOT NULL,
  jurisdiccion varchar(120) NOT NULL,
  consejo_profesional varchar(200) NOT NULL,
  hash_revisado varchar(64) NOT NULL,
  alcance text NOT NULL DEFAULT 'Revision mensual de liquidacion laboral',
  observaciones text NOT NULL DEFAULT '',
  firmado_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_revision_profesional_tenant
  ON public.revision_profesional(tenant_id);
CREATE INDEX IF NOT EXISTS ix_revision_profesional_carpeta
  ON public.revision_profesional(carpeta_id);
CREATE INDEX IF NOT EXISTS ix_revision_profesional_contador
  ON public.revision_profesional(contador_id);

ALTER TABLE public.revision_profesional ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.revision_profesional FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS revision_profesional_tenant_isolation
  ON public.revision_profesional;
CREATE POLICY revision_profesional_tenant_isolation
  ON public.revision_profesional
  USING (tenant_id = nullif(current_setting('app.current_tenant', true), '')::uuid)
  WITH CHECK (tenant_id = nullif(current_setting('app.current_tenant', true), '')::uuid);

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
  USING (tenant_id = nullif(current_setting('app.current_tenant', true), '')::uuid)
  WITH CHECK (tenant_id = nullif(current_setting('app.current_tenant', true), '')::uuid);

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_role') THEN
    GRANT SELECT, INSERT, UPDATE ON public.contador_profesional TO app_role;
    GRANT SELECT, INSERT ON public.revision_profesional TO app_role;
    GRANT SELECT, INSERT, UPDATE ON public.obligacion_pago_mensual TO app_role;
    REVOKE DELETE, TRUNCATE ON public.contador_profesional FROM app_role;
    REVOKE UPDATE, DELETE, TRUNCATE ON public.revision_profesional FROM app_role;
    REVOKE DELETE, TRUNCATE ON public.obligacion_pago_mensual FROM app_role;
  END IF;
END
$$;

COMMIT;
