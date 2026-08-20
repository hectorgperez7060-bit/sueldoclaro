-- Permisos de la aplicación para las tablas incorporadas por la migración 008.
-- Es una migración separada porque 008 ya fue ejecutada en producción.
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sueldoclaro') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON establecimiento TO sueldoclaro;
    GRANT SELECT, INSERT, UPDATE, DELETE
      ON empleado_establecimiento_historial TO sueldoclaro;
  END IF;
END $$;
