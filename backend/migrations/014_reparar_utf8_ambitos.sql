-- Reparacion ASCII-safe de textos que Windows PowerShell pudo copiar con una
-- codificacion incorrecta. U& usa escapes Unicode interpretados por PostgreSQL.
BEGIN;

UPDATE public.cct
SET nombre = U&'Cl\00EDnicas, sanatorios, geri\00E1tricos y establecimientos con internaci\00F3n'
WHERE numero = '122/75';

UPDATE public.cct_regla_estructural
SET descripcion = U&'La actividad principal es cl\00EDnica, sanatorio, geri\00E1trico o establecimiento con internaci\00F3n; una farmacia interna es un sector del establecimiento sanitario.',
    articulo = 'ambito personal y de actividad'
WHERE cct_numero = '122/75' AND codigo = 'AMBITO_ACTIVIDAD' AND version = 1;

COMMIT;
