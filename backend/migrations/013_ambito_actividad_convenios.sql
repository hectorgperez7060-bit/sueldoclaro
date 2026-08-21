-- Etiquetas y reglas de ámbito para no confundir la actividad principal del
-- establecimiento con el sector interno donde presta tareas una persona.
BEGIN;

UPDATE public.cct SET nombre = 'Clínicas, sanatorios, geriátricos y establecimientos con internación'
WHERE numero = '122/75';
UPDATE public.cct SET nombre = 'Farmacias alcanzadas por ADEF'
WHERE numero = '414/05';
UPDATE public.cct SET nombre = 'Farmacias alcanzadas por FATFA-COFA'
WHERE numero = '659/13';

INSERT INTO public.cct_regla_estructural
  (cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,is_verified,version,activa)
VALUES
  ('122/75','AMBITO_ACTIVIDAD','ambito',
   'La actividad principal es clínica, sanatorio, geriátrico o establecimiento con internación; una farmacia interna es un sector del establecimiento sanitario.',
   'ámbito personal y de actividad',
   '{"actividad_principal":"sanidad_con_internacion","sectores_internos":["farmacia_interna"]}',
   'CCT 122/75 y acuerdos homologados: https://www.argentina.gob.ar/normativa/nacional/norma-257521/texto',true,1,true),
  ('414/05','AMBITO_ACTIVIDAD','ambito',
   'Convenio de empleados de farmacia dentro del ámbito personal y territorial de ADEF; no se asigna por la sola existencia de una farmacia interna en una clínica.',
   'arts. 2 y 3',
   '{"actividad_principal":"farmacia_comunitaria_comercial","excluye_asignacion_automatica_por_sector_interno":true}',
   'CCT 414/05 ADEF: https://www.adef.org.ar/institucional/legislacion/convenio-colectivo-de-trabajo-nro-414-05',true,1,true),
  ('659/13','AMBITO_ACTIVIDAD','ambito',
   'Convenio FATFA celebrado con cámaras y confederación de farmacias; no se asigna automáticamente a la farmacia interna de una clínica.',
   'ámbito de representación de las partes',
   '{"actividad_principal":"farmacia_comunitaria_comercial","excluye_asignacion_automatica_por_sector_interno":true}',
   'CCT 659/13 Infoleg: https://servicios.infoleg.gob.ar/infolegInternet/anexos/205000-209999/209603/norma.htm',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, articulo=EXCLUDED.articulo,
  configuracion=EXCLUDED.configuracion, fuente=EXCLUDED.fuente,
  is_verified=EXCLUDED.is_verified, activa=true;

COMMIT;
