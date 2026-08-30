-- UTHGRA-FEHGRA CCT 389/04 · básicos y segunda cuota NR de agosto 2026.
-- Fuente oficial publicada por UTHGRA:
-- RE-2026-72653200-APN-CGDTEYS#MCH, Acta 24/07/2026, Anexo I, pág. 5 de 5.
--
-- El acuerdo fue presentado y ratificado, pero al 30/08/2026 no se encontró
-- acto homologatorio oficial publicado. Por eso los valores quedan cargados
-- para prueba y trazabilidad con is_verified=false: no deben cerrar una
-- liquidación definitiva hasta incorporar la homologación.

BEGIN;

UPDATE public.cct SET
  nombre='Gastronómicos y Hoteleros', sindicato='UTHGRA',
  antiguedad_pct_por_anio=0, aplica_presentismo=false,
  aplica_cuota_sindical=false, activo=true
WHERE numero='389/04';

DROP TABLE IF EXISTS public._staging_uthgra_agosto_2026;
CREATE TABLE public._staging_uthgra_agosto_2026 (
  clase text, nivel integer, basico numeric, no_remunerativo numeric
);

INSERT INTO public._staging_uthgra_agosto_2026 VALUES
 ('D',1, 990555, 68000), ('D',2,1047930,72000), ('D',3,1099139,75000),
 ('D',4,1157884, 79000), ('D',5,1210980,83000), ('D',6,1292026,88000),
 ('C',1,1013346, 69000), ('C',2,1080354,74000), ('C',3,1148481,79000),
 ('C',4,1195083, 82000), ('C',5,1243418,85000), ('C',6,1337186,91000),
 ('B',1,1038120, 71000), ('B',2,1102324,75000), ('B',3,1180295,81000),
 ('B',4,1217642, 83000), ('B',5,1271299,87000), ('B',6,1384689,95000),
 ('B',7,1538297,105000),
 ('A',1,1074307, 74000), ('A',2,1141004,78000), ('A',3,1220868,83000),
 ('A',4,1284118, 88000), ('A',5,1356517,93000), ('A',6,1429981,98000),
 ('A',7,1840959,126000),
 ('ESP',1,1206779, 83000), ('ESP',2,1281272,88000), ('ESP',3,1342334,92000),
 ('ESP',4,1424619,97000), ('ESP',5,1483366,101000), ('ESP',6,1524806,104000),
 ('ESP',7,1970475,134000);

UPDATE public.cct_categoria SET activa=false WHERE cct_numero='389/04';

INSERT INTO public.cct_categoria
  (id,cct_numero,codigo,nombre,orden,activa,fuente,estado_fuente,is_verified,version)
SELECT gen_random_uuid(), '389/04',
       'N' || nivel || '_CLASE_' || clase,
       'Nivel ' || nivel || ' · Categoría ' || clase,
       CASE clase WHEN 'D' THEN 0 WHEN 'C' THEN 100 WHEN 'B' THEN 200
                  WHEN 'A' THEN 300 ELSE 400 END + nivel * 10,
       true,
       'CCT 389/04 arts. 10.1 y 11.1; acuerdo UTHGRA-FEHGRA 24/07/2026, Anexo I',
       'VERIFICADA_OFICIAL', true, 1
FROM public._staging_uthgra_agosto_2026 d
WHERE NOT EXISTS (
  SELECT 1 FROM public.cct_categoria c
  WHERE c.cct_numero='389/04' AND c.codigo='N' || d.nivel || '_CLASE_' || d.clase
);

UPDATE public.cct_categoria c SET activa=true
FROM public._staging_uthgra_agosto_2026 d
WHERE c.cct_numero='389/04' AND c.codigo='N' || d.nivel || '_CLASE_' || d.clase;

DELETE FROM public.escala_salarial
WHERE cct_numero='389/04' AND valid_from=DATE '2026-08-01';

INSERT INTO public.escala_salarial
  (id,cct_numero,categoria,basico,valid_from,valid_to,fuente,
   estado_fuente,is_verified,version,provisoria)
SELECT gen_random_uuid(), '389/04',
       'Nivel ' || nivel || ' · Categoría ' || clase,
       basico, DATE '2026-08-01', DATE '2026-08-31',
       'UTHGRA-FEHGRA · Acta 24/07/2026 · RE-2026-72653200 · Anexo I pág. 5',
       'PROVISORIA', false, 1, true
FROM public._staging_uthgra_agosto_2026;

DELETE FROM public.parametro_legal
WHERE cct_numero='389/04'
  AND codigo LIKE 'UTHGRA_ACUERDO_2026_SEGUNDA_%'
  AND valid_from=DATE '2026-08-01';

INSERT INTO public.parametro_legal
  (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,
   estado_fuente,is_verified,version,cct_numero,incidencias)
SELECT gen_random_uuid(),
       'UTHGRA_ACUERDO_2026_SEGUNDA_N' || nivel || '_' || clase,
       no_remunerativo, 'ARS', 'no_rem',
       DATE '2026-08-01', DATE '2026-08-31',
       'UTHGRA-FEHGRA · Acta 24/07/2026 · RE-2026-72653200 · PRIMERO y Anexo I pág. 5',
       'PROVISORIA', false, 1, '389/04',
       jsonb_build_object(
         'categoria', 'Nivel ' || nivel || ' · Categoría ' || clase,
         'regla_jornada', 'proporcional',
         'integra_antiguedad', false,
         'integra_presentismo', false,
         'aporte_jubilacion', false,
         'aporte_obra_social', false,
         'aporte_sindicato', false
       )
FROM public._staging_uthgra_agosto_2026;

DROP TABLE IF EXISTS public._staging_uthgra_agosto_2026;

COMMIT;