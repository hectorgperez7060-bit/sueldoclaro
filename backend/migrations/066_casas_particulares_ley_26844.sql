-- Personal de Casas Particulares · Ley 26.844 · Resolución CNTCP 6/2026.
-- Escalas oficiales agosto-diciembre 2026 y valores ARCA desde julio 2026.
BEGIN;

ALTER TABLE public.escala_salarial
  ADD COLUMN IF NOT EXISTS valor_hora numeric(18,2);
ALTER TABLE public.escala_salarial DROP CONSTRAINT IF EXISTS ck_escala_salarial_unidad;
ALTER TABLE public.escala_salarial ADD CONSTRAINT ck_escala_salarial_unidad
  CHECK (unidad_escala IN ('HORA','MENSUAL','MIXTA'));
ALTER TABLE public.novedad_mensual
  ADD COLUMN IF NOT EXISTS casas_particulares_detalle jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE public.novedad_mensual DROP CONSTRAINT IF EXISTS casas_particulares_detalle_objeto;
ALTER TABLE public.novedad_mensual ADD CONSTRAINT casas_particulares_detalle_objeto
  CHECK (jsonb_typeof(casas_particulares_detalle)='object');

INSERT INTO public.cct
  (id,numero,nombre,sindicato,cuota_sindical_pct,antiguedad_pct_por_anio,
   presentismo_divisor,divisor_horas,aplica_presentismo,aplica_cuota_sindical,activo)
VALUES
  (gen_random_uuid(),'LEY 26844',
   'Régimen Especial de Contrato de Trabajo para el Personal de Casas Particulares',
   '',0,0.01,12,192,false,false,true)
ON CONFLICT (numero) DO UPDATE SET
  nombre=EXCLUDED.nombre, sindicato=EXCLUDED.sindicato,
  antiguedad_pct_por_anio=EXCLUDED.antiguedad_pct_por_anio,
  divisor_horas=EXCLUDED.divisor_horas, aplica_presentismo=false,
  aplica_cuota_sindical=false, activo=true;

UPDATE public.cct_categoria SET activa=false WHERE cct_numero='LEY 26844';
INSERT INTO public.cct_categoria
  (id,cct_numero,codigo,nombre,orden,activa,fuente,estado_fuente,is_verified,version)
VALUES
  (gen_random_uuid(),'LEY 26844','SUP_CON_RETIRO','Supervisor/a · Con retiro',10,true,
   'Argentina.gob.ar — Modalidades de trabajo para casas particulares','VERIFICADA_OFICIAL',true,1),
  (gen_random_uuid(),'LEY 26844','SUP_SIN_RETIRO','Supervisor/a · Sin retiro',20,true,
   'Argentina.gob.ar — Modalidades de trabajo para casas particulares','VERIFICADA_OFICIAL',true,1),
  (gen_random_uuid(),'LEY 26844','ESP_CON_RETIRO','Personal para tareas específicas · Con retiro',30,true,
   'Argentina.gob.ar — Modalidades de trabajo para casas particulares','VERIFICADA_OFICIAL',true,1),
  (gen_random_uuid(),'LEY 26844','ESP_SIN_RETIRO','Personal para tareas específicas · Sin retiro',40,true,
   'Argentina.gob.ar — Modalidades de trabajo para casas particulares','VERIFICADA_OFICIAL',true,1),
  (gen_random_uuid(),'LEY 26844','CASEROS','Caseros/as · Sin retiro',50,true,
   'Argentina.gob.ar — Modalidades de trabajo para casas particulares','VERIFICADA_OFICIAL',true,1),
  (gen_random_uuid(),'LEY 26844','CUIDADO_CON_RETIRO','Asistencia y cuidado de personas · Con retiro',60,true,
   'Argentina.gob.ar — Modalidades de trabajo para casas particulares','VERIFICADA_OFICIAL',true,1),
  (gen_random_uuid(),'LEY 26844','CUIDADO_SIN_RETIRO','Asistencia y cuidado de personas · Sin retiro',70,true,
   'Argentina.gob.ar — Modalidades de trabajo para casas particulares','VERIFICADA_OFICIAL',true,1),
  (gen_random_uuid(),'LEY 26844','GENERAL_CON_RETIRO','Personal para tareas generales · Con retiro',80,true,
   'Argentina.gob.ar — Modalidades de trabajo para casas particulares','VERIFICADA_OFICIAL',true,1),
  (gen_random_uuid(),'LEY 26844','GENERAL_SIN_RETIRO','Personal para tareas generales · Sin retiro',90,true,
   'Argentina.gob.ar — Modalidades de trabajo para casas particulares','VERIFICADA_OFICIAL',true,1)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  nombre=EXCLUDED.nombre, orden=EXCLUDED.orden, activa=true, fuente=EXCLUDED.fuente,
  estado_fuente=EXCLUDED.estado_fuente, is_verified=true;

