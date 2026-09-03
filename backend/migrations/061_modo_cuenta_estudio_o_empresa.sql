-- Una cuenta puede ser un estudio contable, que lleva varias empresas
-- clientes, o una sola empresa que se liquida a si misma. El estudio necesita
-- la capa de clientes; la empresa no, y verla de mas solo le complica la
-- carga. Las cuentas que ya existen quedan como estudio, que es como venia
-- funcionando la aplicacion.
BEGIN;

ALTER TABLE public.usuario
  ADD COLUMN IF NOT EXISTS modo_cuenta varchar(20) NOT NULL DEFAULT 'ESTUDIO';

ALTER TABLE public.usuario
  DROP CONSTRAINT IF EXISTS ck_usuario_modo_cuenta;
ALTER TABLE public.usuario
  ADD CONSTRAINT ck_usuario_modo_cuenta
  CHECK (modo_cuenta IN ('ESTUDIO', 'EMPRESA'));

COMMIT;
