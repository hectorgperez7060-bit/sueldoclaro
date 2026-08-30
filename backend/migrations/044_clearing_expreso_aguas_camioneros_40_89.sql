-- CCT 40/89 · clearing, expreso/mudanzas y aguas gaseosas.
-- Valores vigentes publicados en la planilla salarial FedCam 8/26.
BEGIN;

DELETE FROM public.parametro_legal
WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01' AND version=1
  AND codigo IN (
    'CAM_CLEARING_PCT','CAM_EXPRESO_PCT','CAM_EXPRESO_FRIO_PCT',
    'CAM_AGUAS_GASEOSAS_20_PCT','CAM_AGUAS_GASEOSAS_16_PCT'
  );

WITH datos(codigo,valor,articulo,descripcion,base,remunerativo) AS (VALUES
 ('CAM_CLEARING_PCT',0.20::numeric,'5.2.2','Clearing y carga postal','basico_comida_viatico',true),
 ('CAM_EXPRESO_PCT',0.16::numeric,'5.10','Expreso, mudanzas y encomiendas','basico_comida_viatico',true),
 ('CAM_EXPRESO_FRIO_PCT',0.18::numeric,'5.10','Expreso, mudanzas y encomiendas en cámara de frío','basico_comida_viatico',true),
 ('CAM_AGUAS_GASEOSAS_20_PCT',0.20::numeric,'5.11.1','Conductores, taller y administrativos de aguas gaseosas','basico_categoria',true),
 ('CAM_AGUAS_GASEOSAS_16_PCT',0.16::numeric,'5.11.1','Operarios especializados, maestranza y serenos de aguas gaseosas','basico_categoria',true)
)
INSERT INTO public.parametro_legal
 (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,
  is_verified,version,cct_numero,incidencias)
SELECT gen_random_uuid(),codigo,valor,'%','rama_pct',DATE '2026-08-01',DATE '2026-08-31',
 'CCT 40/89 ítem '||articulo||'; Planilla salarial FedCam 8/26 hoja 2',
 'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,'40/89',
 jsonb_build_object('descripcion',descripcion,'base',base,'remunerativo',remunerativo,
                    'integra_antiguedad',remunerativo,'integra_aportes',remunerativo,
                    'articulo',articulo,
                    'recarga_comida_y_viatico',base='basico_comida_viatico')
FROM datos;

DO $$
DECLARE cantidad integer;
BEGIN
 SELECT count(*) INTO cantidad FROM public.parametro_legal
 WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01'
   AND codigo IN (
    'CAM_CLEARING_PCT','CAM_EXPRESO_PCT','CAM_EXPRESO_FRIO_PCT',
    'CAM_AGUAS_GASEOSAS_20_PCT','CAM_AGUAS_GASEOSAS_16_PCT'
   ) AND is_verified;
 IF cantidad <> 5 THEN
   RAISE EXCEPTION 'No se cargaron las cinco reglas de clearing, expreso y aguas gaseosas';
 END IF;
END $$;

COMMIT;
