-- Política operativa mensual para escalas publicadas pendientes de validación final.
-- No homologa ni verifica fuentes: habilita reglas convencionales conocidas y
-- conserva la revisión/firma profesional como un estado separado.
BEGIN;

UPDATE public.cct
SET antiguedad_pct_por_anio = 0.01,
    presentismo_divisor = 10,
    aplica_presentismo = true,
    aplica_cuota_sindical = false,
    cuota_sindical_pct = 0,
    activo = true
WHERE numero IN ('749/18', '761/19');

DO $$
DECLARE
  faltantes integer;
BEGIN
  SELECT count(*) INTO faltantes
  FROM (VALUES ('749/18'), ('761/19')) AS esperados(numero)
  WHERE NOT EXISTS (
    SELECT 1 FROM public.cct c WHERE c.numero = esperados.numero AND c.activo
  );

  IF faltantes <> 0 THEN
    RAISE EXCEPTION 'Política provisoria SOECRA: faltan % convenios activos', faltantes;
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.cct
    WHERE numero IN ('749/18', '761/19')
      AND (
        antiguedad_pct_por_anio <> 0.01
        OR presentismo_divisor <> 10
        OR aplica_presentismo IS NOT TRUE
        OR aplica_cuota_sindical IS NOT FALSE
        OR cuota_sindical_pct <> 0
      )
  ) THEN
    RAISE EXCEPTION 'Política provisoria SOECRA: configuración convencional inconsistente';
  END IF;
END $$;

COMMIT;
