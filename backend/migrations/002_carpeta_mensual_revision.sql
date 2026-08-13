-- Carpeta mensual y revisión profesional. Preparada; NO ejecutada en Supabase.
CREATE TABLE contador_profesional (
  id uuid PRIMARY KEY, usuario_id uuid NOT NULL UNIQUE REFERENCES usuario(id),
  nombre_apellido varchar(200) NOT NULL, cuit varchar(11) NOT NULL,
  matricula varchar(60) NOT NULL, jurisdiccion varchar(120) NOT NULL,
  consejo_profesional varchar(200) NOT NULL, matricula_vigente boolean NOT NULL DEFAULT false,
  constancia_url text NOT NULL DEFAULT '', verificado_at timestamptz, created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_contador_consejo_matricula UNIQUE(consejo_profesional, matricula)
);
CREATE TABLE carpeta_mensual (
  id uuid PRIMARY KEY, tenant_id uuid NOT NULL, periodo varchar(7) NOT NULL,
  version integer NOT NULL DEFAULT 1, estado varchar(20) NOT NULL DEFAULT 'borrador',
  contenido jsonb NOT NULL DEFAULT '{}'::jsonb, hash_sha256 varchar(64),
  liquidacion_id uuid REFERENCES liquidacion(id), comprobante_presentacion text NOT NULL DEFAULT '',
  comprobante_aceptacion text NOT NULL DEFAULT '', comprobante_pago text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_carpeta_tenant_periodo_version UNIQUE(tenant_id, periodo, version),
  CONSTRAINT ck_carpeta_mensual_estado_valido CHECK (estado IN ('borrador','calculada','revisada','presentada','aceptada','pagada'))
);
CREATE TABLE revision_profesional (
  id uuid PRIMARY KEY, tenant_id uuid NOT NULL, carpeta_id uuid NOT NULL REFERENCES carpeta_mensual(id),
  contador_id uuid NOT NULL REFERENCES contador_profesional(id), usuario_id uuid NOT NULL REFERENCES usuario(id),
  nombre_apellido varchar(200) NOT NULL, matricula varchar(60) NOT NULL,
  jurisdiccion varchar(120) NOT NULL, consejo_profesional varchar(200) NOT NULL,
  hash_revisado varchar(64) NOT NULL, alcance text NOT NULL DEFAULT 'Revisión mensual de liquidación laboral',
  observaciones text NOT NULL DEFAULT '', firmado_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_carpeta_mensual_tenant_id ON carpeta_mensual(tenant_id);
CREATE INDEX ix_revision_profesional_tenant_id ON revision_profesional(tenant_id);
ALTER TABLE carpeta_mensual ENABLE ROW LEVEL SECURITY;
ALTER TABLE carpeta_mensual FORCE ROW LEVEL SECURITY;
CREATE POLICY carpeta_mensual_tenant_isolation ON carpeta_mensual USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);
ALTER TABLE revision_profesional ENABLE ROW LEVEL SECURITY;
ALTER TABLE revision_profesional FORCE ROW LEVEL SECURITY;
CREATE POLICY revision_profesional_tenant_isolation ON revision_profesional USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);
