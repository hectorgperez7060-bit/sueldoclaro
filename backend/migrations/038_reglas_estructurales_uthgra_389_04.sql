-- UTHGRA–FEHGRA CCT 389/04 · reglas permanentes verificadas.
-- No contiene escalas ni valores temporales del acuerdo 2026/2027.
-- Fuente oficial: texto del CCT publicado por UTHGRA.
-- https://www.uthgra.org.ar/wp-content/uploads/2016/08/ConvFEHGRA.pdf

BEGIN;

INSERT INTO public.cct_regla_estructural
  (id,cct_numero,codigo,tipo,descripcion,articulo,configuracion,
   fuente,estado_fuente,is_verified,version,activa)
VALUES
 (gen_random_uuid(),'389/04','AMBITO_TERRITORIAL','ambito',
  'Aplicación nacional con exclusión expresa de la Provincia de Tucumán.',
  'SEGUNDO',
  '{"territorio":"ARGENTINA","exclusiones":["TUCUMAN"]}'::jsonb,
  'Acuerdo UTHGRA-FEHGRA 24/07/2026, cláusula OCTAVO A; CCT 389/04',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','MATRIZ_NIVEL_ESTABLECIMIENTO','encuadramiento',
  'El básico resulta del nivel profesional y de la clase/categoría I a V del establecimiento.',
  '10.1 y 11.1',
  '{"entradas_obligatorias":["nivel_profesional","clase_establecimiento"],"niveles":[0,1,2,3,4,5,6,7],"clases":["I","II","III","IV","V"],"bloquea_sin_dato":true}'::jsonb,
  'CCT 389/04 oficial UTHGRA, págs. 18 a 22',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','TAREAS_POR_NIVEL','encuadramiento',
  'La tarea efectiva determina el nivel profesional; incluye alojamiento integral, residencial y gastronomía.',
  '10.1',
  '{"sectores":["ALOJAMIENTO_INTEGRAL","ALOJAMIENTO_RESIDENCIAL","GASTRONOMIA"],"niveles_documentados":[0,1,2,3,4,5,6,7],"bloquea_sin_tarea":true}'::jsonb,
  'CCT 389/04 oficial UTHGRA, págs. 18 a 20',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','CLASE_ESTABLECIMIENTO','encuadramiento',
  'La actividad, estrellas o categoría comercial se convierten en clase salarial I a V.',
  '11.1',
  '{"I":["ALOJAMIENTO_1_ESTRELLA","HOSPEDAJE_PENSION","RESTAURANTE_D","BAR_C","DESPACHO_SIN_SALON","GASTRONOMICO_D"],"II":["ALOJAMIENTO_2_ESTRELLAS","RESTAURANTE_C","PIZZERIA_CON_SALON","BAR_B","CATERING_C","GASTRONOMICO_C"],"III":["ALOJAMIENTO_3_ESTRELLAS","RESTAURANTE_B","HELADERIA_CON_SALON","CABARET_BOITE_VARIETE","BAR_A","CATERING_B","GASTRONOMICO_B"],"IV":["ALOJAMIENTO_4_ESTRELLAS","RESTAURANTE_A","CATERING_A","GASTRONOMICO_A"],"V":["ALOJAMIENTO_5_ESTRELLAS"],"bloquea_sin_clasificacion":true}'::jsonb,
  'CCT 389/04 oficial UTHGRA, págs. 21 y 22',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','BASE_ADICIONALES','base_calculo',
  'Los adicionales porcentuales se calculan sólo sobre el básico paritario homologado.',
  '11.2.1',
  '{"base":"BASICO_PARITARIO_HOMOLOGADO","excluye":["SUMAS_NO_REMUNERATIVAS","INCREMENTOS_LEGALES_POSTERIORES"]}'::jsonb,
  'CCT 389/04 oficial UTHGRA, art. 11.2.1',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','ANTIGUEDAD_ESCALONADA','antiguedad',
  'Adicional no acumulable según años cumplidos: 1%, 2%, 4%, 5%, 6%, 7%, 8%, 10%, 12% y 14%.',
  '11.3',
  '{"base":"BASICO_PARITARIO_HOMOLOGADO","escalones":[{"desde":1,"hasta":2,"porcentaje":0.01},{"desde":3,"hasta":4,"porcentaje":0.02},{"desde":5,"hasta":6,"porcentaje":0.04},{"desde":7,"hasta":8,"porcentaje":0.05},{"desde":9,"hasta":10,"porcentaje":0.06},{"desde":11,"hasta":12,"porcentaje":0.07},{"desde":13,"hasta":14,"porcentaje":0.08},{"desde":15,"hasta":16,"porcentaje":0.10},{"desde":17,"hasta":18,"porcentaje":0.12},{"desde":19,"porcentaje":0.14}],"acumulable":false}'::jsonb,
  'CCT 389/04 oficial UTHGRA, art. 11.3',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','ALIMENTACION','adicional',
  'Beneficio de alimentación en especie, vales o dinero con tratamiento diferenciado.',
  '11.4',
  '{"referencia":"NIVEL_1_CLASE_I","comida_completa_pct":0.10,"refrigerio_complemento_pct":0.05,"en_especie_no_remunerativo":true,"en_dinero_remunerativo":true,"prorratea_ausencias":true,"excepciones_ausencia":["FERIADOS","VACACIONES","LICENCIAS_LEGALES","LICENCIAS_CCT"]}'::jsonb,
  'CCT 389/04 oficial UTHGRA, art. 11.4',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','ASISTENCIA_PERFECTA','presentismo',
  'Diez por ciento del básico por no registrar inasistencias ni tardanzas.',
  '11.5',
  '{"base":"BASICO_PARITARIO_HOMOLOGADO","porcentaje":0.10,"prorratea_jornada":true,"eximentes":["VACACIONES","LICENCIAS_ART_158_LCT","LICENCIAS_CCT","EXAMENES_MEDICOS_OBLIGATORIOS"]}'::jsonb,
  'CCT 389/04 oficial UTHGRA, art. 11.5',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','COMPLEMENTO_SERVICIO','adicional',
  'Doce por ciento del básico para todo dependiente, cualquiera sea su función o nivel.',
  '11.6',
  '{"base":"BASICO_PARITARIO_HOMOLOGADO","porcentaje":0.12,"aplica_todos":true}'::jsonb,
  'CCT 389/04 oficial UTHGRA, art. 11.6',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','ZONA_FRIA','adicional_zonal',
  'La cuantía debe provenir del convenio zonal, local o regional aplicable.',
  '11.7',
  '{"provincias":["NEUQUEN","RIO_NEGRO","CHUBUT","SANTA_CRUZ","TIERRA_DEL_FUEGO"],"incluye_centros_invierno":true,"requiere_acuerdo_zonal":true,"bloquea_sin_acuerdo":true}'::jsonb,
  'CCT 389/04 oficial UTHGRA, arts. 11.7 y 22.3',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','JORNADA_Y_DESCANSOS','jornada',
  'Jornada completa de ocho horas, jornadas reducidas y descansos convencionales.',
  '8.1 y concordantes',
  '{"horas_diarias_completa":8,"jornada_reducida_min":4,"jornada_reducida_max":7,"descanso_entre_jornadas_horas":12,"franco_semanal_horas":35}'::jsonb,
  'CCT 389/04 oficial UTHGRA, cláusula OCTAVO',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','TAREA_SUPERIOR_TEMPORARIA','tarea',
  'La asignación transitoria de una tarea superior devenga su salario proporcional durante el lapso trabajado.',
  '10.2',
  '{"paga_nivel_superior":true,"proporcional_tiempo":true}'::jsonb,
  'CCT 389/04 oficial UTHGRA, art. 10.2',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','FALLECIMIENTO_SEPELIO','aporte_contribucion',
  'Financiación de asignaciones por fallecimiento y sepelio.',
  '23.1 a 23.3',
  '{"base":"TOTAL_REMUNERACIONES","aporte_trabajador_pct":0.01,"contribucion_empleador_pct":0.01,"destino":"UTHGRA"}'::jsonb,
  'CCT 389/04 oficial UTHGRA, art. 23.3',
  'VERIFICADA_OFICIAL',true,1,true),

 (gen_random_uuid(),'389/04','CUOTA_SINDICAL_AFILIADO','aporte_sindical',
  'Retención de cuota sindical para trabajadores afiliados; debe verificarse su vigencia al período.',
  'VIGESIMO QUINTO',
  '{"porcentaje_texto_original":0.025,"base":"TOTAL_REMUNERACIONES","solo_afiliados":true,"requiere_vigencia_periodo":true}'::jsonb,
  'CCT 389/04 oficial UTHGRA, cláusula VIGESIMO QUINTO',
  'VERIFICADA_OFICIAL',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  tipo=EXCLUDED.tipo,descripcion=EXCLUDED.descripcion,articulo=EXCLUDED.articulo,
  configuracion=EXCLUDED.configuracion,fuente=EXCLUDED.fuente,
  estado_fuente=EXCLUDED.estado_fuente,is_verified=EXCLUDED.is_verified,activa=true;

COMMIT;