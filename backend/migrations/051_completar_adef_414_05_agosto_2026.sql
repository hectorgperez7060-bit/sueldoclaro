-- ADEF CCT 414/05 · básicos completos aplicables a agosto 2026.
-- Fuente salarial oficial: ADEF, escala abril-julio 2026, columna julio.
-- Aplicación en agosto: ultraactividad expresa del CCT 414/05 art. 2 y
-- Ley 14.250 art. 6. Las asignaciones "por única vez" finalizan en julio
-- y deliberadamente NO se trasladan a agosto.
DO $migracion$
DECLARE
  categorias_verificadas integer;
  escalas_habilitadas integer;
  parametros_adef integer;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.cct WHERE numero='414/05' AND activo
  ) THEN
    RAISE EXCEPTION 'No existe el CCT 414/05 activo';
  END IF;

  SELECT count(DISTINCT nombre) INTO categorias_verificadas
  FROM public.cct_categoria
  WHERE cct_numero='414/05' AND activa AND is_verified;

  SELECT count(*) INTO parametros_adef
  FROM public.parametro_legal
  WHERE cct_numero='414/05'
    AND valid_from <= DATE '2026-08-31'
    AND (valid_to IS NULL OR valid_to >= DATE '2026-08-01')
    AND is_verified AND coalesce(trim(fuente),'') <> '';

  IF categorias_verificadas <> 6 OR parametros_adef < 2 THEN
    RAISE EXCEPTION
      'ADEF no se habilitó: categorías %, parámetros % (esperado 6/2 o más)',
      categorias_verificadas, parametros_adef;
  END IF;

  DELETE FROM public.escala_salarial
  WHERE cct_numero='414/05'
    AND valid_from=DATE '2026-08-01';

  INSERT INTO public.escala_salarial
    (id,cct_numero,categoria,basico,valid_from,valid_to,fuente,
     estado_fuente,is_verified,version,provisoria,habilitada_liquidacion)
  VALUES
    (gen_random_uuid(),'414/05','Categoría Inicial A',1341694.15,
     DATE '2026-08-01',DATE '2026-08-31',
     'ADEF · escala oficial abril-julio 2026, columna julio · ultraactividad CCT 414/05 art. 2',
     'VERIFICADA_OFICIAL',true,1,false,true),
    (gen_random_uuid(),'414/05','Categoría Inicial B',1435611.36,
     DATE '2026-08-01',DATE '2026-08-31',
     'ADEF · escala oficial abril-julio 2026, columna julio · ultraactividad CCT 414/05 art. 2',
     'VERIFICADA_OFICIAL',true,1,false,true),
    (gen_random_uuid(),'414/05','Cajero, Perfumería y Administrativo',1486864.61,
     DATE '2026-08-01',DATE '2026-08-31',
     'ADEF · escala oficial abril-julio 2026, columna julio · ultraactividad CCT 414/05 art. 2',
     'VERIFICADA_OFICIAL',true,1,false,true),
    (gen_random_uuid(),'414/05','Empleado de Farmacia',1538116.45,
     DATE '2026-08-01',DATE '2026-08-31',
     'ADEF · escala oficial abril-julio 2026, columna julio · ultraactividad CCT 414/05 art. 2',
     'VERIFICADA_OFICIAL',true,1,false,true),
    (gen_random_uuid(),'414/05','Empleado Especializado de Farmacia',1828730.75,
     DATE '2026-08-01',DATE '2026-08-31',
     'ADEF · escala oficial abril-julio 2026, columna julio · ultraactividad CCT 414/05 art. 2',
     'VERIFICADA_OFICIAL',true,1,false,true),
    (gen_random_uuid(),'414/05','Farmacéutico',1999675.61,
     DATE '2026-08-01',DATE '2026-08-31',
     'ADEF · escala oficial abril-julio 2026, columna julio · ultraactividad CCT 414/05 art. 2',
     'VERIFICADA_OFICIAL',true,1,false,true);

  SELECT count(DISTINCT e.categoria) INTO escalas_habilitadas
  FROM public.escala_salarial e
  JOIN public.cct_categoria c
    ON c.cct_numero=e.cct_numero AND c.nombre=e.categoria
   AND c.activa AND c.is_verified
  WHERE e.cct_numero='414/05'
    AND e.valid_from=DATE '2026-08-01'
    AND e.valid_to=DATE '2026-08-31'
    AND e.is_verified
    AND e.habilitada_liquidacion
    AND NOT e.provisoria
    AND coalesce(trim(e.fuente),'') <> '';

  IF escalas_habilitadas <> 6 THEN
    RAISE EXCEPTION
      'ADEF no quedó habilitado: % escalas válidas (esperado 6)',
      escalas_habilitadas;
  END IF;
END
$migracion$;
