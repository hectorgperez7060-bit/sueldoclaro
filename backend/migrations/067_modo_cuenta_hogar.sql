-- Agrega una experiencia guiada para familias empleadoras de personal de
-- casas particulares. No modifica empresas, empleados ni liquidaciones: solo
-- amplía la preferencia visual de la cuenta.
BEGIN;

ALTER TABLE public.usuario
  DROP CONSTRAINT IF EXISTS ck_usuario_modo_cuenta;
ALTER TABLE public.usuario
  ADD CONSTRAINT ck_usuario_modo_cuenta
  CHECK (modo_cuenta IN ('ESTUDIO', 'EMPRESA', 'HOGAR'));

COMMIT;
