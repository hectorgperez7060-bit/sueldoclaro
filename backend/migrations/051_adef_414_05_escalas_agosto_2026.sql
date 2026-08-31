-- CCT 414/05 · ADEF · escala oficial abril-julio 2026 y ultraactividad agosto 2026.
-- Fuente primaria: ADEF, Escala Salarial Abril a Julio 2026.
-- https://www.adef.org.ar/escala-salarial/escala-salarial-2026
--
-- Agosto conserva los básicos oficiales de julio por ultraactividad (art. 2
-- CCT 414/05 y art. 6 Ley 14.250), queda marcado PROVISORIO y exige
-- confirmación expresa. No traslada los adicionales no remunerativos
-- identificados por ADEF como importes de única vez hasta julio.
BEGIN;

ALTER TABLE public.escala_salarial
  ADD COLUMN IF NOT EXISTS provisoria boolean NOT NULL DEFAULT false;

WITH escala(categoria, basico) AS (
  VALUES
    ('Categoría Inicial A', 1341694.15::numeric),
    ('Categoría Inicial B', 1435611.36::numeric),
    ('Cajero, Perfumería y Administrativo', 1486864.61::numeric),
    ('Empleado de Farmacia', 1538116.45::numeric),
    ('Empleado Especializado de Farmacia', 1828730.75::numeric),
    ('Farmacéutico', 1999675.61::numeric)
)
DELETE FROM public.escala_salarial e
USING escala x
WHERE e.cct_numero='414/05'
  AND e.categoria=x.categoria
  AND e.valid_from IN (DATE '2026-07-01', DATE '2026-08-01');

WITH escala(categoria, basico) AS (
  VALUES
    ('Categoría Inicial A', 1341694.15::numeric),
    ('Categoría Inicial B', 1435611.36::numeric),
    ('Cajero, Perfumería y Administrativo', 1486864.61::numeric),
    ('Empleado de Farmacia', 1538116.45::numeric),
    ('Empleado Especializado de Farmacia', 1828730.75::numeric),
    ('Farmacéutico', 1999675.61::numeric)
)
INSERT INTO public.escala_salarial (
  id, cct_numero, categoria, basico, valid_from, valid_to, fuente,
  is_verified, version, provisoria, habilitada_liquidacion
)
SELECT
  gen_random_uuid(), '414/05', categoria, basico,
  DATE '2026-07-01', DATE '2026-07-31',
  'ADEF · Escala Salarial Abril a Julio 2026 · columna Julio 2026',
  true, 2, false, true
FROM escala;

WITH escala(categoria, basico) AS (
  VALUES
    ('Categoría Inicial A', 1341694.15::numeric),
    ('Categoría Inicial B', 1435611.36::numeric),
    ('Cajero, Perfumería y Administrativo', 1486864.61::numeric),
    ('Empleado de Farmacia', 1538116.45::numeric),
    ('Empleado Especializado de Farmacia', 1828730.75::numeric),
    ('Farmacéutico', 1999675.61::numeric)
)
INSERT INTO public.escala_salarial (
  id, cct_numero, categoria, basico, valid_from, valid_to, fuente,
  is_verified, version, provisoria, habilitada_liquidacion
)
SELECT
  gen_random_uuid(), '414/05', categoria, basico,
  DATE '2026-08-01', DATE '2026-08-31',
  'ADEF · básico oficial julio 2026 ultraactivo en agosto · CCT 414/05 art. 2 y Ley 14.250 art. 6 · requiere confirmación',
  true, 2, true, true
FROM escala;

DO $$
DECLARE
  julio integer;
  agosto integer;
BEGIN
  SELECT count(DISTINCT categoria) INTO julio
  FROM public.escala_salarial
  WHERE cct_numero='414/05'
    AND valid_from=DATE '2026-07-01'
    AND is_verified AND NOT provisoria;

  SELECT count(DISTINCT categoria) INTO agosto
  FROM public.escala_salarial
  WHERE cct_numero='414/05'
    AND valid_from=DATE '2026-08-01'
    AND is_verified AND provisoria AND habilitada_liquidacion;

  IF julio <> 6 OR agosto <> 6 THEN
    RAISE EXCEPTION
      'ADEF no quedó completo: julio %, agosto provisorio % (esperado 6/6)',
      julio, agosto;
  END IF;
END
$$;

COMMIT;
