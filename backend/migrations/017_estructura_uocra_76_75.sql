-- Estructura permanente verificada del regimen UOCRA CCT 76/75.
-- No incorpora jornales, sumas variables, alicuotas sindicales ni boletas.
BEGIN;

UPDATE public.cct
SET nombre = 'Construcción', sindicato = 'UOCRA', activo = true
WHERE numero = '76/75';

-- Retira del padron visible cualquier categoria historica incompleta o con un
-- nombre distinto. No borra escalas ni recibos anteriores.
UPDATE public.cct_categoria
SET activa = false
WHERE cct_numero = '76/75'
  AND nombre NOT IN (
    'Oficial Especializado','Oficial','Medio Oficial','Ayudante','Sereno'
  );

INSERT INTO public.cct_categoria
  (cct_numero,codigo,nombre,orden,activa,fuente,is_verified,version)
VALUES
  ('76/75','OFICIAL_ESPECIALIZADO','Oficial Especializado',10,true,
   'CCT 76/75 y escalas homologadas: https://www.argentina.gob.ar/normativa/nacional/norma-186590/texto',true,1),
  ('76/75','OFICIAL','Oficial',20,true,
   'CCT 76/75 y escalas homologadas: https://www.argentina.gob.ar/normativa/nacional/norma-186590/texto',true,1),
  ('76/75','MEDIO_OFICIAL','Medio Oficial',30,true,
   'CCT 76/75 y escalas homologadas: https://www.argentina.gob.ar/normativa/nacional/norma-186590/texto',true,1),
  ('76/75','AYUDANTE','Ayudante',40,true,
   'CCT 76/75 y escalas homologadas: https://www.argentina.gob.ar/normativa/nacional/norma-186590/texto',true,1),
  ('76/75','SERENO','Sereno',50,true,
   'CCT 76/75 y escalas homologadas: https://www.argentina.gob.ar/normativa/nacional/norma-186590/texto',true,1)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  nombre=EXCLUDED.nombre, orden=EXCLUDED.orden, activa=true,
  fuente=EXCLUDED.fuente, is_verified=EXCLUDED.is_verified;

INSERT INTO public.cct_regla_estructural
  (cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,is_verified,version,activa)
VALUES
  ('76/75','AMBITO_ACTIVIDAD','ambito',
   'Construccion general, obras de ingenieria civil, edificacion, arquitectura y montaje; las ramas con convenio especifico se encuadran por separado.',
   'ambito personal y de actividad',
   '{"actividad_principal":"construccion_general","convenios_especificos_separados":["545/08","577/10"]}',
   'CCT 76/75 y Ley 22.250',true,1,true),
  ('76/75','MODALIDAD_CATEGORIA','modalidad',
   'Oficial Especializado, Oficial, Medio Oficial y Ayudante son jornalizados por hora; Sereno es mensualizado.',
   'escala convencional',
   '{"jornalizados":["Oficial Especializado","Oficial","Medio Oficial","Ayudante"],"mensualizados":["Sereno"]}',
   'Escalas homologadas CCT 76/75: https://www.argentina.gob.ar/normativa/nacional/norma-186590/texto',true,1,true),
  ('76/75','ZONIFICACION','zona',
   'La escala se selecciona por el domicilio efectivo de la obra, no por el domicilio social del empleador.',
   '47',
   '{"campo_determinante":"domicilio_laboral","zonas":{"A":["CABA","Buenos Aires","Catamarca","Chaco","Cordoba","Corrientes","Entre Rios","Formosa","Jujuy","La Rioja","Mendoza","Misiones","Salta","San Juan","San Luis","Santa Fe","Santiago del Estero","Tucuman"],"B":["La Pampa","Neuquen","Rio Negro","Chubut"],"C":["Santa Cruz"],"C_AUSTRAL":["Tierra del Fuego","Antartida Argentina","Islas del Atlantico Sur"]}}',
   'CCT 76/75 art. 47 y escalas homologadas',true,1,true),
  ('76/75','ASISTENCIA_PERFECTA','presentismo',
   'Adicional del 20% sobre el salario basico de la categoria por asistencia perfecta, evaluado por cada quincena y con excepciones convencionales.',
   '52',
   '{"porcentaje":0.20,"base":"salario_basico_categoria","periodicidad":"quincenal","requiere_control_asistencia":true,"no_automatizar_sin_novedades_quincenales":true,"excepciones":["vacaciones","licencias_especiales","examenes","causas_climaticas_o_no_imputables","feriados","funcion_gremial","dia_construccion","accidente_ART"]}',
   'CCT 76/75 art. 52; referencia oficial: https://www.argentina.gob.ar/normativa/nacional/norma-235836/texto',true,1,true),
  ('76/75','FONDO_CESE_LABORAL','fondo_cese',
   'Aporte patronal obligatorio desde el inicio de la relacion: 12% durante el primer ano y 8% desde el segundo ano; reemplaza preaviso e indemnizacion por despido de la LCT.',
   '15-18',
   '{"tramos":[{"desde_mes":1,"hasta_mes":12,"porcentaje":0.12},{"desde_mes":13,"hasta_mes":null,"porcentaje":0.08}],"base":{"incluye":["salarios_basicos","adicionales_convencionales","incrementos_generales","incrementos_voluntarios_sobre_basicos"],"excluye":["SAC"]},"vencimiento":"primeros_15_dias_del_mes_siguiente","cuenta":"especial_a_nombre_del_trabajador","prohibe_pago_directo_salvo_cese_con_periodo_no_vencido":true}',
   'Ley 22.250 arts. 15 a 18: https://www.argentina.gob.ar/normativa/nacional/norma-27238/texto',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  tipo=EXCLUDED.tipo, descripcion=EXCLUDED.descripcion, articulo=EXCLUDED.articulo,
  configuracion=EXCLUDED.configuracion, fuente=EXCLUDED.fuente,
  is_verified=EXCLUDED.is_verified, activa=true;

COMMIT;
