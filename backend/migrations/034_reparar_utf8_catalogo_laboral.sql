-- Repara mojibake UTF-8 visible en categorías (ej. CategorÃ­a, FarmacÃ©utico).
-- No modifica códigos, importes, porcentajes ni vigencias.
BEGIN;

CREATE OR REPLACE FUNCTION pg_temp.reparar_utf8(texto text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT replace(replace(replace(replace(replace(replace(replace(replace(
         replace(replace(replace(replace(replace(replace(replace(replace(
         texto,
         'Ã¡','á'),'Ã©','é'),'Ã­','í'),'Ã³','ó'),'Ãº','ú'),'Ã±','ñ'),
         'Ã','Á'),'Ã‰','É'),'Ã','Í'),'Ã“','Ó'),'Ãš','Ú'),'Ã‘','Ñ'),
         'Â°','°'),'Âº','º'),'Âª','ª'),'Â ',' ')
$$;

UPDATE public.cct_categoria
SET nombre = pg_temp.reparar_utf8(nombre),
    fuente = pg_temp.reparar_utf8(fuente)
WHERE nombre LIKE '%Ã%' OR nombre LIKE '%Â%'
   OR fuente LIKE '%Ã%' OR fuente LIKE '%Â%';

UPDATE public.escala_salarial
SET categoria = pg_temp.reparar_utf8(categoria),
    fuente = pg_temp.reparar_utf8(fuente)
WHERE categoria LIKE '%Ã%' OR categoria LIKE '%Â%'
   OR fuente LIKE '%Ã%' OR fuente LIKE '%Â%';

UPDATE public.empleado
SET categoria = pg_temp.reparar_utf8(categoria)
WHERE categoria LIKE '%Ã%' OR categoria LIKE '%Â%';

UPDATE public.parametro_legal
SET fuente = pg_temp.reparar_utf8(fuente),
    incidencias = pg_temp.reparar_utf8(incidencias::text)::jsonb
WHERE fuente LIKE '%Ã%' OR fuente LIKE '%Â%'
   OR incidencias::text LIKE '%Ã%' OR incidencias::text LIKE '%Â%';

UPDATE public.cct_regla_estructural
SET descripcion = pg_temp.reparar_utf8(descripcion),
    fuente = pg_temp.reparar_utf8(fuente),
    configuracion = pg_temp.reparar_utf8(configuracion::text)::jsonb
WHERE descripcion LIKE '%Ã%' OR descripcion LIKE '%Â%'
   OR fuente LIKE '%Ã%' OR fuente LIKE '%Â%'
   OR configuracion::text LIKE '%Ã%' OR configuracion::text LIKE '%Â%';

COMMIT;
