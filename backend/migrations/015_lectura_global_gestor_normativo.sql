-- Las tablas normativas son globales (sin tenant_id) y de solo lectura para la
-- aplicacion. Si Supabase activo RLS automaticamente, el rol de la app veia
-- cero filas aunque los datos existieran. Los permisos SQL siguen limitando la
-- escritura: sueldoclaro recibe SELECT, nunca INSERT/UPDATE/DELETE.
BEGIN;

ALTER TABLE public.cct_categoria DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.cct_regla_estructural DISABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sueldoclaro') THEN
    REVOKE INSERT, UPDATE, DELETE, TRUNCATE
      ON public.cct_categoria, public.cct_regla_estructural FROM sueldoclaro;
    GRANT SELECT
      ON public.cct_categoria, public.cct_regla_estructural TO sueldoclaro;
  END IF;
END $$;

COMMIT;
