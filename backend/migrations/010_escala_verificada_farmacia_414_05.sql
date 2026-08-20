-- Escala y no remunerativo VERIFICADOS del CCT 414/05 (ADEF) — julio 2026.
-- Fuente: recibo real de control + CCT 414/05.
--
-- Se carga ÚNICAMENTE el Empleado Especializado de Farmacia (única categoría
-- con escala verificada disponible). Las demás categorías oficiales quedan
-- deliberadamente sin escala: se ven en el encuadramiento pero la liquidación
-- se BLOQUEA por falta de escala verificada. No se estima ni se pone en cero.
--
-- Los importes viven acá (dato versionado en las tablas existentes), no en el
-- código del dominio ni del motor. Migración idempotente: reejecutable sin
-- duplicar. NO ejecutada en Supabase por este cambio: preparada para revisión.

BEGIN;

-- Básico verificado del Empleado Especializado, julio 2026.
DO $$
BEGIN
  UPDATE public.escala_salarial
  SET basico = 1828730.75, valid_to = DATE '2026-07-31',
      fuente = 'Recibo real de control + CCT 414/05', is_verified = true
  WHERE cct_numero = '414/05'
    AND categoria = 'Empleado Especializado de Farmacia'
    AND valid_from = DATE '2026-07-01';
  IF NOT FOUND THEN
    INSERT INTO public.escala_salarial (
      id, cct_numero, categoria, basico, valid_from, valid_to, fuente, is_verified, version
    ) VALUES (
      gen_random_uuid(), '414/05', 'Empleado Especializado de Farmacia',
      1828730.75, DATE '2026-07-01', DATE '2026-07-31',
      'Recibo real de control + CCT 414/05', true, 1
    );
  END IF;
END $$;

-- No remunerativo verificado: EXCLUSIVO del Empleado Especializado y de julio
-- 2026. La vigencia acotada (jul 2026) impide que se traslade a agosto u otros
-- períodos. La categoría queda registrada en las incidencias.
INSERT INTO public.parametro_legal (
  id, codigo, valor, unidad, ambito, valid_from, valid_to,
  fuente, is_verified, version, cct_numero, incidencias
)
SELECT
  gen_random_uuid(), 'FARMACIA_NR_ESPECIALIZADO_414/05', 54100.54, 'ARS', 'no_rem',
  DATE '2026-07-01', DATE '2026-07-31',
  'Recibo real de control + CCT 414/05', true, 1, '414/05',
  '{"categoria":"Empleado Especializado de Farmacia","integra_antiguedad":false,"integra_presentismo":false,"aporte_jubilacion":false,"aporte_obra_social":false,"aporte_sindicato":true}'::jsonb
WHERE NOT EXISTS (
  SELECT 1 FROM public.parametro_legal
  WHERE codigo = 'FARMACIA_NR_ESPECIALIZADO_414/05' AND valid_from = DATE '2026-07-01'
);

COMMIT;
