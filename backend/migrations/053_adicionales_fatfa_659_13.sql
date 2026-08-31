-- FATFA CCT 659/13 · referencias de títulos y adicionales de agosto 2026.
-- Fórmulas permanentes: CCT homologado por Resolución ST 94/2013, arts. 7, 22 y 23.
-- Importes temporales: escala publicada por FATFA el 28/08/2026; permanecen
-- PROVISORIOS hasta publicarse el acto homologatorio del acuerdo 27/08/2026.
BEGIN;

INSERT INTO public.cct_regla_estructural
  (id,cct_numero,codigo,tipo,descripcion,articulo,configuracion,
   fuente,estado_fuente,is_verified,version,activa)
VALUES
 (gen_random_uuid(),'659/13','TITULOS_FARMACEUTICOS_2026_08','referencias',
  'Bloqueo de título, auxiliar con bloqueo y título farmacéutico para agosto 2026.',
  '7',
  '{"vigencia_desde":"2026-08-01","vigencia_hasta":"2026-08-31","BLOQUEO_DT":1650389.40,"BLOQUEO_DT_NR":42681.99,"AUX_BLOQUEO":1320311.52,"AUX_BLOQUEO_NR":34145.59,"TITULO_60":990233.64,"TITULO_60_NR":25609.20}'::jsonb,
  'FATFA · Escala salarial agosto-noviembre · Anexo I paritaria CCT 659/13 · 27/08/2026',
  'PROVISORIA',false,1,true),
 (gen_random_uuid(),'659/13','ADICIONALES_CAPACITACION','adicional',
  'Certificados de auxiliar y técnico, capacitación profesional y títulos admitidos.',
  '22.a, 22.b y 22.c',
  '{"auxiliar_pct":0.10,"tecnico_pct":0.20,"actualizacion_profesional_pct":0.30,"titulo_secundario_pct":0.05,"requiere_certificacion":true}'::jsonb,
  'CCT 659/13 homologado por Resolución ST 94/2013, art. 22',
  'VERIFICADA_OFICIAL',true,1,true),
 (gen_random_uuid(),'659/13','ADICIONALES_TAREA','adicional',
  'Administración, perfumería, idiomas y vehículo propio requerido.',
  '22.d, 22.e, 22.f y 22.g',
  '{"administrativo_pct":0.10,"perfumeria_pct":0.10,"idioma_pct":0.10,"vehiculo_pct":0.15,"base":"BASICO_MAS_ANTIGUEDAD"}'::jsonb,
  'CCT 659/13 homologado por Resolución ST 94/2013, art. 22',
  'VERIFICADA_OFICIAL',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  tipo=EXCLUDED.tipo,descripcion=EXCLUDED.descripcion,articulo=EXCLUDED.articulo,
  configuracion=EXCLUDED.configuracion,fuente=EXCLUDED.fuente,
  estado_fuente=EXCLUDED.estado_fuente,is_verified=EXCLUDED.is_verified,activa=true;

COMMIT;
