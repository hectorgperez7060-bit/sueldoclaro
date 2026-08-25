-- Paquete Camioneros CCT 40/89 · estructura general y planilla 8/26.
-- Registra las 43 categorías y 129 escalas territoriales de la hoja 1.
-- El motor queda bloqueado hasta modelar la cartilla ampliatoria (hoja 2).
BEGIN;

INSERT INTO public.cct
 (id,numero,nombre,sindicato,cuota_sindical_pct,antiguedad_pct_por_anio,
  presentismo_divisor,divisor_horas,aplica_presentismo,aplica_cuota_sindical,activo)
VALUES
 (gen_random_uuid(),'40/89','Camioneros','FedCam',0,0.01,12,200,false,false,true)
ON CONFLICT (numero) DO UPDATE SET
 nombre=EXCLUDED.nombre,sindicato=EXCLUDED.sindicato,
 antiguedad_pct_por_anio=EXCLUDED.antiguedad_pct_por_anio,
 aplica_presentismo=false,aplica_cuota_sindical=false,activo=true;

WITH datos(codigo,nombre,orden,basico) AS (VALUES
 ('CONDUCTOR_1','Conductor de Primera Categoría',10,1047830.65),
 ('CONDUCTOR_2','Conductor de Segunda Categoría',20,1029157.90),
 ('CONDUCTOR_3_FLETES','Conductor de Tercera Categoría (Fletes al instante)',30,1010466.26),
 ('GRUA_HASTA_10','Conductores de grúas de hasta 10 toneladas y operadores de autoelevadores',40,1066511.23),
 ('GRUA_10_20','Conductores de grúas de más de 10 y hasta 20 toneladas',50,1173162.35),
 ('GRUA_20_35','Conductores de grúas de más de 20 y hasta 35 toneladas',60,1220088.84),
 ('GRUA_35_45','Conductores de grúas de más de 35 y hasta 45 toneladas',70,1268892.39),
 ('GRUA_45_55','Conductores de grúas de más de 45 y hasta 55 toneladas',80,1319648.09),
 ('GRUA_55_70','Conductores de grúas de más de 55 y hasta 70 toneladas',90,1385630.49),
 ('GRUA_70_90','Conductores de grúas de más de 70 y hasta 90 toneladas',100,1454912.01),
 ('GRUA_90_110','Conductores de grúas de más de 90 y hasta 110 toneladas',110,1527657.61),
 ('GRUA_110_140','Conductores de grúas de más de 110 y hasta 140 toneladas',120,1604040.49),
 ('GRUA_140_170','Conductores de grúas de más de 140 y hasta 170 toneladas',130,1684242.51),
 ('GRUA_170_300','Conductores de grúas de más de 170 y hasta 300 toneladas',140,1768454.64),
 ('GRUA_MAS_300','Conductores de grúas de más de 300 toneladas',150,1909931.01),
 ('ENCARGADO','Encargado',160,984812.93),
 ('RECIBIDOR_GUIAS','Recibidor y/o Clasificador de Guías',170,975419.30),
 ('OPERARIO_ESPECIALIZADO','Operarios Especializados',180,966217.77),
 ('RECOLECTOR_RESIDUOS','Recolectores de Residuo y Limpieza',190,966217.77),
 ('PEON','Peones',200,956996.33),
 ('PEON_BARRIDO','Peones Generales de Barrido y Limpieza',210,956996.33),
 ('OPERADOR_SERVICIOS','Operador de Servicios',220,1114933.30),
 ('DISTRIBUIDOR_DOMICILIARIO','Distribuidor Domiciliario',230,1014804.90),
 ('AYUDANTE_MAYOR_18','Ayudantes Mayores de 18 Años',240,938655.67),
 ('CHOFER_BLINDADO','Chofer de Camión Blindado',250,1126550.90),
 ('CHOFER_CON_FIRMA','Chofer con Firma',260,1209889.63),
 ('CUSTODIA_CAUDALES','Custodia de Camión de Caudales',270,976709.64),
 ('AUX_OPERATIVO_1','Auxiliar Operativo de Primera',280,1439898.83),
 ('AUX_OPERATIVO_2','Auxiliar Operativo de Segunda',290,1003019.86),
 ('OFICIAL_1','Oficial de Primera',300,1167000.23),
 ('OFICIAL_COMPLETO_TALLER','Oficial Completo de Taller',310,1106537.17),
 ('OFICIAL','Oficial',320,1052031.25),
 ('MEDIO_OFICIAL','Medio Oficial',330,993812.37),
 ('OFICIAL_GOMERO','Oficial Gomero',340,1052031.25),
 ('MEDIO_OFICIAL_GOMERO','Medio Oficial Gomero',350,993812.37),
 ('LAVADOR_ENGRASADOR_TALLER','Lavadores, Engrasadores y Ayudantes de Taller',360,993812.37),
 ('ADMIN_1','Personal Administrativo - Primera Categoría',370,1042730.29),
 ('ADMIN_2','Personal Administrativo - Segunda Categoría',380,1003019.86),
 ('ADMIN_3','Personal Administrativo - Tercera Categoría',390,966217.77),
 ('ADMIN_4','Personal Administrativo - Cuarta Categoría',400,947834.73),
 ('MAESTRANZA_SERENO','Maestranza y/o Serenos',410,947834.73),
 ('AUX_CLEARING_1','Auxiliar Operativo de Primera de Clearing y Correo Privado',420,1044645.95),
 ('AUX_CLEARING_2','Auxiliar Operativo de Segunda de Clearing y Correo Privado',430,994236.37)
)
UPDATE public.cct_categoria c SET activa=false
WHERE c.cct_numero='40/89' AND NOT EXISTS (SELECT 1 FROM datos d WHERE d.nombre=c.nombre);

