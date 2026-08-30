-- UTHGRA-FEHGRA CCT 389/04 · básicos y segunda cuota NR de agosto 2026.
-- Fuente oficial: RE-2026-72653200-APN-CGDTEYS#MCH,
-- Acta 24/07/2026, Anexo I, pág. 5 de 5.
--
-- Operación atómica sin tablas auxiliares. El acuerdo fue presentado y
-- ratificado, pero al 30/08/2026 no se encontró acto homologatorio publicado.
-- Por eso la escala queda PROVISORIA, is_verified=false y provisoria=true.

DO $migracion$
DECLARE
  r record;
  categoria_nombre text;
  categoria_codigo text;
  parametro_codigo text;
  cantidad_escalas integer;
  cantidad_parametros integer;
BEGIN
  UPDATE public.cct
     SET nombre='Gastronómicos y Hoteleros',
         sindicato='UTHGRA',
         antiguedad_pct_por_anio=0,
         aplica_presentismo=false,
         aplica_cuota_sindical=false,
         activo=true
   WHERE numero='389/04';

  UPDATE public.cct_categoria
     SET activa=false
   WHERE cct_numero='389/04';

  DELETE FROM public.escala_salarial
   WHERE cct_numero='389/04'
     AND valid_from=DATE '2026-08-01';

  DELETE FROM public.parametro_legal
   WHERE cct_numero='389/04'
     AND codigo LIKE 'UTHGRA_ACUERDO_2026_SEGUNDA_%'
     AND valid_from=DATE '2026-08-01';

  FOR r IN
    SELECT *
      FROM (VALUES
        ('D',1, 990555::numeric, 68000::numeric),
        ('D',2,1047930::numeric, 72000::numeric),
        ('D',3,1099139::numeric, 75000::numeric),
        ('D',4,1157884::numeric, 79000::numeric),
        ('D',5,1210980::numeric, 83000::numeric),
        ('D',6,1292026::numeric, 88000::numeric),
        ('C',1,1013346::numeric, 69000::numeric),
        ('C',2,1080354::numeric, 74000::numeric),
        ('C',3,1148481::numeric, 79000::numeric),
        ('C',4,1195083::numeric, 82000::numeric),
        ('C',5,1243418::numeric, 85000::numeric),
        ('C',6,1337186::numeric, 91000::numeric),
        ('B',1,1038120::numeric, 71000::numeric),
        ('B',2,1102324::numeric, 75000::numeric),
        ('B',3,1180295::numeric, 81000::numeric),
        ('B',4,1217642::numeric, 83000::numeric),
        ('B',5,1271299::numeric, 87000::numeric),
        ('B',6,1384689::numeric, 95000::numeric),
        ('B',7,1538297::numeric,105000::numeric),
        ('A',1,1074307::numeric, 74000::numeric),
        ('A',2,1141004::numeric, 78000::numeric),
        ('A',3,1220868::numeric, 83000::numeric),
        ('A',4,1284118::numeric, 88000::numeric),
        ('A',5,1356517::numeric, 93000::numeric),
        ('A',6,1429981::numeric, 98000::numeric),
        ('A',7,1840959::numeric,126000::numeric),
        ('ESP',1,1206779::numeric, 83000::numeric),
        ('ESP',2,1281272::numeric, 88000::numeric),
        ('ESP',3,1342334::numeric, 92000::numeric),
        ('ESP',4,1424619::numeric, 97000::numeric),
        ('ESP',5,1483366::numeric,101000::numeric),
        ('ESP',6,1524806::numeric,104000::numeric),
        ('ESP',7,1970475::numeric,134000::numeric)
      ) AS datos(clase,nivel,basico,no_remunerativo)
  LOOP
    categoria_nombre := 'Nivel ' || r.nivel || ' · Categoría ' || r.clase;
    categoria_codigo := 'N' || r.nivel || '_CLASE_' || r.clase;
    parametro_codigo := 'UTHGRA_ACUERDO_2026_SEGUNDA_N' || r.nivel || '_' || r.clase;

    IF EXISTS (
      SELECT 1 FROM public.cct_categoria
       WHERE cct_numero='389/04' AND codigo=categoria_codigo
    ) THEN
      UPDATE public.cct_categoria
         SET nombre=categoria_nombre,
             orden=(CASE r.clase
                      WHEN 'D' THEN 0 WHEN 'C' THEN 100
                      WHEN 'B' THEN 200 WHEN 'A' THEN 300 ELSE 400
                    END) + r.nivel * 10,
             activa=true,
             fuente='CCT 389/04 arts. 10.1 y 11.1; acuerdo UTHGRA-FEHGRA 24/07/2026, Anexo I',
             estado_fuente='VERIFICADA_OFICIAL',
             is_verified=true
       WHERE cct_numero='389/04' AND codigo=categoria_codigo;
    ELSE
      INSERT INTO public.cct_categoria
        (id,cct_numero,codigo,nombre,orden,activa,fuente,
         estado_fuente,is_verified,version)
      VALUES
        (gen_random_uuid(),'389/04',categoria_codigo,categoria_nombre,
         (CASE r.clase
            WHEN 'D' THEN 0 WHEN 'C' THEN 100
            WHEN 'B' THEN 200 WHEN 'A' THEN 300 ELSE 400
          END) + r.nivel * 10,
         true,
         'CCT 389/04 arts. 10.1 y 11.1; acuerdo UTHGRA-FEHGRA 24/07/2026, Anexo I',
         'VERIFICADA_OFICIAL',true,1);
    END IF;

    INSERT INTO public.escala_salarial
      (id,cct_numero,categoria,basico,valid_from,valid_to,fuente,
       estado_fuente,is_verified,version,provisoria)
    VALUES
      (gen_random_uuid(),'389/04',categoria_nombre,r.basico,
       DATE '2026-08-01',DATE '2026-08-31',
       'UTHGRA-FEHGRA · Acta 24/07/2026 · RE-2026-72653200 · Anexo I pág. 5',
       'PROVISORIA',false,1,true);

    INSERT INTO public.parametro_legal
      (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,
       estado_fuente,is_verified,version,cct_numero,incidencias)
    VALUES
      (gen_random_uuid(),parametro_codigo,r.no_remunerativo,'ARS','no_rem',
       DATE '2026-08-01',DATE '2026-08-31',
       'UTHGRA-FEHGRA · Acta 24/07/2026 · RE-2026-72653200 · PRIMERO y Anexo I pág. 5',
       'PROVISORIA',false,1,'389/04',
       jsonb_build_object(
         'categoria',categoria_nombre,
         'regla_jornada','proporcional',
         'integra_antiguedad',false,
         'integra_presentismo',false,
         'aporte_jubilacion',false,
         'aporte_obra_social',false,
         'aporte_sindicato',false
       ));
  END LOOP;

  SELECT count(*) INTO cantidad_escalas
    FROM public.escala_salarial
   WHERE cct_numero='389/04'
     AND valid_from=DATE '2026-08-01';

  SELECT count(*) INTO cantidad_parametros
    FROM public.parametro_legal
   WHERE cct_numero='389/04'
     AND codigo LIKE 'UTHGRA_ACUERDO_2026_SEGUNDA_%'
     AND valid_from=DATE '2026-08-01';

  IF cantidad_escalas <> 33 OR cantidad_parametros <> 33 THEN
    RAISE EXCEPTION
      'Control UTHGRA falló: escalas %, parámetros %',
      cantidad_escalas, cantidad_parametros;
  END IF;
END
$migracion$;
