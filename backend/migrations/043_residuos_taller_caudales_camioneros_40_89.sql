-- CCT 40/89 · residuos, taller y caudales. Porcentajes sobre básico,
-- salvo comida de residuos que recarga el viático no remunerativo.
BEGIN;

DELETE FROM public.parametro_legal
WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01' AND version=1
  AND codigo IN (
   'CAM_RESIDUOS_OPERATIVO_PCT','CAM_RESIDUOS_COMIDA_PCT',
   'CAM_TALLER_OFICIAL_PCT','CAM_TALLER_MEDIO_PCT',
   'CAM_CAUDALES_CUSTODIO_PCT','CAM_MULTIPLICIDAD_OFICIAL_PCT',
   'CAM_MULTIPLICIDAD_OTROS_PCT'
  );

WITH datos(codigo,valor,articulo,descripcion,base,remunerativo) AS (VALUES
 ('CAM_RESIDUOS_OPERATIVO_PCT',0.15::numeric,'5.3.3/5.3.6/5.3.8','Personal operativo de residuos','basico_categoria',true),
 ('CAM_RESIDUOS_COMIDA_PCT',0.15::numeric,'5.3.11','Recargo comida de residuos','comida_4_1_12',false),
 ('CAM_TALLER_OFICIAL_PCT',0.25::numeric,'3.1.13','Oficial de taller grupos I y III','basico_categoria',true),
 ('CAM_TALLER_MEDIO_PCT',0.18::numeric,'3.1.13','Medio oficial de taller grupos I y III','basico_categoria',true),
 ('CAM_CAUDALES_CUSTODIO_PCT',0.20::numeric,'5.1.13','Custodio de unidad blindada','basico_categoria',true),
 ('CAM_MULTIPLICIDAD_OFICIAL_PCT',0.10::numeric,'5.1.17/5.3.25','Multiplicidad oficial taller caudales o residuos','basico_categoria',true),
 ('CAM_MULTIPLICIDAD_OTROS_PCT',0.02::numeric,'5.1.17/5.3.25','Multiplicidad medio oficial, lavador, engrasador o ayudante','basico_categoria',true)
)
INSERT INTO public.parametro_legal
 (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,
  is_verified,version,cct_numero,incidencias)
SELECT gen_random_uuid(),codigo,valor,'%','rama_pct',DATE '2026-08-01',DATE '2026-08-31',
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
    'CAM_RESIDUOS_OPERATIVO_PCT','CAM_RESIDUOS_COMIDA_PCT',
    'CAM_TALLER_OFICIAL_PCT','CAM_TALLER_MEDIO_PCT',
    'CAM_CAUDALES_CUSTODIO_PCT','CAM_MULTIPLICIDAD_OFICIAL_PCT',
    'CAM_MULTIPLICIDAD_OTROS_PCT'
   ) AND is_verified;
 IF cantidad <> 7 THEN
   RAISE EXCEPTION 'No se cargaron las siete reglas de residuos, taller y caudales';
 END IF;
END $$;

COMMIT;
