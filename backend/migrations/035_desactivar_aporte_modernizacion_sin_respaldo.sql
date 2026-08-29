-- Desactiva para liquidaciones nuevas una retención personal que fue asociada
-- incorrectamente al art. 131 de la Ley 27.802. Ese artículo regula la
-- ultraactividad de los CCT y no crea un aporte a cargo del trabajador.
-- Las carpetas mensuales ya creadas permanecen intactas y auditables.
BEGIN;

UPDATE public.parametro_legal
SET valor = 0,
    is_verified = true,
    estado_fuente = 'VERIFICADA_OFICIAL',
    fuente = 'Ley 27.802, arts. 131 y 133 (texto oficial): no crean un aporte personal general denominado aporte modernización. https://www.argentina.gob.ar/normativa/nacional/norma-423680/texto',
    incidencias = COALESCE(incidencias, '{}'::jsonb) || jsonb_build_object(
      'desactivado', true,
      'motivo_desactivacion', 'Sin norma que autorice esta retención personal general'
    )
WHERE codigo = 'APORTE_MODERNIZACION'
  AND cct_numero IS NULL;

COMMIT;
