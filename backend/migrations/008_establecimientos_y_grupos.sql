-- Agrupación comercial de sociedades y domicilios laborales por empresa.
ALTER TABLE tenant
    ADD COLUMN IF NOT EXISTS grupo_cliente varchar(200) NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS establecimiento (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    nombre varchar(120) NOT NULL,
    domicilio varchar(200) NOT NULL,
    localidad varchar(120) NOT NULL DEFAULT '',
    provincia varchar(120) NOT NULL DEFAULT '',
    actividad varchar(120) NOT NULL DEFAULT '',
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_establecimiento_tenant_id ON establecimiento (tenant_id);

ALTER TABLE empleado
    ADD COLUMN IF NOT EXISTS establecimiento_id uuid NULL REFERENCES establecimiento(id);
CREATE INDEX IF NOT EXISTS ix_empleado_establecimiento_id ON empleado (establecimiento_id);

CREATE TABLE IF NOT EXISTS empleado_establecimiento_historial (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    empleado_id uuid NOT NULL REFERENCES empleado(id),
    establecimiento_id uuid NOT NULL REFERENCES establecimiento(id),
    vigente_desde date NOT NULL,
    vigente_hasta date NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_empleado_establecimiento_historial_vigencia_establecimiento_valida
      CHECK (vigente_hasta IS NULL OR vigente_hasta >= vigente_desde)
);
CREATE INDEX IF NOT EXISTS ix_empleado_establecimiento_historial_tenant_id
    ON empleado_establecimiento_historial (tenant_id);
CREATE INDEX IF NOT EXISTS ix_empleado_establecimiento_historial_empleado_id
    ON empleado_establecimiento_historial (empleado_id);

ALTER TABLE establecimiento ENABLE ROW LEVEL SECURITY;
ALTER TABLE establecimiento FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS establecimiento_tenant_isolation ON establecimiento;
CREATE POLICY establecimiento_tenant_isolation ON establecimiento
USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);

ALTER TABLE empleado_establecimiento_historial ENABLE ROW LEVEL SECURITY;
ALTER TABLE empleado_establecimiento_historial FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS empleado_establecimiento_historial_tenant_isolation
    ON empleado_establecimiento_historial;
CREATE POLICY empleado_establecimiento_historial_tenant_isolation
ON empleado_establecimiento_historial
USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);
