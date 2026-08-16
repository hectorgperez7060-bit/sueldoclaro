-- Identidad visible de convenios. No cambia empleados ni liquidaciones.
BEGIN;

UPDATE public.cct SET nombre = 'Farmacia', sindicato = 'ADEF'
WHERE numero = '414/05';

UPDATE public.cct SET nombre = 'Sanidad', sindicato = 'FATSA'
WHERE numero = '122/75';

UPDATE public.cct SET nombre = 'Empleados de Comercio', sindicato = 'FAECYS'
WHERE numero = '130/75';

COMMIT;
