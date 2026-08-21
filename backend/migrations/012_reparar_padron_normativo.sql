-- Reparación defensiva del padrón normativo después de la primera instalación.
-- Reejecutable: no duplica convenios, categorías ni reglas.
BEGIN;

INSERT INTO public.cct (
  id, numero, nombre, sindicato, cuota_sindical_pct,
  antiguedad_pct_por_anio, presentismo_divisor, divisor_horas,
  aplica_presentismo, aplica_cuota_sindical, activo
)
SELECT gen_random_uuid(), '414/05', 'Empleados de Farmacia (ADEF)', 'ADEF',
       0, 0, 12, 200, false, false, true
WHERE NOT EXISTS (SELECT 1 FROM public.cct WHERE numero = '414/05');

-- Reconstruye las categorías ya acreditadas por escalas históricas.
INSERT INTO public.cct_categoria (
  cct_numero, codigo, nombre, orden, activa, fuente, is_verified, version
)
SELECT
  e.cct_numero,
  substr(upper(regexp_replace(e.categoria, '[^[:alnum:]]+', '_', 'g')), 1, 50)
    || '_' || substr(md5(e.categoria), 1, 8),
  e.categoria, 0, true,
  coalesce(max(nullif(e.fuente, '')), 'Escala salarial histórica'),
  bool_or(e.is_verified), 1
FROM public.escala_salarial e
WHERE NOT EXISTS (
  SELECT 1 FROM public.cct_categoria c
  WHERE c.cct_numero = e.cct_numero AND c.nombre = e.categoria AND c.activa
)
GROUP BY e.cct_numero, e.categoria;

-- El padrón ADEF es estructural: deben verse las seis categorías aun cuando
-- únicamente una tenga importe verificado para el mes.
INSERT INTO public.cct_categoria
  (cct_numero, codigo, nombre, orden, fuente, is_verified, version, activa)
VALUES
  ('414/05','INICIAL_A','Categoría Inicial A',10,'CCT 414/05',true,1,true),
  ('414/05','INICIAL_B','Categoría Inicial B',20,'CCT 414/05',true,1,true),
  ('414/05','CAJERO_PERF_ADMIN','Cajero, Perfumería y Administrativo',30,'CCT 414/05',true,1,true),
  ('414/05','EMPLEADO_FARMACIA','Empleado de Farmacia',40,'CCT 414/05',true,1,true),
  ('414/05','EMPLEADO_ESPECIALIZADO','Empleado Especializado de Farmacia',50,'CCT 414/05',true,1,true),
  ('414/05','FARMACEUTICO','Farmacéutico',60,'CCT 414/05',true,1,true)
ON CONFLICT (cct_numero, codigo, version) DO UPDATE SET
  nombre=EXCLUDED.nombre, orden=EXCLUDED.orden, fuente=EXCLUDED.fuente,
  is_verified=EXCLUDED.is_verified, activa=true;

INSERT INTO public.cct_regla_estructural
  (cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,is_verified,version,activa)
VALUES
  ('414/05','ANTIGUEDAD','antiguedad','Escalones por años cumplidos','13',
   '{"escalones":[[1,0.05],[2,0.10],[5,0.20],[10,0.30],[15,0.35],[20,0.40],[25,0.50]]}',
   'CCT 414/05 art. 13',true,1,true),
  ('414/05','JORNADA','jornada','Jornada convencional y regímenes especiales','14-16',
   '{"completa_horas":45,"nocturna_horas":42,"insalubre_horas":33,"parcial_menor_horas":30}',
   'CCT 414/05 arts. 14 a 16',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, articulo=EXCLUDED.articulo,
  configuracion=EXCLUDED.configuracion, fuente=EXCLUDED.fuente,
  is_verified=EXCLUDED.is_verified, activa=true;

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sueldoclaro') THEN
    GRANT SELECT ON public.cct_categoria TO sueldoclaro;
    GRANT SELECT ON public.cct_regla_estructural TO sueldoclaro;
  END IF;
END $$;

COMMIT;
