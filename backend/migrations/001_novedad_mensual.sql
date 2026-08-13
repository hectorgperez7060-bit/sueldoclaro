-- Etapa 0: persistencia de novedades mensuales.
-- Preparada para revisión. NO ejecutada en Supabase.

CREATE TABLE novedad_mensual (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    empleado_id uuid NOT NULL REFERENCES empleado(id),
    periodo varchar(7) NOT NULL,
    dias_trabajados integer NOT NULL DEFAULT 0,
    faltas_justificadas integer NOT NULL DEFAULT 0,
    faltas_injustificadas integer NOT NULL DEFAULT 0,
    horas_extra_50 numeric(8,2) NOT NULL DEFAULT 0,
    horas_extra_100 numeric(8,2) NOT NULL DEFAULT 0,
    licencias integer NOT NULL DEFAULT 0,
    vacaciones integer NOT NULL DEFAULT 0,
    premios numeric(18,2) NOT NULL DEFAULT 0,
    tipo_premio varchar(20) NOT NULL DEFAULT 'pendiente',
    descuentos_adicionales numeric(18,2) NOT NULL DEFAULT 0,
    observaciones text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_novedad_mensual_tenant_empleado_periodo
        UNIQUE (tenant_id, empleado_id, periodo),
    CONSTRAINT ck_novedad_mensual_periodo_yyyy_mm
        CHECK (periodo ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    CONSTRAINT ck_novedad_mensual_dias_no_negativos
        CHECK (dias_trabajados >= 0 AND faltas_justificadas >= 0
            AND faltas_injustificadas >= 0 AND licencias >= 0 AND vacaciones >= 0),
    CONSTRAINT ck_novedad_mensual_importes_horas_no_negativos
        CHECK (horas_extra_50 >= 0 AND horas_extra_100 >= 0
            AND premios >= 0 AND descuentos_adicionales >= 0),
    CONSTRAINT ck_novedad_mensual_tipo_premio_valido
        CHECK (tipo_premio IN ('pendiente', 'remunerativo', 'no_remunerativo')),
    CONSTRAINT ck_novedad_mensual_dias_segun_periodo CHECK (
        dias_trabajados <= EXTRACT(DAY FROM (TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day'))
        AND faltas_justificadas <= EXTRACT(DAY FROM (TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day'))
        AND faltas_injustificadas <= EXTRACT(DAY FROM (TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day'))
        AND licencias <= EXTRACT(DAY FROM (TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day'))
        AND vacaciones <= EXTRACT(DAY FROM (TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day'))
    )
);

CREATE INDEX ix_novedad_mensual_tenant_id ON novedad_mensual (tenant_id);
CREATE INDEX ix_novedad_mensual_empleado_id ON novedad_mensual (empleado_id);

ALTER TABLE novedad_mensual ENABLE ROW LEVEL SECURITY;
ALTER TABLE novedad_mensual FORCE ROW LEVEL SECURITY;
CREATE POLICY novedad_mensual_tenant_isolation ON novedad_mensual
    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sueldoclaro') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON novedad_mensual TO sueldoclaro;
  END IF;
END $$;
