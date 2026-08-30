-- UOM CCT 260/75 · habilitación controlada del motor para agosto 2026.
-- No cambia importes ni fuentes. Solo conecta las escalas ya documentadas
-- después de incorporar al cálculo los adicionales variables por rama.
DO $migracion$
DECLARE
  categorias_activas integer;
  escalas_verificadas integer;
  parametros_uom integer;
BEGIN
  SELECT count(DISTINCT nombre) INTO categorias_activas
  FROM public.cct_categoria
  WHERE cct_numero='260/75' AND activa AND is_verified;

  SELECT count(DISTINCT categoria) INTO escalas_verificadas
  FROM public.escala_salarial
  WHERE cct_numero='260/75'
    AND valid_from <= DATE '2026-08-28'
    AND (valid_to IS NULL OR valid_to >= DATE '2026-08-28')
    AND is_verified AND coalesce(trim(fuente),'') <> ''
    AND unidad_escala IN ('HORA','MENSUAL');

  SELECT count(*) INTO parametros_uom
  FROM public.parametro_legal
  WHERE cct_numero='260/75'
    AND valid_from <= DATE '2026-08-28'
    AND (valid_to IS NULL OR valid_to >= DATE '2026-08-28')
    AND is_verified AND coalesce(trim(fuente),'') <> '';

  IF categorias_activas <> 247 OR escalas_verificadas <> 247 OR parametros_uom < 84 THEN
    RAISE EXCEPTION
      'UOM no se habilitó: categorías %, escalas %, parámetros % (esperado 247/247/84 o más)',
      categorias_activas, escalas_verificadas, parametros_uom;
  END IF;

  UPDATE public.escala_salarial
  SET habilitada_liquidacion=true
  WHERE cct_numero='260/75'
    AND valid_from <= DATE '2026-08-28'
    AND (valid_to IS NULL OR valid_to >= DATE '2026-08-28')
    AND is_verified AND coalesce(trim(fuente),'') <> ''
    AND unidad_escala IN ('HORA','MENSUAL');

  IF (SELECT count(DISTINCT categoria)
      FROM public.escala_salarial
      WHERE cct_numero='260/75'
        AND valid_from <= DATE '2026-08-28'
        AND (valid_to IS NULL OR valid_to >= DATE '2026-08-28')
        AND is_verified AND habilitada_liquidacion) <> 247 THEN
    RAISE EXCEPTION 'UOM no quedó habilitado para sus 247 categorías';
  END IF;
END
$migracion$;