WITH datos(codigo,nombre,orden) AS (VALUES
 ('CONDUCTOR_1','Conductor de Primera Categoría',10),('CONDUCTOR_2','Conductor de Segunda Categoría',20),
 ('CONDUCTOR_3_FLETES','Conductor de Tercera Categoría (Fletes al instante)',30),
 ('GRUA_HASTA_10','Conductores de grúas de hasta 10 toneladas y operadores de autoelevadores',40),
 ('GRUA_10_20','Conductores de grúas de más de 10 y hasta 20 toneladas',50),('GRUA_20_35','Conductores de grúas de más de 20 y hasta 35 toneladas',60),
 ('GRUA_35_45','Conductores de grúas de más de 35 y hasta 45 toneladas',70),('GRUA_45_55','Conductores de grúas de más de 45 y hasta 55 toneladas',80),
 ('GRUA_55_70','Conductores de grúas de más de 55 y hasta 70 toneladas',90),('GRUA_70_90','Conductores de grúas de más de 70 y hasta 90 toneladas',100),
 ('GRUA_90_110','Conductores de grúas de más de 90 y hasta 110 toneladas',110),('GRUA_110_140','Conductores de grúas de más de 110 y hasta 140 toneladas',120),
 ('GRUA_140_170','Conductores de grúas de más de 140 y hasta 170 toneladas',130),('GRUA_170_300','Conductores de grúas de más de 170 y hasta 300 toneladas',140),
 ('GRUA_MAS_300','Conductores de grúas de más de 300 toneladas',150),('ENCARGADO','Encargado',160),
 ('RECIBIDOR_GUIAS','Recibidor y/o Clasificador de Guías',170),('OPERARIO_ESPECIALIZADO','Operarios Especializados',180),
 ('RECOLECTOR_RESIDUOS','Recolectores de Residuo y Limpieza',190),('PEON','Peones',200),
 ('PEON_BARRIDO','Peones Generales de Barrido y Limpieza',210),('OPERADOR_SERVICIOS','Operador de Servicios',220),
 ('DISTRIBUIDOR_DOMICILIARIO','Distribuidor Domiciliario',230),('AYUDANTE_MAYOR_18','Ayudantes Mayores de 18 Años',240),
 ('CHOFER_BLINDADO','Chofer de Camión Blindado',250),('CHOFER_CON_FIRMA','Chofer con Firma',260),
 ('CUSTODIA_CAUDALES','Custodia de Camión de Caudales',270),('AUX_OPERATIVO_1','Auxiliar Operativo de Primera',280),
 ('AUX_OPERATIVO_2','Auxiliar Operativo de Segunda',290),('OFICIAL_1','Oficial de Primera',300),
 ('OFICIAL_COMPLETO_TALLER','Oficial Completo de Taller',310),('OFICIAL','Oficial',320),('MEDIO_OFICIAL','Medio Oficial',330),
 ('OFICIAL_GOMERO','Oficial Gomero',340),('MEDIO_OFICIAL_GOMERO','Medio Oficial Gomero',350),
 ('LAVADOR_ENGRASADOR_TALLER','Lavadores, Engrasadores y Ayudantes de Taller',360),
 ('ADMIN_1','Personal Administrativo - Primera Categoría',370),('ADMIN_2','Personal Administrativo - Segunda Categoría',380),
 ('ADMIN_3','Personal Administrativo - Tercera Categoría',390),('ADMIN_4','Personal Administrativo - Cuarta Categoría',400),
 ('MAESTRANZA_SERENO','Maestranza y/o Serenos',410),
 ('AUX_CLEARING_1','Auxiliar Operativo de Primera de Clearing y Correo Privado',420),
 ('AUX_CLEARING_2','Auxiliar Operativo de Segunda de Clearing y Correo Privado',430)
)
INSERT INTO public.cct_categoria
 (id,cct_numero,codigo,nombre,orden,activa,fuente,estado_fuente,is_verified,version)
