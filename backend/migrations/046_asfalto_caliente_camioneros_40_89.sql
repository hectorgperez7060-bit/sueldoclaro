-- CCT 40/89 · asfalto y productos que requieren calentamiento.
BEGIN;

DELETE FROM public.parametro_legal
WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01' AND version=1
  AND codigo='CAM_ASFALTO_JORNALES_POR_DIA';

INSERT INTO public.parametro_legal
 (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,
  is_verified,version,cct_numero,incidencias)
VALUES (
 gen_random_uuid(),'CAM_ASFALTO_JORNALES_POR_DIA',1,'jornal','rama_pct',
 DATE '2026-08-01',DATE '2026-08-31',
 'CCT 40/89 ítem 5.5.2; Planilla salarial FedCam 8/26 hoja 2',
 'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,'40/89',
 jsonb_build_object(
  'descripcion','Un jornal por día que realiza la operación con asfalto o producto caliente',
  'base','jornal_categoria','remunerativo',true,'integra_antiguedad',true,
  'integra_aportes',true,'articulo','5.5.2','requiere_adicional_combustibles',true
 )
);

DO $$
BEGIN
 IF NOT EXISTS (
  SELECT 1 FROM public.parametro_legal
  WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01'
    AND codigo='CAM_ASFALTO_JORNALES_POR_DIA' AND is_verified
 ) THEN
  RAISE EXCEPTION 'No se cargó la regla verificada de asfalto caliente';
 END IF;
END $$;

COMMIT;
