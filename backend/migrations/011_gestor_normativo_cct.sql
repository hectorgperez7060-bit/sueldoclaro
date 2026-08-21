-- Gestor normativo: separa el padrón estructural (estable) de los importes
-- versionados que ya viven en escala_salarial/parametro_legal.
BEGIN;

CREATE TABLE IF NOT EXISTS public.cct_categoria (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cct_numero varchar(20) NOT NULL,
  codigo varchar(60) NOT NULL,
  nombre varchar(160) NOT NULL,
  orden integer NOT NULL DEFAULT 0,
  activa boolean NOT NULL DEFAULT true,
  fuente text NOT NULL DEFAULT '',
  is_verified boolean NOT NULL DEFAULT false,
  version integer NOT NULL DEFAULT 1,
  UNIQUE (cct_numero, codigo, version)
);

CREATE INDEX IF NOT EXISTS ix_cct_categoria_cct
  ON public.cct_categoria (cct_numero, activa);

CREATE TABLE IF NOT EXISTS public.cct_regla_estructural (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cct_numero varchar(20) NOT NULL,
  codigo varchar(80) NOT NULL,
  tipo varchar(40) NOT NULL,
  descripcion text NOT NULL,
  articulo varchar(40) NOT NULL DEFAULT '',
  configuracion jsonb NOT NULL DEFAULT '{}'::jsonb,
  fuente text NOT NULL DEFAULT '',
  is_verified boolean NOT NULL DEFAULT false,
  version integer NOT NULL DEFAULT 1,
  activa boolean NOT NULL DEFAULT true,
  UNIQUE (cct_numero, codigo, version)
);

CREATE INDEX IF NOT EXISTS ix_cct_regla_estructural_cct
  ON public.cct_regla_estructural (cct_numero, activa);

-- Recupera el padrón ya existente sin duplicar datos.
INSERT INTO public.cct_categoria (
  cct_numero, codigo, nombre, orden, fuente, is_verified
)
SELECT DISTINCT
  e.cct_numero,
  upper(regexp_replace(e.categoria, '[^[:alnum:]]+', '_', 'g'))
    || '_' || substr(md5(e.categoria), 1, 8),
  e.categoria,
  0,
  coalesce(nullif(e.fuente, ''), 'Escala salarial histórica'),
  e.is_verified
FROM public.escala_salarial e
WHERE e.cct_numero <> '414/05'
  AND NOT EXISTS (
  SELECT 1 FROM public.cct_categoria c
  WHERE c.cct_numero = e.cct_numero AND c.nombre = e.categoria AND c.activa
);

-- Categorías estructurales de Farmacia: existen aunque falte su escala mensual.
INSERT INTO public.cct_categoria
  (cct_numero, codigo, nombre, orden, fuente, is_verified)
VALUES
  ('414/05','INICIAL_A','Categoría Inicial A',10,'CCT 414/05',true),
  ('414/05','INICIAL_B','Categoría Inicial B',20,'CCT 414/05',true),
  ('414/05','CAJERO_PERF_ADMIN','Cajero, Perfumería y Administrativo',30,'CCT 414/05',true),
  ('414/05','EMPLEADO_FARMACIA','Empleado de Farmacia',40,'CCT 414/05',true),
  ('414/05','EMPLEADO_ESPECIALIZADO','Empleado Especializado de Farmacia',50,'CCT 414/05',true),
  ('414/05','FARMACEUTICO','Farmacéutico',60,'CCT 414/05',true)
ON CONFLICT (cct_numero, codigo, version) DO UPDATE SET
  nombre=EXCLUDED.nombre, orden=EXCLUDED.orden, fuente=EXCLUDED.fuente,
  is_verified=EXCLUDED.is_verified, activa=true;

INSERT INTO public.cct_regla_estructural
  (cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,is_verified)
VALUES
  ('414/05','ANTIGUEDAD','antiguedad','Escalones por años cumplidos','13',
   '{"escalones":[[1,0.05],[2,0.10],[5,0.20],[10,0.30],[15,0.35],[20,0.40],[25,0.50]]}',
   'CCT 414/05 art. 13',true),
  ('414/05','JORNADA','jornada','Jornada convencional y regímenes especiales','14-16',
   '{"completa_horas":45,"nocturna_horas":42,"insalubre_horas":33,"parcial_menor_horas":30}',
   'CCT 414/05 arts. 14 a 16',true)
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
