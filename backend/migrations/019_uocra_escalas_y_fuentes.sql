-- UOCRA 76/75: estados documentales, zona histórica y escalas oficiales.
-- Los datos quedan registrados pero NO habilitados para liquidar hasta que el
-- motor admita jornales horarios, asistencia y devengamiento por quincena.
BEGIN;

ALTER TABLE public.cct_categoria
  ADD COLUMN IF NOT EXISTS estado_fuente varchar(40) NOT NULL DEFAULT 'PENDIENTE_DOCUMENTACION';
ALTER TABLE public.cct_regla_estructural
  ADD COLUMN IF NOT EXISTS estado_fuente varchar(40) NOT NULL DEFAULT 'PENDIENTE_DOCUMENTACION';
ALTER TABLE public.escala_salarial
  ADD COLUMN IF NOT EXISTS estado_fuente varchar(40) NOT NULL DEFAULT 'PENDIENTE_DOCUMENTACION',
  ADD COLUMN IF NOT EXISTS unidad_escala varchar(12) NOT NULL DEFAULT 'MENSUAL',
  ADD COLUMN IF NOT EXISTS basico_puro numeric(18,2),
  ADD COLUMN IF NOT EXISTS adicional_zona numeric(18,2),
  ADD COLUMN IF NOT EXISTS habilitada_liquidacion boolean NOT NULL DEFAULT true;
ALTER TABLE public.parametro_legal
  ADD COLUMN IF NOT EXISTS estado_fuente varchar(40) NOT NULL DEFAULT 'PENDIENTE_DOCUMENTACION';

DO $$
DECLARE
  tabla text;