INSERT INTO public.cct_regla_estructural
  (id,cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,
   estado_fuente,is_verified,version,activa)
VALUES
  (gen_random_uuid(),'LEY 26844','JORNADA','jornada',
   'Ocho horas diarias o cuarenta y ocho semanales, máximo nueve diarias','14',
   '{"completa_horas":48,"maximo_diario":9}',
   'Ley 26.844 art. 14','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','MODALIDAD_SALARIAL','salario',
   'Menos de 24 horas semanales: valor hora; desde 24 y menos de 48: mensual proporcional; 48: mensual completo','18',
   '{"corte_valor_hora":24,"jornada_completa":48}',
   'Argentina.gob.ar — Escala salarial de Casas Particulares','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','ANTIGUEDAD','antiguedad',
   'Uno por ciento por año; cómputo desde el 1 de septiembre de 2020 sin retroactividad','Resoluciones CNTCP',
   '{"porcentaje_anual":0.01,"computo_desde":"2020-09-01"}',
   'Argentina.gob.ar — Sueldo de Casas Particulares','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','HORAS_EXTRA','hora_extra',
   'Recargo 50% en días comunes y 100% sábados después de las 13, domingos y feriados','25',
   '{"comun":0.50,"sabado_13_domingo_feriado":1.00}',
   'Ley 26.844 art. 25','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','LICENCIAS','licencias',
   'Vacaciones, enfermedad, maternidad y licencias especiales del régimen','29-39',
   '{"vacaciones_dias":[14,21,28,35],"enfermedad_meses":[3,6],"maternidad_dias":90}',
   'Ley 26.844 arts. 29 a 39','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','ZONIFICACION','zona',
   'Adicional del 31% por zona desfavorable','Anexos Res. CNTCP 6/2026',
   '{"zonas":["BASE","DESFAVORABLE"],"porcentaje":0.31,"campo_determinante":"domicilio_laboral","resolucion":"cct_zona_vigencia","localidades_excepcion":[{"provincia":"Buenos Aires","localidades":["Patagones","Partido de Patagones","Carmen de Patagones"],"zona":"DESFAVORABLE"}]}',
   'Resolución CNTCP 6/2026, anexos 1 a 5','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','APORTES_ARCA','seguridad_social',
   'Importes fijos según horas semanales y condición: activo, adolescente o jubilado','Ley 26.844',
   '{"tramos":["MENOS_12","12_A_15","16_O_MAS"],"condiciones":["ACTIVO","ADOLESCENTE_16_17","JUBILADO"],"formulario":"F102RT"}',
   'Argentina.gob.ar — Aportes y contribuciones para casas particulares','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','CATEGORIA_MULTIPLE','encuadramiento',
   'Si realiza tareas de más de una categoría corresponde la mejor remunerada','18',
   '{"criterio":"categoria_mejor_remunerada"}',
   'Argentina.gob.ar — Salario de Casas Particulares','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','TRABAJO_ADOLESCENTE','proteccion',
   'Desde 16 y hasta 18 años: máximo 6 horas diarias y 36 semanales; prohibida modalidad sin retiro','9-13',
   '{"edad_minima":16,"maximo_diario":6,"maximo_semanal":36,"sin_retiro_prohibido":true}',
   'Ley 26.844 arts. 9 a 13','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','SAC','sac',
   'Cada cuota es el 50% de la mayor remuneración mensual del semestre; proporcional si corresponde','26-28',
   '{"porcentaje_mejor_remuneracion":0.50,"cuotas":[6,12]}',
   'Ley 26.844 arts. 26 a 28','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','VACACIONES_SIN_RETIRO','vacaciones',
   'Sustitución de habitación y manutención no inferior al 30% del salario diario en los casos legales','32',
   '{"adicional_minimo_diario":0.30}',
   'Ley 26.844 art. 32','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','PERIODO_PRUEBA','contrato',
   'Período de prueba de seis meses para contrato por tiempo indeterminado','7',
   '{"meses":6,"vigencia_desde":"2026-03-06"}',
   'Ley 26.844 art. 7, texto según Ley 27.802','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','PREAVISO','extincion',
   'Trabajador: 10 días; empleador: 10 días con antigüedad menor a un año y 30 días si es superior','42-45',
   '{"trabajador_dias":10,"empleador_menor_un_anio_dias":10,"empleador_mayor_un_anio_dias":30,"integra_mes_despido":true}',
   'Ley 26.844 arts. 42 a 45','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','INDEMNIZACION_DESPIDO','extincion',
   'Un mes por año o fracción mayor de tres meses, mínimo un mes, sobre la mejor remuneración normal y habitual','48',
   '{"meses_por_anio":1,"fraccion_mayor_meses":3,"minimo_meses":1,"base":"mejor_remuneracion_ultimo_anio"}',
   'Ley 26.844 art. 48; art. 50 derogado por Ley 27.742','VERIFICADA_OFICIAL',true,1,true),
  (gen_random_uuid(),'LEY 26844','RECIBO_ELECTRONICO_ARCA','documentacion',
   'Recibo electrónico emitido por el sistema que determine ARCA','20-24',
   '{"emisor":"ARCA","electronico":true}',
   'Ley 26.844 art. 20, texto según Ley 27.802','VERIFICADA_OFICIAL',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, articulo=EXCLUDED.articulo,
  configuracion=EXCLUDED.configuracion, fuente=EXCLUDED.fuente,
  estado_fuente=EXCLUDED.estado_fuente, is_verified=true, activa=true;

-- Toda provincia debe resolver explícitamente; Buenos Aires es BASE y la
-- excepción del Partido de Patagones se resuelve por localidad en la regla.
WITH provincias(provincia,zona) AS (VALUES
  ('CABA','BASE'),('Buenos Aires','BASE'),('Catamarca','BASE'),('Chaco','BASE'),
  ('Cordoba','BASE'),('Corrientes','BASE'),('Entre Rios','BASE'),('Formosa','BASE'),
  ('Jujuy','BASE'),('La Rioja','BASE'),('Mendoza','BASE'),('Misiones','BASE'),
  ('Salta','BASE'),('San Juan','BASE'),('San Luis','BASE'),('Santa Fe','BASE'),
  ('Santiago del Estero','BASE'),('Tucuman','BASE'),
  ('La Pampa','DESFAVORABLE'),('Neuquen','DESFAVORABLE'),
  ('Rio Negro','DESFAVORABLE'),('Chubut','DESFAVORABLE'),
  ('Santa Cruz','DESFAVORABLE'),('Tierra del Fuego','DESFAVORABLE')
)
INSERT INTO public.cct_zona_vigencia
  (id,cct_numero,provincia,zona,valid_from,valid_to,fuente,estado_fuente,is_verified,version)
SELECT gen_random_uuid(),'LEY 26844',provincia,zona,DATE '2026-08-01',NULL,
  'Resolución CNTCP 6/2026 · zona desfavorable 31%',
  'VERIFICADA_OFICIAL',true,1
FROM provincias
ON CONFLICT (cct_numero,provincia,valid_from,version) DO UPDATE SET
  zona=EXCLUDED.zona, fuente=EXCLUDED.fuente,
  estado_fuente=EXCLUDED.estado_fuente, is_verified=true;

-- Una fila contiene las dos unidades que la resolución publica juntas.
DELETE FROM public.escala_salarial
WHERE cct_numero='LEY 26844' AND valid_from BETWEEN DATE '2026-08-01' AND DATE '2026-12-01';

DO $$
DECLARE
  periodo record;
  fila jsonb;
  zona_item text;
  multiplicador numeric;
  hasta date;
  fuente_oficial text := 'Resolución CNTCP 6/2026 · BORA 03/09/2026 · Anexos 1 a 5';
BEGIN
  FOR periodo IN SELECT * FROM (VALUES
    (DATE '2026-08-01', '[
      {"c":"Supervisor/a · Con retiro","h":4523.11,"m":564246.70},
      {"c":"Supervisor/a · Sin retiro","h":4920.89,"m":624313.90},
      {"c":"Personal para tareas específicas · Con retiro","h":4303.50,"m":526829.56},
      {"c":"Personal para tareas específicas · Sin retiro","h":4684.53,"m":582283.26},
      {"c":"Caseros/as · Sin retiro","h":4072.38,"m":514903.51},
      {"c":"Asistencia y cuidado de personas · Con retiro","h":4072.38,"m":514903.51},
      {"c":"Asistencia y cuidado de personas · Sin retiro","h":4520.15,"m":569593.41},
      {"c":"Personal para tareas generales · Con retiro","h":3804.66,"m":466756.24},
      {"c":"Personal para tareas generales · Sin retiro","h":4072.38,"m":514903.51}
    ]'::jsonb),
    (DATE '2026-09-01', '[
      {"c":"Supervisor/a · Con retiro","h":4645.33,"m":579493.14},
      {"c":"Supervisor/a · Sin retiro","h":5049.58,"m":640641.55},
      {"c":"Personal para tareas específicas · Con retiro","h":4422.54,"m":541402.49},
      {"c":"Personal para tareas específicas · Sin retiro","h":4809.80,"m":597854.36},
      {"c":"Caseros/as · Sin retiro","h":4185.94,"m":529261.78},
      {"c":"Asistencia y cuidado de personas · Con retiro","h":4185.94,"m":529261.78},
      {"c":"Asistencia y cuidado de personas · Sin retiro","h":4641.90,"m":584936.09},
      {"c":"Personal para tareas generales · Con retiro","h":3914.64,"m":480247.85},
      {"c":"Personal para tareas generales · Sin retiro","h":4185.94,"m":529261.78}
    ]'::jsonb),
    (DATE '2026-10-01', '[
      {"c":"Supervisor/a · Con retiro","h":4805.82,"m":599514.52},
      {"c":"Supervisor/a · Sin retiro","h":5215.59,"m":661702.46},
      {"c":"Personal para tareas específicas · Con retiro","h":4580.80,"m":560776.33},
      {"c":"Personal para tareas específicas · Sin retiro","h":4973.38,"m":618187.89},
      {"c":"Caseros/as · Sin retiro","h":4337.53,"m":548429.23},
      {"c":"Asistencia y cuidado de personas · Con retiro","h":4337.53,"m":548429.23},
      {"c":"Asistencia y cuidado de personas · Sin retiro","h":4801.52,"m":605050.00},
      {"c":"Personal para tareas generales · Con retiro","h":4064.08,"m":498582.06},
      {"c":"Personal para tareas generales · Sin retiro","h":4337.53,"m":548429.23}
    ]'::jsonb),
    (DATE '2026-11-01', '[
      {"c":"Supervisor/a · Con retiro","h":4928.28,"m":614791.27},
      {"c":"Supervisor/a · Sin retiro","h":5344.33,"m":678036.40},
      {"c":"Personal para tareas específicas · Con retiro","h":4700.21,"m":575394.53},
      {"c":"Personal para tareas específicas · Sin retiro","h":5098.84,"m":633782.08},
      {"c":"Caseros/as · Sin retiro","h":4451.49,"m":562837.52},
      {"c":"Asistencia y cuidado de personas · Con retiro","h":4451.49,"m":562837.52},
      {"c":"Asistencia y cuidado de personas · Sin retiro","h":4923.50,"m":620420.85},
      {"c":"Personal para tareas generales · Con retiro","h":4174.62,"m":512142.96},
      {"c":"Personal para tareas generales · Sin retiro","h":4451.49,"m":562837.52}
    ]'::jsonb),
    (DATE '2026-12-01', '[
      {"c":"Supervisor/a · Con retiro","h":5007.14,"m":624627.93},
      {"c":"Supervisor/a · Sin retiro","h":5429.84,"m":688884.98},
      {"c":"Personal para tareas específicas · Con retiro","h":4775.41,"m":584600.84},
      {"c":"Personal para tareas específicas · Sin retiro","h":5180.42,"m":643922.59},
      {"c":"Caseros/as · Sin retiro","h":4522.71,"m":571842.92},
      {"c":"Asistencia y cuidado de personas · Con retiro","h":4522.71,"m":571842.92},
      {"c":"Asistencia y cuidado de personas · Sin retiro","h":5002.28,"m":630347.58},
      {"c":"Personal para tareas generales · Con retiro","h":4241.42,"m":520337.24},
      {"c":"Personal para tareas generales · Sin retiro","h":4522.71,"m":571842.92}
    ]'::jsonb)
  ) AS x(desde, datos)
  LOOP
    hasta := CASE WHEN periodo.desde=DATE '2026-12-01' THEN NULL
                  ELSE (periodo.desde + INTERVAL '1 month - 1 day')::date END;
    FOR fila IN SELECT value FROM jsonb_array_elements(periodo.datos)
    LOOP
      FOREACH zona_item IN ARRAY ARRAY['BASE','DESFAVORABLE'] LOOP
        multiplicador := CASE WHEN zona_item='DESFAVORABLE' THEN 1.31 ELSE 1 END;
        INSERT INTO public.escala_salarial
          (id,cct_numero,categoria,basico,valor_hora,valid_from,valid_to,
           fuente,estado_fuente,is_verified,version,provisoria,zona,
           unidad_escala,habilitada_liquidacion)
        VALUES
          (gen_random_uuid(),'LEY 26844',fila->>'c',
           round((fila->>'m')::numeric*multiplicador,2),
           round((fila->>'h')::numeric*multiplicador,2),
           periodo.desde,hasta,fuente_oficial,'VERIFICADA_OFICIAL',true,1,false,
           zona_item,'MIXTA',true);
      END LOOP;
    END LOOP;
  END LOOP;
END $$;

-- Suma extraordinaria no remunerativa pagada en agosto de 2026.
DELETE FROM public.parametro_legal
WHERE cct_numero='LEY 26844' AND codigo LIKE 'CP_SUMA_NR_%';
INSERT INTO public.parametro_legal
  (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,
   is_verified,version,cct_numero,incidencias)
VALUES
  (gen_random_uuid(),'CP_SUMA_NR_MENOS_12',8000,'ARS','variable',DATE '2026-08-01',DATE '2026-08-31',
   'Resolución CNTCP 6/2026 art. 3','VERIFICADA_OFICIAL',true,1,'LEY 26844','{"tramo_horas":"MENOS_12","tipo":"suma_no_remunerativa"}'),
  (gen_random_uuid(),'CP_SUMA_NR_12_A_15',11500,'ARS','variable',DATE '2026-08-01',DATE '2026-08-31',
   'Resolución CNTCP 6/2026 art. 3','VERIFICADA_OFICIAL',true,1,'LEY 26844','{"tramo_horas":"12_A_15","tipo":"suma_no_remunerativa"}'),
  (gen_random_uuid(),'CP_SUMA_NR_16_O_MAS',20000,'ARS','variable',DATE '2026-08-01',DATE '2026-08-31',
   'Resolución CNTCP 6/2026 art. 3','VERIFICADA_OFICIAL',true,1,'LEY 26844','{"tramo_horas":"16_O_MAS","tipo":"suma_no_remunerativa"}');

-- F.102/RT: aporte del trabajador, contribución patronal y cuota ART.
DELETE FROM public.parametro_legal
WHERE cct_numero='LEY 26844' AND codigo LIKE 'CP_ARCA_%';
DO $$
DECLARE fila record; componente record;
BEGIN
  FOR fila IN SELECT * FROM (VALUES
    ('ACTIVO','MENOS_12',2084.85,729.90,7273.89),
    ('ACTIVO','12_A_15',3863.30,1459.48,10535.18),
    ('ACTIVO','16_O_MAS',25694.55,2128.79,15259.36),
    ('ADOLESCENTE_16_17','MENOS_12',2084.85,0,7273.89),
    ('ADOLESCENTE_16_17','12_A_15',3863.30,0,10535.18),
    ('ADOLESCENTE_16_17','16_O_MAS',25694.55,0,15259.36),
    ('JUBILADO','MENOS_12',0,729.90,7273.89),
    ('JUBILADO','12_A_15',0,1459.48,10535.18),
    ('JUBILADO','16_O_MAS',0,2128.79,15259.36)
  ) AS x(condicion,tramo,aporte,contrib,art)
  LOOP
    FOR componente IN SELECT * FROM (VALUES
      ('APORTE',fila.aporte),('CONTRIB',fila.contrib),('ART',fila.art)
    ) AS y(nombre,importe)
    LOOP
      INSERT INTO public.parametro_legal
        (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,
         is_verified,version,cct_numero,incidencias)
      VALUES
        (gen_random_uuid(),
         'CP_ARCA_'||componente.nombre||'_'||fila.condicion||'_'||fila.tramo,
         componente.importe,'ARS','variable',DATE '2026-07-01',NULL,
         'Argentina.gob.ar — Montos a pagar Casas Particulares · período julio 2026',
         'VERIFICADA_OFICIAL',true,1,'LEY 26844',
         jsonb_build_object('condicion',fila.condicion,'tramo_horas',fila.tramo,
                            'componente',componente.nombre,'formulario','F102RT'));
    END LOOP;
  END LOOP;
END $$;

COMMIT;
