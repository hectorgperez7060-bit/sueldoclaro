-- Identidad visible de convenios. No cambia empleados ni liquidaciones.
BEGIN;

INSERT INTO public.cct (
  id, numero, nombre, sindicato, cuota_sindical_pct,
  antiguedad_pct_por_anio, presentismo_divisor, divisor_horas,
  aplica_presentismo, aplica_cuota_sindical, activo
) VALUES (
  gen_random_uuid(), '414/05', 'Farmacia', 'ADEF', 0,
  0, 12, 200, false, false, true
)
ON CONFLICT (numero) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  sindicato = EXCLUDED.sindicato,
  activo = true;

UPDATE public.cct SET nombre = 'Sanidad', sindicato = 'FATSA'
WHERE numero = '122/75';

UPDATE public.cct SET nombre = 'Empleados de Comercio', sindicato = 'FAECYS'
WHERE numero = '130/75';

COMMIT;
