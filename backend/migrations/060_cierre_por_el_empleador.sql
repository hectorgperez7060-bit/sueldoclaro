-- Un empleador puede armar el recibo, pagar ARCA y pagar las boletas
-- sindicales sin contador: no hay norma que se lo prohiba. El cierre mensual
-- dejaba de estar disponible si el usuario no tenia matricula. Ahora el cierre
-- lo puede hacer el administrador de la empresa, y si ademas es contador
-- matriculado el cierre queda firmado con su matricula.
BEGIN;

ALTER TABLE public.revision_profesional
  ALTER COLUMN contador_id DROP NOT NULL,
  ALTER COLUMN matricula DROP NOT NULL,
  ALTER COLUMN jurisdiccion DROP NOT NULL,
  ALTER COLUMN consejo_profesional DROP NOT NULL;

ALTER TABLE public.revision_profesional
  ADD COLUMN IF NOT EXISTS tipo_cierre varchar(20) NOT NULL DEFAULT 'CONTADOR';

COMMIT;
