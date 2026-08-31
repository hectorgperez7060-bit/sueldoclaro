-- CCT 40/89 · habilitación controlada del motor completo para agosto 2026.
-- No altera importes. Habilita únicamente escalas verificadas y documentadas.
DO $migracion$
DECLARE
  escalas_verificadas integer;
  parametros_camioneros integer;
BEGIN
  SELECT count(DISTINCT (e.categoria, coalesce(e.zona, ''))) INTO escalas_verificadas
  FROM public.escala_salarial e
  JOIN public.cct_categoria c
    ON c.cct_numero=e.cct_numero AND c.nombre=e.categoria
   AND c.activa AND c.is_verified
  WHERE e.cct_numero='40/89'
    AND e.valid_from <= DATE '2026-08-31'
    AND (e.valid_to IS NULL OR e.valid_to >= DATE '2026-08-01')
    AND e.is_verified AND coalesce(trim(e.fuente),'') <> '';

  SELECT count(*) INTO parametros_camioneros
  FROM public.parametro_legal
  WHERE cct_numero='40/89'
    AND valid_from <= DATE '2026-08-31'
    AND (valid_to IS NULL OR valid_to >= DATE '2026-08-01')
    AND is_verified AND coalesce(trim(fuente),'') <> '';

  IF escalas_verificadas <> 129 OR parametros_camioneros < 47 THEN
    RAISE EXCEPTION
      'Camioneros no se habilitó: escalas %, parámetros % (esperado 129/47 o más)',
      escalas_verificadas, parametros_camioneros;
  END IF;

  UPDATE public.escala_salarial e
  SET habilitada_liquidacion=true
  WHERE e.cct_numero='40/89'
    AND e.valid_from <= DATE '2026-08-31'
    AND (e.valid_to IS NULL OR e.valid_to >= DATE '2026-08-01')
    AND e.is_verified AND coalesce(trim(e.fuente),'') <> ''
    AND EXISTS (
      SELECT 1 FROM public.cct_categoria c
      WHERE c.cct_numero=e.cct_numero AND c.nombre=e.categoria
        AND c.activa AND c.is_verified
    );

  IF (SELECT count(DISTINCT (e.categoria, coalesce(e.zona, '')))
      FROM public.escala_salarial e
      JOIN public.cct_categoria c
        ON c.cct_numero=e.cct_numero AND c.nombre=e.categoria
       AND c.activa AND c.is_verified
      WHERE e.cct_numero='40/89'
        AND e.valid_from <= DATE '2026-08-31'
        AND (e.valid_to IS NULL OR e.valid_to >= DATE '2026-08-01')
        AND e.is_verified AND e.habilitada_liquidacion) <> 129 THEN
    RAISE EXCEPTION 'Camioneros no quedó habilitado para sus 129 escalas';
  END IF;
END
$migracion$;
