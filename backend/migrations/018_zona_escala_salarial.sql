-- Dimensión geográfica de las escalas. Las filas históricas quedan como
-- escalas nacionales (zona vacía); los convenios zonificados usan código.
BEGIN;

ALTER TABLE public.escala_salarial
  ADD COLUMN IF NOT EXISTS zona varchar(20) NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS ix_escala_cct_categoria_zona_vigencia
  ON public.escala_salarial (cct_numero, categoria, zona, valid_from);

COMMIT;
