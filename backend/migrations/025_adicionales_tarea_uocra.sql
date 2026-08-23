-- Adicionales verificados de tarea UOCRA arts. 56 y 57.
BEGIN;

ALTER TABLE public.novedad_mensual
  ADD COLUMN IF NOT EXISTS horas_hormigon_manual_uocra numeric(8,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS horas_altura_uocra numeric(8,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS altura_metros_uocra numeric(8,2);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_novedad_adicionales_uocra_no_negativos') THEN
    ALTER TABLE public.novedad_mensual ADD CONSTRAINT ck_novedad_adicionales_uocra_no_negativos
      CHECK (horas_hormigon_manual_uocra >= 0 AND horas_altura_uocra >= 0
        AND (altura_metros_uocra IS NULL OR altura_metros_uocra >= 0));
  END IF;
END $$;

INSERT INTO public.cct_regla_estructural
  (id,cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,
   estado_fuente,is_verified,version,activa)
VALUES
  (gen_random_uuid(),'76/75','ADIC_HORMIGON_ART56','adicional_tarea',
   'Suplemento del 15% por horas efectivas de colada manual directa de hormigón, sin medios mecánicos o automáticos.',
   '56','{"porcentaje":0.15,"base":"basico_puro_horario","unidad":"horas_efectivas","requiere_trabajo_manual_directo":true}',
   'CCT 76/75 oficial UOCRA, art. 56: https://www.uocra.org/pdf/9c21ef_76.75.pdf',
   'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true),
  (gen_random_uuid(),'76/75','ADIC_ALTURA_ART57','adicional_tarea',
   'Suplemento por horas efectivas en balancín, silleta, andamio colgante y tareas enumeradas: 15%, 20% o 25% según altura.',
   '57','{"base":"basico_puro_horario","unidad":"horas_efectivas","tramos":[{"desde":4,"hasta":26,"porcentaje":0.15},{"desde":26,"hasta":40,"porcentaje":0.20},{"desde":40,"hasta":null,"porcentaje":0.25}],"bloqueo_limite_ambiguo":26}',
   'CCT 76/75 oficial UOCRA, art. 57: https://www.uocra.org/pdf/9c21ef_76.75.pdf',
   'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, articulo=EXCLUDED.articulo,
  configuracion=EXCLUDED.configuracion, fuente=EXCLUDED.fuente,
  estado_fuente=EXCLUDED.estado_fuente, is_verified=true, activa=true;

COMMIT;