BEGIN
  FOREACH tabla IN ARRAY ARRAY['cct_categoria','cct_regla_estructural','escala_salarial','parametro_legal']
  LOOP
    IF NOT EXISTS (
      SELECT 1 FROM pg_constraint WHERE conname = 'ck_' || tabla || '_estado_fuente'
    ) THEN
      EXECUTE format(
        'ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (estado_fuente IN (' ||
        '''VERIFICADA_OFICIAL'',''HOMOLOGADA_NO_PUBLICADA_BORA'',' ||
        '''PUBLICADA_POR_PARTE_SIGNATARIA'',''PROVISORIA'',' ||
        '''PENDIENTE_DOCUMENTACION'',''RECHAZADA''))',
        tabla, 'ck_' || tabla || '_estado_fuente'
      );
    END IF;
  END LOOP;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_escala_salarial_unidad') THEN
    ALTER TABLE public.escala_salarial ADD CONSTRAINT ck_escala_salarial_unidad
      CHECK (unidad_escala IN ('HORA','MENSUAL'));
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.cct_zona_vigencia (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cct_numero varchar(20) NOT NULL,
  provincia varchar(80) NOT NULL,
  zona varchar(20) NOT NULL,
  valid_from date NOT NULL,
  valid_to date,
  fuente text NOT NULL DEFAULT '',
  estado_fuente varchar(40) NOT NULL DEFAULT 'PENDIENTE_DOCUMENTACION',
  is_verified boolean NOT NULL DEFAULT false,
  version integer NOT NULL DEFAULT 1,
  UNIQUE (cct_numero, provincia, valid_from, version)
);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_cct_zona_estado_fuente') THEN
    ALTER TABLE public.cct_zona_vigencia ADD CONSTRAINT ck_cct_zona_estado_fuente
      CHECK (estado_fuente IN (
        'VERIFICADA_OFICIAL','HOMOLOGADA_NO_PUBLICADA_BORA',
        'PUBLICADA_POR_PARTE_SIGNATARIA','PROVISORIA',
        'PENDIENTE_DOCUMENTACION','RECHAZADA'
      ));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_cct_zona_vigencia_busqueda
  ON public.cct_zona_vigencia (cct_numero, provincia, valid_from, valid_to);

ALTER TABLE public.cct_zona_vigencia DISABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sueldoclaro') THEN
    REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.cct_zona_vigencia FROM sueldoclaro;
    GRANT SELECT ON public.cct_zona_vigencia TO sueldoclaro;
  END IF;
END $$;

-- La estructura declara que el mapa se resuelve por vigencia. Se elimina el
-- mapa fijo incrustado en JSON para impedir errores en liquidaciones históricas.
UPDATE public.cct_regla_estructural
SET configuracion = '{"campo_determinante":"domicilio_laboral","resolucion":"cct_zona_vigencia","zonas":["A","B","C","C_AUSTRAL"],"requiere_confirmacion_usuario":true}',
    fuente = 'CCT 76/75; tablas salariales UOCRA y Res. ST 362/2008 y 1713/2010',
    estado_fuente = 'PUBLICADA_POR_PARTE_SIGNATARIA',
    is_verified = true
WHERE cct_numero = '76/75' AND codigo = 'ZONIFICACION' AND activa = true;

-- Mapa vigente. La Pampa cambia de A a B desde el acuerdo del 22/02/2008.
WITH actuales(provincia,zona,desde,fuente) AS (VALUES
  ('CABA','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Buenos Aires','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Catamarca','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Chaco','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Cordoba','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Corrientes','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Entre Rios','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Formosa','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Jujuy','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('La Rioja','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Mendoza','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Misiones','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Salta','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('San Juan','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('San Luis','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Santa Fe','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Santiago del Estero','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('Tucuman','A',DATE '1975-01-01','CCT 76/75; tablas UOCRA'),
  ('La Pampa','A',DATE '1975-01-01','Tabla UOCRA octubre 2006'),
  ('La Pampa','B',DATE '2008-02-22','Res. ST 362/2008 y tablas UOCRA posteriores'),
  ('Neuquen','B',DATE '1975-01-01','Tablas salariales UOCRA'),
  ('Rio Negro','B',DATE '1975-01-01','Tablas salariales UOCRA'),
  ('Chubut','B',DATE '1975-01-01','Tablas salariales UOCRA'),
  ('Santa Cruz','C',DATE '1975-01-01','Tablas salariales UOCRA'),
  ('Tierra del Fuego','C_AUSTRAL',DATE '1975-01-01','Tablas salariales UOCRA')
)
INSERT INTO public.cct_zona_vigencia
  (cct_numero,provincia,zona,valid_from,valid_to,fuente,estado_fuente,is_verified,version)
SELECT '76/75', provincia, zona, desde,
       CASE WHEN provincia='La Pampa' AND zona='A' THEN DATE '2008-02-21' ELSE NULL END,
       fuente, 'PUBLICADA_POR_PARTE_SIGNATARIA', true, 1
FROM actuales
ON CONFLICT (cct_numero,provincia,valid_from,version) DO UPDATE SET
  zona=EXCLUDED.zona, valid_to=EXCLUDED.valid_to, fuente=EXCLUDED.fuente,
  estado_fuente=EXCLUDED.estado_fuente, is_verified=EXCLUDED.is_verified;

-- Total oficial por categoría y zona. Para las categorías jornalizadas el
-- total es horario; Sereno es mensual. Se preservan básico puro, adicional y
-- total porque los anexos oficiales contienen redondeos de un peso.
WITH datos(periodo,categoria,zona,basico_puro,adicional,total,unidad) AS (VALUES
  (DATE '2026-06-01','Oficial Especializado','A',6666,0,6666,'HORA'),
  (DATE '2026-06-01','Oficial Especializado','B',6666,733,7400,'HORA'),
  (DATE '2026-06-01','Oficial Especializado','C',6666,3568,10234,'HORA'),
  (DATE '2026-06-01','Oficial Especializado','C_AUSTRAL',6666,6666,13333,'HORA'),
  (DATE '2026-06-01','Oficial','A',5703,0,5703,'HORA'),
  (DATE '2026-06-01','Oficial','B',5703,631,6333,'HORA'),
  (DATE '2026-06-01','Oficial','C',5703,3892,9595,'HORA'),
  (DATE '2026-06-01','Oficial','C_AUSTRAL',5703,5703,11405,'HORA'),
  (DATE '2026-06-01','Medio Oficial','A',5270,0,5270,'HORA'),
  (DATE '2026-06-01','Medio Oficial','B',5270,572,5842,'HORA'),
  (DATE '2026-06-01','Medio Oficial','C',5270,3989,9259,'HORA'),
  (DATE '2026-06-01','Medio Oficial','C_AUSTRAL',5270,5270,10540,'HORA'),
  (DATE '2026-06-01','Ayudante','A',4851,0,4851,'HORA'),
  (DATE '2026-06-01','Ayudante','B',4851,558,5409,'HORA'),
  (DATE '2026-06-01','Ayudante','C',4851,4140,8990,'HORA'),
  (DATE '2026-06-01','Ayudante','C_AUSTRAL',4851,4851,9701,'HORA'),
  (DATE '2026-06-01','Sereno','A',881193,0,881193,'MENSUAL'),
  (DATE '2026-06-01','Sereno','B',881193,100495,981688,'MENSUAL'),
  (DATE '2026-06-01','Sereno','C',881193,591971,1473164,'MENSUAL'),
  (DATE '2026-06-01','Sereno','C_AUSTRAL',881193,881193,1762386,'MENSUAL'),
  (DATE '2026-07-01','Oficial Especializado','A',6800,0,6800,'HORA'),
  (DATE '2026-07-01','Oficial Especializado','B',6800,748,7548,'HORA'),
  (DATE '2026-07-01','Oficial Especializado','C',6800,3639,10439,'HORA'),
  (DATE '2026-07-01','Oficial Especializado','C_AUSTRAL',6800,6800,13599,'HORA'),
  (DATE '2026-07-01','Oficial','A',5817,0,5817,'HORA'),
  (DATE '2026-07-01','Oficial','B',5817,643,6460,'HORA'),
  (DATE '2026-07-01','Oficial','C',5817,3970,9787,'HORA'),
  (DATE '2026-07-01','Oficial','C_AUSTRAL',5817,5817,11633,'HORA'),
  (DATE '2026-07-01','Medio Oficial','A',5375,0,5375,'HORA'),
  (DATE '2026-07-01','Medio Oficial','B',5375,583,5958,'HORA'),
  (DATE '2026-07-01','Medio Oficial','C',5375,4069,9444,'HORA'),
  (DATE '2026-07-01','Medio Oficial','C_AUSTRAL',5375,5375,10750,'HORA'),
  (DATE '2026-07-01','Ayudante','A',4948,0,4948,'HORA'),
  (DATE '2026-07-01','Ayudante','B',4948,569,5517,'HORA'),
  (DATE '2026-07-01','Ayudante','C',4948,4223,9170,'HORA'),
  (DATE '2026-07-01','Ayudante','C_AUSTRAL',4948,4948,9895,'HORA'),
  (DATE '2026-07-01','Sereno','A',898817,0,898817,'MENSUAL'),
  (DATE '2026-07-01','Sereno','B',898817,102505,1001322,'MENSUAL'),
  (DATE '2026-07-01','Sereno','C',898817,603810,1502627,'MENSUAL'),
  (DATE '2026-07-01','Sereno','C_AUSTRAL',898817,898817,1797634,'MENSUAL'),
  (DATE '2026-08-01','Oficial Especializado','A',7420,0,7420,'HORA'),
  (DATE '2026-08-01','Oficial Especializado','B',7420,816,8237,'HORA'),
  (DATE '2026-08-01','Oficial Especializado','C',7420,3971,11392,'HORA'),
  (DATE '2026-08-01','Oficial Especializado','C_AUSTRAL',7420,7420,14841,'HORA'),
  (DATE '2026-08-01','Oficial','A',6348,0,6348,'HORA'),
  (DATE '2026-08-01','Oficial','B',6348,702,7049,'HORA'),
  (DATE '2026-08-01','Oficial','C',6348,4333,10680,'HORA'),
  (DATE '2026-08-01','Oficial','C_AUSTRAL',6348,6348,12695,'HORA'),
  (DATE '2026-08-01','Medio Oficial','A',5866,0,5866,'HORA'),
  (DATE '2026-08-01','Medio Oficial','B',5866,636,6502,'HORA'),
  (DATE '2026-08-01','Medio Oficial','C',5866,4440,10306,'HORA'),
  (DATE '2026-08-01','Medio Oficial','C_AUSTRAL',5866,5866,11732,'HORA'),
  (DATE '2026-08-01','Ayudante','A',5399,0,5399,'HORA'),
  (DATE '2026-08-01','Ayudante','B',5399,621,6020,'HORA'),
  (DATE '2026-08-01','Ayudante','C',5399,4608,10007,'HORA'),
  (DATE '2026-08-01','Ayudante','C_AUSTRAL',5399,5399,10798,'HORA'),
  (DATE '2026-08-01','Sereno','A',980858,0,980858,'MENSUAL'),
  (DATE '2026-08-01','Sereno','B',980858,111861,1092719,'MENSUAL'),
  (DATE '2026-08-01','Sereno','C',980858,658924,1639782,'MENSUAL'),
  (DATE '2026-08-01','Sereno','C_AUSTRAL',980858,980858,1961716,'MENSUAL')
)
INSERT INTO public.escala_salarial
  (cct_numero,categoria,zona,basico,basico_puro,adicional_zona,unidad_escala,
   valid_from,valid_to,fuente,estado_fuente,is_verified,provisoria,
   habilitada_liquidacion,version)
SELECT '76/75', categoria, zona, total, basico_puro, adicional, unidad,
       periodo, (periodo + INTERVAL '1 month - 1 day')::date,
       'UOCRA - Anexo I comunicado segundo tramo junio-julio-agosto 2026; resolución homologatoria 02/06/2026',
       'PUBLICADA_POR_PARTE_SIGNATARIA', true, false, false, 1
FROM datos
WHERE NOT EXISTS (
  SELECT 1 FROM public.escala_salarial e
  WHERE e.cct_numero='76/75' AND e.categoria=datos.categoria
    AND e.zona=datos.zona AND e.valid_from=datos.periodo AND e.version=1
);

COMMIT;
