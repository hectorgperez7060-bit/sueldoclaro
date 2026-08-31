-- FATFA-COFA/FACAF CCT 659/13 · agosto 2026.
-- Básicos y sumas no remunerativas: publicación oficial FATFA del 28/08/2026.
-- https://fatfa.org.ar/2026/08/28/escala-salarial-agosto-noviembre/
-- El acta fue celebrada el 27/08/2026; hasta contar con homologación publicada,
-- las filas salariales quedan PROVISORIAS y requieren confirmación expresa.
BEGIN;

UPDATE public.cct
SET nombre='Farmacias alcanzadas por FATFA-COFA',
    sindicato='FATFA',
    antiguedad_pct_por_anio=0,
    aplica_presentismo=false,
    aplica_cuota_sindical=false,
    activo=true
WHERE numero='659/13';

INSERT INTO public.cct_regla_estructural
  (id,cct_numero,codigo,tipo,descripcion,articulo,configuracion,
   fuente,estado_fuente,is_verified,version,activa)
VALUES
 (gen_random_uuid(),'659/13','ANTIGUEDAD_ESCALONADA','antiguedad',
  'Escalafón no lineal sobre el sueldo básico según años cumplidos.',
  '15',
  '{"base":"BASICO_CATEGORIA","escalones":[{"desde":1,"porcentaje":0.07},{"desde":2,"porcentaje":0.09},{"desde":3,"porcentaje":0.11},{"desde":4,"porcentaje":0.13},{"desde":5,"porcentaje":0.15},{"desde":6,"porcentaje":0.17},{"desde":7,"porcentaje":0.19},{"desde":8,"porcentaje":0.21},{"desde":9,"porcentaje":0.23},{"desde":10,"porcentaje":0.25},{"desde":11,"porcentaje":0.27},{"desde":12,"porcentaje":0.29},{"desde":13,"porcentaje":0.31},{"desde":14,"porcentaje":0.33},{"desde":15,"porcentaje":0.35},{"desde":16,"porcentaje":0.37},{"desde":17,"porcentaje":0.39},{"desde":18,"porcentaje":0.41},{"desde":19,"porcentaje":0.43},{"desde":20,"porcentaje":0.45},{"desde":25,"porcentaje":0.50}],"acumulable":false}'::jsonb,
  'CCT 659/13 homologado por Resolución ST 94/2013, art. 15',
  'VERIFICADA_OFICIAL',true,1,true),
 (gen_random_uuid(),'659/13','ZONAS_FRIAS','adicional_zonal',
  'Adicional no remunerativo sobre haberes convencionales más antigüedad.',
  '21',
  '{"RIO_NEGRO":0.27,"NEUQUEN":0.27,"CHUBUT":0.30,"SANTA_CRUZ":0.30,"TIERRA_DEL_FUEGO":0.30,"ISLAS_ATLANTICO_SUR":0.30,"naturaleza":"NO_REMUNERATIVA"}'::jsonb,
  'CCT 659/13 homologado por Resolución ST 94/2013, art. 21',
  'VERIFICADA_OFICIAL',true,1,true),
 (gen_random_uuid(),'659/13','FALLA_CAJA','adicional',
  'Fondo compensador para tarea permanente de cajero: 20% del básico.',
  '23',
  '{"base":"BASICO_CATEGORIA","porcentaje":0.20,"naturaleza":"NO_REMUNERATIVA","requiere_tarea_cajero":true}'::jsonb,
  'CCT 659/13 homologado por Resolución ST 94/2013, art. 23',
  'VERIFICADA_OFICIAL',true,1,true),
 (gen_random_uuid(),'659/13','JORNADA','jornada',
  'Jornada completa máxima de 8 horas diarias o 45 semanales.',
  '16',
  '{"horas_diarias":8,"horas_semanales":45}'::jsonb,
  'CCT 659/13 homologado por Resolución ST 94/2013, art. 16',
  'VERIFICADA_OFICIAL',true,1,true),
 (gen_random_uuid(),'659/13','HORAS_SUPLEMENTARIAS','horas_extra',
  'Recargo 50% en días comunes y 100% sábados después de las 13, domingos y feriados.',
  '25',
  '{"recargo_comun":0.50,"recargo_especial":1.00}'::jsonb,
  'CCT 659/13 homologado por Resolución ST 94/2013, art. 25',
  'VERIFICADA_OFICIAL',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  tipo=EXCLUDED.tipo,descripcion=EXCLUDED.descripcion,articulo=EXCLUDED.articulo,
  configuracion=EXCLUDED.configuracion,fuente=EXCLUDED.fuente,
  estado_fuente=EXCLUDED.estado_fuente,is_verified=EXCLUDED.is_verified,activa=true;

DELETE FROM public.escala_salarial
WHERE cct_numero='659/13' AND valid_from=DATE '2026-08-01';

DELETE FROM public.parametro_legal
WHERE cct_numero='659/13'
  AND (valid_from=DATE '2026-08-01'
       OR codigo IN ('FATFA_SOLIDARIO','FATFA_CAPACITACION'));

DO $carga$
DECLARE
  r record;
  cant_escalas integer;
  cant_nr integer;
BEGIN
  FOR r IN
    SELECT * FROM (VALUES
      ('Cadetes','CADETE',1403185.39::numeric,36288.86::numeric),
      ('Aprendiz Ayudante','APRENDIZ',1403185.39::numeric,36288.86::numeric),
      ('Personal Auxiliar Interno y Externo','AUXILIAR',1486139.03::numeric,38434.19::numeric),
      ('Personal con Asignación Específica','ASIGNACION',1580289.30::numeric,40869.08::numeric),
      ('Ayudante en Gestión de Farmacia','AYUDANTE_GESTION',1580289.30::numeric,40869.08::numeric),
      ('Personal en Gestión de Farmacia','GESTION',1933355.60::numeric,50000.00::numeric),
      ('Farmacéutico','FARMACEUTICO',2134953.36::numeric,55213.68::numeric)
    ) AS datos(categoria,clave,basico,suma_nr)
  LOOP
    IF NOT EXISTS (
      SELECT 1 FROM public.cct_categoria
      WHERE cct_numero='659/13' AND nombre=r.categoria AND activa
    ) THEN
      RAISE EXCEPTION 'FATFA: falta la categoría activa %', r.categoria;
    END IF;

    INSERT INTO public.escala_salarial
      (id,cct_numero,categoria,basico,valid_from,valid_to,fuente,
       estado_fuente,is_verified,version,provisoria,habilitada_liquidacion)
    VALUES
      (gen_random_uuid(),'659/13',r.categoria,r.basico,
       DATE '2026-08-01',DATE '2026-08-31',
       'FATFA · Escala salarial agosto-noviembre · Anexo I paritaria CCT 659/13 · 27/08/2026',
       'PROVISORIA',false,1,true,true);

    INSERT INTO public.parametro_legal
      (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,
       estado_fuente,is_verified,version,cct_numero,incidencias)
    VALUES
      (gen_random_uuid(),'FATFA_NR_' || r.clave,r.suma_nr,'ARS','no_rem',
       DATE '2026-08-01',DATE '2026-08-31',
       'FATFA · Escala salarial agosto-noviembre · Anexo I paritaria CCT 659/13 · 27/08/2026',
       'PROVISORIA',false,1,'659/13',
       jsonb_build_object(
         'categoria',r.categoria,'regla_jornada','proporcional',
         'integra_antiguedad',false,'integra_presentismo',false,
         'aporte_jubilacion',false,'aporte_obra_social',false,
         'aporte_sindicato',true
       ));
  END LOOP;

  SELECT count(*) INTO cant_escalas FROM public.escala_salarial
  WHERE cct_numero='659/13' AND valid_from=DATE '2026-08-01';
  SELECT count(*) INTO cant_nr FROM public.parametro_legal
  WHERE cct_numero='659/13' AND codigo LIKE 'FATFA_NR_%'
    AND valid_from=DATE '2026-08-01';

  IF cant_escalas <> 7 OR cant_nr <> 7 THEN
    RAISE EXCEPTION 'FATFA incompleto: escalas %, sumas NR % (esperado 7/7)',
      cant_escalas, cant_nr;
  END IF;
END
$carga$;

INSERT INTO public.parametro_legal
  (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,
   estado_fuente,is_verified,version,cct_numero,incidencias)
VALUES
 (gen_random_uuid(),'FATFA_SOLIDARIO',0.01,'%','ded_todos',
  DATE '2013-02-01',NULL,
  'CCT 659/13 homologado por Resolución ST 94/2013, art. 47',
  'VERIFICADA_OFICIAL',true,1,'659/13',
  '{"base_deduccion":"sindical","destino_pago":"FATFA","codigo_boleta":"FATFA_APORTES","canal_pago":"Boleta electrónica FATFA","url_pago":"https://fatfa.org.ar/","regla_vencimiento":"Del día 1 al 10 de cada mes","fuente_pago":"CCT 659/13 art. 47"}'::jsonb),
 (gen_random_uuid(),'FATFA_CAPACITACION',0.01,'%','contrib_emp',
  DATE '2013-02-01',NULL,
  'CCT 659/13 homologado por Resolución ST 94/2013, art. 48',
  'VERIFICADA_OFICIAL',true,1,'659/13',
  '{"base_contribucion":"basico","destino_pago":"FATFA","codigo_boleta":"FATFA_APORTES","canal_pago":"Boleta electrónica FATFA","url_pago":"https://fatfa.org.ar/","regla_vencimiento":"Del día 1 al 10 de cada mes","fuente_pago":"CCT 659/13 art. 48"}'::jsonb);

COMMIT;
