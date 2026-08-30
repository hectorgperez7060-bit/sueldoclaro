-- ADEF CCT 414/05 · escala completa y sumas no remunerativas de julio 2026.
-- Fuente oficial: ADEF, "Nuevas escalas salariales ... hasta julio 2026".
-- https://adef.org.ar/images/Escala-Salarial-MAY26_final2.jpg
--
-- No crea valores para agosto: ADEF no publicó en su sitio una escala 414/05
-- posterior a julio al momento de esta carga. La ausencia debe bloquear o
-- requerir confirmación; nunca convertirse silenciosamente en cero.

BEGIN;

WITH datos(categoria, basico, no_remunerativo) AS (
  VALUES
    ('Categoría Inicial A',                         1341694.15::numeric, 39692.42::numeric),
    ('Categoría Inicial B',                         1435611.36::numeric, 42469.57::numeric),
    ('Cajero, Perfumería y Administrativo',         1486864.61::numeric, 43986.02::numeric),
    ('Empleado de Farmacia',                        1538116.45::numeric, 45586.01::numeric),
    ('Empleado Especializado de Farmacia',          1828730.75::numeric, 54100.54::numeric),
    ('Farmacéutico',                                 1999675.61::numeric, 59156.96::numeric)
), actualizadas AS (
  UPDATE public.escala_salarial e
     SET basico = d.basico,
         valid_to = DATE '2026-07-31',
         fuente = 'ADEF · escala oficial abril-julio 2026 (planilla mayo 2026)',
         estado_fuente = 'PUBLICADA_POR_PARTE_SIGNATARIA',
         is_verified = true,
         provisoria = false
    FROM datos d
   WHERE e.cct_numero = '414/05'
     AND e.categoria = d.categoria
     AND e.valid_from = DATE '2026-07-01'
  RETURNING e.categoria
)
INSERT INTO public.escala_salarial (
  id, cct_numero, categoria, basico, valid_from, valid_to, fuente,
  estado_fuente, is_verified, version, provisoria
)
SELECT gen_random_uuid(), '414/05', d.categoria, d.basico,
       DATE '2026-07-01', DATE '2026-07-31',
       'ADEF · escala oficial abril-julio 2026 (planilla mayo 2026)',
       'PUBLICADA_POR_PARTE_SIGNATARIA', true, 1, false
  FROM datos d
 WHERE NOT EXISTS (
   SELECT 1 FROM public.escala_salarial e
    WHERE e.cct_numero='414/05' AND e.categoria=d.categoria
      AND e.valid_from=DATE '2026-07-01'
 );

WITH datos(codigo, categoria, importe) AS (
  VALUES
    ('FARMACIA_NR_INICIAL_A_414/05',       'Categoría Inicial A',                         39692.42::numeric),
    ('FARMACIA_NR_INICIAL_B_414/05',       'Categoría Inicial B',                         42469.57::numeric),
    ('FARMACIA_NR_CAJERO_ADMIN_414/05',    'Cajero, Perfumería y Administrativo',         43986.02::numeric),
    ('FARMACIA_NR_EMPLEADO_414/05',        'Empleado de Farmacia',                        45586.01::numeric),
    ('FARMACIA_NR_ESPECIALIZADO_414/05',   'Empleado Especializado de Farmacia',          54100.54::numeric),
    ('FARMACIA_NR_FARMACEUTICO_414/05',    'Farmacéutico',                                59156.96::numeric)
)
DELETE FROM public.parametro_legal p
 USING datos d
 WHERE p.codigo=d.codigo AND p.cct_numero='414/05'
   AND p.valid_from=DATE '2026-07-01' AND p.version=1;

WITH datos(codigo, categoria, importe) AS (
  VALUES
    ('FARMACIA_NR_INICIAL_A_414/05',       'Categoría Inicial A',                         39692.42::numeric),
    ('FARMACIA_NR_INICIAL_B_414/05',       'Categoría Inicial B',                         42469.57::numeric),
    ('FARMACIA_NR_CAJERO_ADMIN_414/05',    'Cajero, Perfumería y Administrativo',         43986.02::numeric),
    ('FARMACIA_NR_EMPLEADO_414/05',        'Empleado de Farmacia',                        45586.01::numeric),
    ('FARMACIA_NR_ESPECIALIZADO_414/05',   'Empleado Especializado de Farmacia',          54100.54::numeric),
    ('FARMACIA_NR_FARMACEUTICO_414/05',    'Farmacéutico',                                59156.96::numeric)
)
INSERT INTO public.parametro_legal (
  id, codigo, valor, unidad, ambito, valid_from, valid_to, fuente,
  estado_fuente, is_verified, version, cct_numero, incidencias
)
SELECT gen_random_uuid(), d.codigo, d.importe, 'ARS', 'no_rem',
       DATE '2026-07-01', DATE '2026-07-31',
       'ADEF · escala oficial abril-julio 2026 (planilla mayo 2026)',
       'PUBLICADA_POR_PARTE_SIGNATARIA', true, 1, '414/05',
       jsonb_build_object(
         'categoria', d.categoria,
         'regla_jornada', 'solo_completa',
         'integra_antiguedad', false,
         'integra_presentismo', false,
         'aporte_jubilacion', false,
         'aporte_obra_social', false,
         'aporte_sindicato', true
       )
  FROM datos d;

COMMIT;