SELECT gen_random_uuid(),'40/89',codigo,nombre,orden,true,
 'CCT 40/89 edición FedCam mayo 2022; Planilla salarial 8/26',
 'PUBLICADA_POR_PARTE_SIGNATARIA',true,1 FROM datos
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
 nombre=EXCLUDED.nombre,orden=EXCLUDED.orden,activa=true,fuente=EXCLUDED.fuente,
 estado_fuente=EXCLUDED.estado_fuente,is_verified=true;

INSERT INTO public.cct_regla_estructural
 (id,cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,estado_fuente,is_verified,version,activa)
VALUES
 (gen_random_uuid(),'40/89','MODALIDAD_MENSUAL_DIARIA','modalidad','La planilla publica salario mínimo mensual y jornal diario equivalente.','6.1.1 y 6.2.13',
  '{"unidad_principal":"MENSUAL","jornal_divisor":24}',
  'Planilla FedCam 8/26','PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true),
 (gen_random_uuid(),'40/89','COEFICIENTES_TERRITORIALES','zona','Escala base, coeficiente 1,20 al sur del Río Colorado/Barrancas hasta Santa Cruz y 1,40 al sur del Río Santa Cruz.','Planilla 8/26 notas 1 y 2',
  '{"zonas":["BASE","COEF_1_20","COEF_1_40"],"requiere_domicilio_laboral":true,"no_inferir_sin_confirmacion":true}',
  'Planilla FedCam 8/26 hoja 1','PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true),
 (gen_random_uuid(),'40/89','ANTIGUEDAD','antiguedad','Antigüedad del 1% por año sobre todos los conceptos remunerativos.','6.1.5',
  '{"porcentaje_por_anio":0.01,"base":"todos_conceptos_remunerativos"}',
  'CCT 40/89 item 6.1.5; Planilla FedCam 8/26 hoja 2','PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true),
 (gen_random_uuid(),'40/89','VIATICOS_Y_KILOMETRAJE','novedad_especifica','Comida, viático especial, pernoctada, kilómetros, permanencia, cruce de frontera y Tierra del Fuego requieren novedades y valores del período.','4.1.12 a 4.2.17',
  '{"requiere_motor_especifico":true,"bloquear_si_aplica_y_falta_detalle":true}',
  'CCT 40/89; Planilla FedCam 8/26 hoja 2','PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true),
 (gen_random_uuid(),'40/89','RAMAS_ESPECIALES','rama','Las ramas de residuos, caudales, combustibles, sustancias peligrosas, petróleo, clearing, mudanzas, logística y otras poseen adicionales propios.','Capítulo 5 y concordantes',
  '{"requiere_rama_empleado":true,"bloquear_rama_sin_regla_modelada":true}',
  'CCT 40/89 edición FedCam mayo 2022; Planilla 8/26 hoja 2','PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
 descripcion=EXCLUDED.descripcion,articulo=EXCLUDED.articulo,configuracion=EXCLUDED.configuracion,
 fuente=EXCLUDED.fuente,estado_fuente=EXCLUDED.estado_fuente,is_verified=true,activa=true;

-- Reemplazo idempotente exclusivo de agosto 2026.
DELETE FROM public.escala_salarial
WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01' AND version=1;

WITH base(categoria,basico) AS (VALUES
 ('Conductor de Primera Categoría',1047830.65),('Conductor de Segunda Categoría',1029157.90),
 ('Conductor de Tercera Categoría (Fletes al instante)',1010466.26),
 ('Conductores de grúas de hasta 10 toneladas y operadores de autoelevadores',1066511.23),
 ('Conductores de grúas de más de 10 y hasta 20 toneladas',1173162.35),('Conductores de grúas de más de 20 y hasta 35 toneladas',1220088.84),
 ('Conductores de grúas de más de 35 y hasta 45 toneladas',1268892.39),('Conductores de grúas de más de 45 y hasta 55 toneladas',1319648.09),
 ('Conductores de grúas de más de 55 y hasta 70 toneladas',1385630.49),('Conductores de grúas de más de 70 y hasta 90 toneladas',1454912.01),
 ('Conductores de grúas de más de 90 y hasta 110 toneladas',1527657.61),('Conductores de grúas de más de 110 y hasta 140 toneladas',1604040.49),
 ('Conductores de grúas de más de 140 y hasta 170 toneladas',1684242.51),('Conductores de grúas de más de 170 y hasta 300 toneladas',1768454.64),
 ('Conductores de grúas de más de 300 toneladas',1909931.01),('Encargado',984812.93),('Recibidor y/o Clasificador de Guías',975419.30),
 ('Operarios Especializados',966217.77),('Recolectores de Residuo y Limpieza',966217.77),('Peones',956996.33),
 ('Peones Generales de Barrido y Limpieza',956996.33),('Operador de Servicios',1114933.30),('Distribuidor Domiciliario',1014804.90),
 ('Ayudantes Mayores de 18 Años',938655.67),('Chofer de Camión Blindado',1126550.90),('Chofer con Firma',1209889.63),
 ('Custodia de Camión de Caudales',976709.64),('Auxiliar Operativo de Primera',1439898.83),('Auxiliar Operativo de Segunda',1003019.86),
 ('Oficial de Primera',1167000.23),('Oficial Completo de Taller',1106537.17),('Oficial',1052031.25),('Medio Oficial',993812.37),
 ('Oficial Gomero',1052031.25),('Medio Oficial Gomero',993812.37),('Lavadores, Engrasadores y Ayudantes de Taller',993812.37),
 ('Personal Administrativo - Primera Categoría',1042730.29),('Personal Administrativo - Segunda Categoría',1003019.86),
 ('Personal Administrativo - Tercera Categoría',966217.77),('Personal Administrativo - Cuarta Categoría',947834.73),
 ('Maestranza y/o Serenos',947834.73),('Auxiliar Operativo de Primera de Clearing y Correo Privado',1044645.95),
 ('Auxiliar Operativo de Segunda de Clearing y Correo Privado',994236.37)
), zonas(zona,coeficiente) AS (VALUES ('BASE',1.00),('COEF_1_20',1.20),('COEF_1_40',1.40))
INSERT INTO public.escala_salarial
 (id,cct_numero,categoria,zona,basico,basico_puro,adicional_zona,unidad_escala,
  valid_from,valid_to,fuente,estado_fuente,is_verified,provisoria,habilitada_liquidacion,version)
SELECT gen_random_uuid(),'40/89',b.categoria,z.zona,round(b.basico*z.coeficiente,2),b.basico,
       round(b.basico*(z.coeficiente-1),2),'MENSUAL',DATE '2026-08-01',DATE '2026-08-31',
       'Planilla salarial FedCam 8/26; Acuerdo 13/03/2026 homologado por Disposición 455/2026',
       'PUBLICADA_POR_PARTE_SIGNATARIA',true,false,false,1
FROM base b CROSS JOIN zonas z;

INSERT INTO public.cct_paquete_version
 (cct_numero,paquete_version,hash_sha256,estado,resumen,fuente_manifest)
VALUES ('40/89','2026.08-estructura-hoja1-v1',
 md5('CAMIONEROS-40/89-2026-08-HOJA1')||md5('1AJOH-80-6202-98/04-SORENOIMAC'),
 'BLOQUEADO','{"categorias":43,"zonas":3,"escalas":129,"reglas":5,"motor":"BLOQUEADO","pendiente":"cartilla ampliatoria y motor por rama"}'::jsonb,
 'Planilla 8/26 FedCam/FADEEAC; Disposición homologatoria 455/2026')
ON CONFLICT (cct_numero,paquete_version) DO UPDATE SET
 hash_sha256=EXCLUDED.hash_sha256,estado=EXCLUDED.estado,resumen=EXCLUDED.resumen,
 fuente_manifest=EXCLUDED.fuente_manifest,instalado_at=now();

COMMIT;
