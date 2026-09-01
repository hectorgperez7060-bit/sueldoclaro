-- Perfil registral requerido por Libro de Sueldos Digital (ARCA).
-- Idempotente: puede ejecutarse una sola vez desde el editor SQL de Supabase.
ALTER TABLE public.empleado
    ADD COLUMN IF NOT EXISTS perfil_arca jsonb NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE public.empleado
    DROP CONSTRAINT IF EXISTS ck_empleado_perfil_arca_objeto;

ALTER TABLE public.empleado
    ADD CONSTRAINT ck_empleado_perfil_arca_objeto
    CHECK (jsonb_typeof(perfil_arca) = 'object');

COMMENT ON COLUMN public.empleado.perfil_arca IS
'Codigos registrales ARCA para Registro 04 LSD. No completar por inferencia; se fotografian en cada carpeta mensual.';
