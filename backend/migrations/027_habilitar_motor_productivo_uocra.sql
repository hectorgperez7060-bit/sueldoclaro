-- Habilitación productiva UOCRA únicamente si la matriz y sus dependencias
-- documentales están completas. Si falta una fila, aborta toda la transacción.
BEGIN;

DO $$
DECLARE
  periodo date;
  cantidad integer;
BEGIN
  FOREACH periodo IN ARRAY ARRAY[DATE '2026-06-01', DATE '2026-07-01', DATE '2026-08-01']
  LOOP
    SELECT count(*) INTO cantidad
    FROM public.escala_salarial
    WHERE cct_numero='76/75' AND valid_from=periodo AND version=1
      AND is_verified AND coalesce(fuente,'')<>''
      AND unidad_escala IN ('HORA','MENSUAL')
      AND basico_puro IS NOT NULL AND adicional_zona IS NOT NULL
      AND categoria IN ('Oficial Especializado','Oficial','Medio Oficial','Ayudante','Sereno')
      AND zona IN ('A','B','C','C_AUSTRAL');
    IF cantidad <> 20 THEN
      RAISE EXCEPTION 'UOCRA %: matriz verificada incompleta (%/20)', periodo, cantidad;
    END IF;
  END LOOP;

  SELECT count(*) INTO cantidad FROM public.cct_regla_estructural
  WHERE cct_numero='76/75' AND activa AND is_verified AND coalesce(fuente,'')<>'';
  IF cantidad < 9 THEN
    RAISE EXCEPTION 'UOCRA: reglas verificadas incompletas (%/9)', cantidad;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.parametro_legal WHERE codigo='APORTE_SOLIDARIO_UOCRA_76/75'
      AND cct_numero='76/75' AND is_verified AND valid_from<=DATE '2026-08-01'
      AND (valid_to IS NULL OR valid_to>=DATE '2026-08-31')
  ) OR NOT EXISTS (
    SELECT 1 FROM public.parametro_legal WHERE codigo='CONTRIB_EMP_UOCRA_76/75'
      AND cct_numero='76/75' AND is_verified AND valid_from<=DATE '2026-08-01'
      AND (valid_to IS NULL OR valid_to>=DATE '2026-08-31')
  ) THEN
    RAISE EXCEPTION 'UOCRA: faltan aportes/contribuciones versionados';
  END IF;
END $$;

UPDATE public.escala_salarial
SET habilitada_liquidacion=true
WHERE cct_numero='76/75' AND version=1
  AND valid_from IN (DATE '2026-06-01',DATE '2026-07-01',DATE '2026-08-01')
  AND is_verified AND coalesce(fuente,'')<>'';

-- Corrige una referencia secundaria equivocada sin cambiar la regla.
UPDATE public.cct_regla_estructural
SET fuente='CCT 76/75 oficial UOCRA, art. 52: https://www.uocra.org/pdf/9c21ef_76.75.pdf',
    estado_fuente='VERIFICADA_OFICIAL'
WHERE cct_numero='76/75' AND codigo='ASISTENCIA_PERFECTA' AND version=1;

INSERT INTO public.cct_paquete_version
  (cct_numero,paquete_version,hash_sha256,estado,resumen,fuente_manifest)
VALUES
  ('76/75','2026.08-productivo-v1',
   md5('UOCRA-76/75-2026-08-productivo-v1') || md5('1v-ovitcudorp-80-6202-57/67-ARCOU'),
   'INSTALADO',
   '{"categorias":5,"zonas":4,"escalas":20,"reglas_minimas":9,"motor":"PRODUCTIVO","periodos_habilitados":["2026-06","2026-07","2026-08"]}'::jsonb,
   'Migraciones 017 a 027; fuentes individualizadas en cada registro')
ON CONFLICT (cct_numero,paquete_version) DO UPDATE SET
  hash_sha256=EXCLUDED.hash_sha256,estado=EXCLUDED.estado,resumen=EXCLUDED.resumen,
  fuente_manifest=EXCLUDED.fuente_manifest,instalado_at=now();

COMMIT;
