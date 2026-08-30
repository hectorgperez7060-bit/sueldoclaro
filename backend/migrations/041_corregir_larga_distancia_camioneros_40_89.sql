-- CCT 40/89 · corrige la regla de larga distancia sin alterar escalas ni historia.
-- El 10% no corresponde a esta rama. El ítem 4.2.6 establece un jornal por
-- cada traslado de la unidad para descarga, contemplando el ítem 4.2.5.
BEGIN;

UPDATE public.cct_regla_estructural
SET descripcion = 'Personal de larga distancia: un jornal por cada traslado de la unidad para descarga; kilómetros, permanencias y viáticos según los ítems 4.2.',
    articulo = '4.2.3 a 4.2.6 y 4.2.11',
    configuracion = '{"jornal_por_traslado_descarga":1,"jornal_divisor":24,"requiere_kilometros":true,"viaticos_item_4_2_no_remunerativos":true}'::jsonb,
    fuente = 'CCT 40/89 ítems 4.2.3 a 4.2.6 y 4.2.11; Planilla salarial FedCam 8/26 hoja 2',
    estado_fuente = 'PUBLICADA_POR_PARTE_SIGNATARIA',
    is_verified = true,
    activa = true
WHERE cct_numero = '40/89'
  AND codigo = 'RAMA_LARGA_DISTANCIA'
  AND version = 1;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.cct_regla_estructural
    WHERE cct_numero='40/89' AND codigo='RAMA_LARGA_DISTANCIA'
      AND version=1 AND activa AND is_verified
      AND configuracion @> '{"jornal_por_traslado_descarga":1,"jornal_divisor":24}'::jsonb
  ) THEN
    RAISE EXCEPTION 'No se pudo corregir la regla de larga distancia CCT 40/89';
  END IF;
END $$;

COMMIT;
