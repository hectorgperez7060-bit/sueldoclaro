-- UOCRA: dos conceptos del 2% jurídicamente distintos.
-- No habilita el motor UOCRA ni presume cuota sindical de afiliados.
BEGIN;

INSERT INTO public.cct_regla_estructural
  (id,cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,
   estado_fuente,is_verified,version,activa)
VALUES
  (gen_random_uuid(),'76/75','APORTE_SOLIDARIO_2026','aporte_trabajador',
   'Aporte solidario del 2% para trabajadores no afiliados; la cuota sindical del afiliado lo absorbe.',
   'Acuerdo salarial mayo 2026',
   '{"desde":"2026-06-01","porcentaje":0.02,"universo":"no_afiliados","base":"remuneraciones_sujetas_aportes","absorcion":"cuota_sindical_afiliado","reserva_documental":"pendiente acceso al acta numerada y cláusula sexta"}',
   'UOCRA, comunicado del segundo tramo junio-julio-agosto 2026',
   'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true),
  (gen_random_uuid(),'76/75','CONTRIB_EMPRESARIA_2026','contribucion_empleador',
   'Contribución empresaria del 2% a UOCRA, sin retención al trabajador, sobre el plantel del mes anterior.',
   'Ley 23.551 art. 9',
   '{"desde":"2026-06-01","porcentaje":0.02,"universo":"todo_el_plantel","base":"remuneraciones_sujetas_aportes_mes_anterior","vigencia_abierta":true,"no_confundir_con_aporte_solidario":true}',
   'Acuerdo UOCRA del 30/07/2026 homologado el 20/08/2026',
   'HOMOLOGADA_NO_PUBLICADA_BORA',true,1,true)
ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, articulo=EXCLUDED.articulo,
  configuracion=EXCLUDED.configuracion, fuente=EXCLUDED.fuente,
  estado_fuente=EXCLUDED.estado_fuente, is_verified=EXCLUDED.is_verified, activa=true;

DO $$
DECLARE
  r record;
BEGIN
FOR r IN SELECT * FROM (VALUES
  ('APORTE_SOLIDARIO_UOCRA_76/75',0.02::numeric,'ded_noafil',
   'PUBLICADA_POR_PARTE_SIGNATARIA',
   'UOCRA, comunicado del segundo tramo junio-julio-agosto 2026',
   '{"base_deduccion":"remunerativa","destino_pago":"UOCRA","codigo_boleta":"UOCRA_APORTE_SOLIDARIO","condicion":"solo_no_afiliados","reserva_documental":"pendiente acceso al acta numerada y cláusula sexta"}'::jsonb),
  ('CONTRIB_EMP_UOCRA_76/75',0.02::numeric,'contrib_emp',
   'HOMOLOGADA_NO_PUBLICADA_BORA',
   'Acuerdo UOCRA del 30/07/2026 homologado el 20/08/2026',
   '{"base_contribucion":"remunerativa_mes_anterior","destino_pago":"UOCRA","codigo_boleta":"UOCRA_OTROS_CONCEPTOS","universo":"todo_el_plantel","no_retener_trabajador":true,"requiere_base_mes_anterior":true}'::jsonb)
) AS datos(codigo,valor,ambito,estado,fuente,incidencias)
LOOP
  UPDATE public.parametro_legal p SET
    valor=r.valor, unidad='%', ambito=r.ambito, valid_to=NULL,
    fuente=r.fuente, estado_fuente=r.estado, is_verified=true,
    cct_numero='76/75', incidencias=r.incidencias
  WHERE p.codigo=r.codigo AND p.valid_from=DATE '2026-06-01' AND p.version=1;
  IF NOT FOUND THEN
    INSERT INTO public.parametro_legal
      (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,
       is_verified,version,cct_numero,incidencias)
    VALUES
      (gen_random_uuid(),r.codigo,r.valor,'%',r.ambito,DATE '2026-06-01',NULL,
       r.fuente,r.estado,true,1,'76/75',r.incidencias);
  END IF;
END LOOP;
END $$;

COMMIT;
