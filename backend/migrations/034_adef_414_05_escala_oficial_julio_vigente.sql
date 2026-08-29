-- CCT 414/05 ADEF: escala oficial publicada en mayo de 2026,
-- con básicos de julio de 2026 vigentes hasta que una nueva escala los sustituya.
-- Fuente oficial ADEF: https://www.adef.org.ar/escala-salarial/escala-salarial-2026
-- Imagen reproducida por FENAEMFA:
-- https://www.fenaemfa.org.ar/images/escala_salarial/Escala-Salarial-MAY26_DEF.jpg
--
-- Las sumas "Adic. No Rem. por única vez" terminan el 31/07/2026: no se
-- trasladan a agosto. Los básicos no vuelven a cero al terminar el cronograma;
-- quedan vigentes hasta que exista una escala posterior documentada.

BEGIN;

ALTER TABLE public.escala_salarial
  ADD COLUMN IF NOT EXISTS provisoria boolean NOT NULL DEFAULT false;

-- Retira la autorización provisoria de agosto creada por la migración 010.
-- Ya no hace falta porque ahora se registra la tabla oficial completa.
DELETE FROM public.escala_salarial
WHERE cct_numero = '414/05'
  AND valid_from = DATE '2026-08-01'
  AND provisoria = true
  AND fuente LIKE 'Provisorio:%';

WITH datos(categoria, basico) AS (VALUES
  ('Categoría Inicial A', 1341694.15::numeric),
  ('Categoría Inicial B', 1435611.36::numeric),
  ('Cajero, Perfumería y Administrativo', 1486864.61::numeric),
  ('Empleado de Farmacia', 1538116.45::numeric),
  ('Empleado Especializado de Farmacia', 1828730.75::numeric),
  ('Farmacéutico', 1999675.61::numeric)
)
UPDATE public.escala_salarial e
SET basico = d.basico,
    valid_to = NULL,
    fuente = 'ADEF — Escala salarial abril a julio 2026, publicada 15/05/2026',
    is_verified = true,
    provisoria = false
FROM datos d
WHERE e.cct_numero = '414/05'
  AND e.categoria = d.categoria
  AND e.valid_from = DATE '2026-07-01';

WITH datos(categoria, basico) AS (VALUES
  ('Categoría Inicial A', 1341694.15::numeric),
  ('Categoría Inicial B', 1435611.36::numeric),
  ('Cajero, Perfumería y Administrativo', 1486864.61::numeric),
  ('Empleado de Farmacia', 1538116.45::numeric),
  ('Empleado Especializado de Farmacia', 1828730.75::numeric),
  ('Farmacéutico', 1999675.61::numeric)
)
INSERT INTO public.escala_salarial (
  id, cct_numero, categoria, basico, valid_from, valid_to,
  fuente, is_verified, version, provisoria
)
SELECT
  gen_random_uuid(), '414/05', d.categoria, d.basico,
  DATE '2026-07-01', NULL,
  'ADEF — Escala salarial abril a julio 2026, publicada 15/05/2026',
  true, 2, false
FROM datos d
WHERE NOT EXISTS (
  SELECT 1 FROM public.escala_salarial e
  WHERE e.cct_numero = '414/05'
    AND e.categoria = d.categoria
    AND e.valid_from = DATE '2026-07-01'
);

-- Seis pagos extraordinarios de julio, uno por categoría. Su vigencia queda
-- cerrada expresamente para impedir que el motor los copie a agosto.
WITH datos(codigo, categoria, importe) AS (VALUES
  ('FARMACIA_NR_INICIAL_A_414/05', 'Categoría Inicial A', 39692.42::numeric),
  ('FARMACIA_NR_INICIAL_B_414/05', 'Categoría Inicial B', 42469.57::numeric),
  ('FARMACIA_NR_CAJERO_ADMIN_414/05', 'Cajero, Perfumería y Administrativo', 43986.02::numeric),
  ('FARMACIA_NR_EMPLEADO_414/05', 'Empleado de Farmacia', 45502.61::numeric),
  ('FARMACIA_NR_ESPECIALIZADO_414/05', 'Empleado Especializado de Farmacia', 54100.54::numeric),
  ('FARMACIA_NR_FARMACEUTICO_414/05', 'Farmacéutico', 59156.96::numeric)
)
UPDATE public.parametro_legal p
SET valor = d.importe,
    unidad = 'ARS',
    ambito = 'no_rem',
    valid_to = DATE '2026-07-31',
    fuente = 'ADEF — Escala salarial abril a julio 2026, publicada 15/05/2026',
    is_verified = true,
    cct_numero = '414/05',
    incidencias = jsonb_build_object(
      'categoria', d.categoria,
      'regla_jornada', 'solo_completa',
      'integra_antiguedad', false,
      'integra_presentismo', false,
      'aporte_jubilacion', false,
      'aporte_obra_social', false,
      'aporte_sindicato', true
    )
FROM datos d
WHERE p.codigo = d.codigo
  AND p.valid_from = DATE '2026-07-01';

WITH datos(codigo, categoria, importe) AS (VALUES
  ('FARMACIA_NR_INICIAL_A_414/05', 'Categoría Inicial A', 39692.42::numeric),
  ('FARMACIA_NR_INICIAL_B_414/05', 'Categoría Inicial B', 42469.57::numeric),
  ('FARMACIA_NR_CAJERO_ADMIN_414/05', 'Cajero, Perfumería y Administrativo', 43986.02::numeric),
  ('FARMACIA_NR_EMPLEADO_414/05', 'Empleado de Farmacia', 45502.61::numeric),
  ('FARMACIA_NR_ESPECIALIZADO_414/05', 'Empleado Especializado de Farmacia', 54100.54::numeric),
  ('FARMACIA_NR_FARMACEUTICO_414/05', 'Farmacéutico', 59156.96::numeric)
)
INSERT INTO public.parametro_legal (
  id, codigo, valor, unidad, ambito, valid_from, valid_to,
  fuente, is_verified, version, cct_numero, incidencias
)
SELECT
  gen_random_uuid(), d.codigo, d.importe, 'ARS', 'no_rem',
  DATE '2026-07-01', DATE '2026-07-31',
  'ADEF — Escala salarial abril a julio 2026, publicada 15/05/2026',
  true, 2, '414/05',
  jsonb_build_object(
    'categoria', d.categoria,
    'regla_jornada', 'solo_completa',
    'integra_antiguedad', false,
    'integra_presentismo', false,
    'aporte_jubilacion', false,
    'aporte_obra_social', false,
    'aporte_sindicato', true
  )
FROM datos d
WHERE NOT EXISTS (
  SELECT 1 FROM public.parametro_legal p
  WHERE p.codigo = d.codigo
    AND p.valid_from = DATE '2026-07-01'
);

COMMIT;
