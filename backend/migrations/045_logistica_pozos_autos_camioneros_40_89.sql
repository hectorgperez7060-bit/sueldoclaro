-- CCT 40/89 · logística, pozos petrolíferos y transporte de automóviles.
BEGIN;

DELETE FROM public.parametro_legal
WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01' AND version=1
  AND codigo IN (
    'CAM_LOGISTICA_PCT','CAM_LOGISTICA_FRIO_PCT','CAM_POZOS_ESPECIALIDAD_PCT',
    'CAM_POZOS_VIATICOS_PCT','CAM_POZOS_CUENCA_PCT','CAM_POZOS_LP_MZA_PCT',
    'CAM_AUTOS_JORNALES_POR_VIAJE'
  );

WITH datos(codigo,valor,unidad,articulo,descripcion,base,remunerativo) AS (VALUES
 ('CAM_LOGISTICA_PCT',0.20::numeric,'%','5.12','Operaciones logísticas','basico_comida_viatico',true),
 ('CAM_LOGISTICA_FRIO_PCT',0.22::numeric,'%','5.12','Operaciones logísticas en cámara de frío','basico_comida_viatico',true),
 ('CAM_POZOS_ESPECIALIDAD_PCT',0.40::numeric,'%','5.7.4','Especialidad pozos petrolíferos','basico_categoria',true),
 ('CAM_POZOS_VIATICOS_PCT',0.40::numeric,'%','5.7.4.a','Recargo comida y viáticos de pozos','comida_viatico',false),
 ('CAM_POZOS_CUENCA_PCT',0.125::numeric,'%','5.7.4.c','Adicional por cuenca petrolífera','basico_categoria',true),
 ('CAM_POZOS_LP_MZA_PCT',0.20::numeric,'%','5.7.4.d','Adicional La Pampa y Mendoza con coeficiente 1,20','basico_categoria_zonal',true),
 ('CAM_AUTOS_JORNALES_POR_VIAJE',1::numeric,'jornal','4.2.9','Transporte de automóviles','jornal_categoria',true)
)
INSERT INTO public.parametro_legal
 (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,
  is_verified,version,cct_numero,incidencias)
SELECT gen_random_uuid(),codigo,valor,unidad,'rama_pct',DATE '2026-08-01',DATE '2026-08-31',
 'CCT 40/89 ítem '||articulo||'; Planilla salarial FedCam 8/26 hoja 2',
 'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,'40/89',
 jsonb_build_object('descripcion',descripcion,'base',base,'remunerativo',remunerativo,
                    'integra_antiguedad',remunerativo,'integra_aportes',remunerativo,
                    'articulo',articulo)
FROM datos;

DO $$
DECLARE cantidad integer;
BEGIN
 SELECT count(*) INTO cantidad FROM public.parametro_legal
 WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01'
   AND codigo IN (
    'CAM_LOGISTICA_PCT','CAM_LOGISTICA_FRIO_PCT','CAM_POZOS_ESPECIALIDAD_PCT',
    'CAM_POZOS_VIATICOS_PCT','CAM_POZOS_CUENCA_PCT','CAM_POZOS_LP_MZA_PCT',
    'CAM_AUTOS_JORNALES_POR_VIAJE'
   ) AND is_verified;
 IF cantidad <> 7 THEN
   RAISE EXCEPTION 'No se cargaron las siete reglas de logística, pozos y automóviles';
 END IF;
END $$;

COMMIT;
