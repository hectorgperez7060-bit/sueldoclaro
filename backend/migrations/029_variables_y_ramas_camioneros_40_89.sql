-- Hoja 2 Planilla FedCam 8/26: valores variables y reglas de rama.
BEGIN;

DO $$
DECLARE r record;
BEGIN
FOR r IN SELECT * FROM (VALUES
 ('CAM_COMIDA_4_1_12',16033.49::numeric,'ARS','variable','{"unidad_cantidad":"dia","coeficiente_zona":true}'::jsonb),
 ('CAM_VIATICO_ESP_4_1_13',8045.57::numeric,'ARS','variable','{"unidad_cantidad":"dia","coeficiente_zona":true}'::jsonb),
 ('CAM_PERNOCTADA_4_1_14',18674.56::numeric,'ARS','variable','{"unidad_cantidad":"pernoctada","coeficiente_zona":true}'::jsonb),
 ('CAM_HORA_EXTRA_KM_4_2_3',83.82825::numeric,'ARS','variable','{"unidad_cantidad":"kilometro","coeficiente_zona":true}'::jsonb),
 ('CAM_VIATICO_KM_4_2_4',83.82825::numeric,'ARS','variable','{"unidad_cantidad":"kilometro","minimo_por_dia":350,"garantia_cordillera":700,"coeficiente_zona":true}'::jsonb),
 ('CAM_PERMANENCIA_4_2_5',56584.48::numeric,'ARS','variable','{"unidad_cantidad":"permanencia"}'::jsonb),
 ('CAM_SIMPLE_PRESENCIA_4_2_5',29659.77::numeric,'ARS','variable','{"unidad_cantidad":"presencia"}'::jsonb),
 ('CAM_PERMANENCIA_SUR_4_2_5',68014.08::numeric,'ARS','variable','{"unidad_cantidad":"permanencia"}'::jsonb),
 ('CAM_SIMPLE_PRESENCIA_SUR_4_2_5',35629.54::numeric,'ARS','variable','{"unidad_cantidad":"presencia"}'::jsonb),
 ('CAM_CRUCE_FRONTERA_4_2_17',38967.57::numeric,'ARS','variable','{"unidad_cantidad":"cruce"}'::jsonb),
 ('CAM_INGRESO_EGRESO_TDF_4_2_17',44433.39::numeric,'ARS','variable','{"unidad_cantidad":"ingreso_egreso"}'::jsonb),
 ('CAM_AGUAS_GAS_CHOFER_LD_5_11_3A2',329895.37::numeric,'ARS','variable','{"unidad_cantidad":"mes","rama":"aguas_gaseosas"}'::jsonb),
 ('CAM_PLUS_VACACIONAL_3_3_2',24476.52::numeric,'ARS','variable','{"unidad_cantidad":"dia"}'::jsonb),
 ('CAM_ADICIONAL_BITRENES',677108.16::numeric,'ARS','variable','{"unidad_cantidad":"unidad","requiere_verificar_hecho_generador":true}'::jsonb)
) AS x(codigo,valor,unidad,ambito,incidencias)
LOOP
  DELETE FROM public.parametro_legal WHERE codigo=r.codigo AND cct_numero='40/89'
    AND valid_from=DATE '2026-08-01' AND version=1;
  INSERT INTO public.parametro_legal
   (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,is_verified,version,cct_numero,incidencias)
  VALUES (gen_random_uuid(),r.codigo,r.valor,r.unidad,r.ambito,DATE '2026-08-01',DATE '2026-08-31',
   'Planilla salarial FedCam 8/26 hoja 2; Acuerdo homologado por Disposición 455/2026',
   'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,'40/89',r.incidencias);
END LOOP;
END $$;

-- Catálogo permanente. Los porcentajes se aplican únicamente cuando la rama
-- y el hecho generador fueron informados; no se activan por categoría sola.
WITH reglas(codigo,descripcion,articulo,configuracion) AS (VALUES
 ('RAMA_MATERIA_PRIMA_LACTEA','Transporte de materia prima láctea: adicional 15%.','3.1.3','{"porcentaje":0.15,"requiere_rama":true}'),
 ('RAMA_AUXILIO','Camiones o camionetas de auxilio: adicional 10%.','3.1.4','{"porcentaje":0.10,"requiere_rama":true}'),
 ('RAMA_RESIDUOS','Personal operativo de residuos: adicional 15%.','5.3.3/5.3.6/5.3.8','{"porcentaje":0.15,"requiere_rama":true}'),
 ('RAMA_TALLER_OFICIAL','Oficiales de taller grupos I y III: adicional 25%.','3.1.13','{"porcentaje":0.25,"requiere_grupo":true}'),
 ('RAMA_TALLER_MEDIO_OFICIAL','Medio oficiales grupos I y III: adicional 18%.','3.1.13','{"porcentaje":0.18,"requiere_grupo":true}'),
 ('RAMA_CUSTODIO_BLINDADO','Custodio de unidades blindadas: adicional 20%.','5.1.13','{"porcentaje":0.20,"requiere_rama":true}'),
 ('RAMA_DIARIOS_REVISTAS','Distribución de diarios y revistas: adicional 12%.','5.4.1','{"porcentaje":0.12,"requiere_rama":true}'),
 ('RAMA_COMBUSTIBLES','Transporte de combustibles: adicional 15%.','5.5.1','{"porcentaje":0.15,"requiere_rama":true}'),
 ('RAMA_SUSTANCIAS_PELIGROSAS','Transporte de sustancias peligrosas: adicional 20%.','5.6.2','{"porcentaje":0.20,"requiere_rama":true}'),
 ('RAMA_POZOS_PETROLIFEROS','Pozos petrolíferos: adicional 40%, más reglas de cuenca.','5.7.4','{"porcentaje":0.40,"requiere_cuenca":true,"reglas_adicionales_pendientes":true}'),
 ('RAMA_CLEARING_CHOFER','Clearing: chofer adicional 17% sobre comida y viáticos.','5.2.2','{"porcentaje":0.17,"base":"comida_y_viaticos"}'),
 ('RAMA_CLEARING_OTROS','Clearing: categorías detalladas adicional 16% sobre comida y viáticos.','5.2.2','{"porcentaje":0.16,"base":"comida_y_viaticos","requiere_categoria":true}'),
 ('RAMA_EXPRESO_MUDANZA','Expreso, mudanza y encomiendas: adicional 16%.','5.10','{"porcentaje":0.16,"camara_frio":0.18}'),
 ('RAMA_AGUAS_GASEOSAS','Aguas gaseosas: 20% o 16% según categoría.','5.11.1','{"porcentajes":{"conductor_taller_admin":0.20,"operario_maestranza_sereno":0.16}}'),
 ('RAMA_LOGISTICA','Operaciones logísticas, almacenamiento y distribución: adicional 16%.','5.12','{"porcentaje":0.16,"camara_frio":0.18}'),
 ('RAMA_LARGA_DISTANCIA','Chofer de larga distancia: adicional 10% y conceptos por kilometraje.','4.2','{"porcentaje_chofer":0.10,"requiere_kilometros":true}')
)
INSERT INTO public.cct_regla_estructural
 (id,cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,estado_fuente,is_verified,version,activa)
SELECT gen_random_uuid(),'40/89',codigo,'rama',descripcion,articulo,configuracion::jsonb,
 'CCT 40/89; Planilla FedCam 8/26 hoja 2','PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true
FROM reglas
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
 descripcion=EXCLUDED.descripcion,articulo=EXCLUDED.articulo,configuracion=EXCLUDED.configuracion,
 fuente=EXCLUDED.fuente,estado_fuente=EXCLUDED.estado_fuente,is_verified=true,activa=true;

UPDATE public.cct_paquete_version SET
 resumen='{"categorias":43,"zonas":3,"escalas":129,"parametros_variables":14,"reglas":21,"motor":"VISTA_PREVIA","pendiente":"captura de novedades por rama e integración al recibo"}'::jsonb,
 estado='VALIDADO',instalado_at=now()
WHERE cct_numero='40/89' AND paquete_version='2026.08-estructura-hoja1-v1';

COMMIT;
