-- Habilita las obligaciones SOECRA expresamente previstas por el CCT 749/18.
-- Agosto 2026: el acta salarial dispone que sus arts. 55, 56 y 61 alcanzan
-- también a las sumas no remunerativas del acuerdo.
-- Idempotente: cada concepto se reemplaza por código y vigencia.

BEGIN;

UPDATE public.parametro_legal
   SET incidencias = jsonb_set(incidencias, '{aporte_sindicato}', 'true'::jsonb, true)
 WHERE cct_numero = '749/18'
   AND valid_from = '2026-08-01'
   AND incidencias->>'base_arts_55_56_61' = 'true';

DELETE FROM public.parametro_legal
 WHERE cct_numero = '749/18'
   AND valid_from = '2026-08-01'
   AND codigo IN (
       'FONDO_FALLECIMIENTO_SOECRA_749/18',
       'CUOTA_SINDICAL_SOECRA_749/18',
       'FONDO_CONVENCIONAL_SOECRA_749/18'
   );

INSERT INTO public.parametro_legal
    (id,codigo,valor,unidad,ambito,valid_from,valid_to,is_verified,version,fuente,cct_numero,incidencias)
VALUES
    (gen_random_uuid(),'FONDO_FALLECIMIENTO_SOECRA_749/18',0.01,'%',
     'ded_todos','2026-08-01','2026-08-31',false,1,
     'CCT 749/18 art. 55 publicado por SOECRA; acta salarial 17/07/2026 punto 4',
     '749/18',
     '{"base_deduccion":"sindical","destino_pago":"SOECRA","codigo_boleta":"SOECRA_FONDO_FALLECIMIENTO","canal_pago":"CuotaQ","url_pago":"https://www.cuotaq.com/soecra","regla_vencimiento":"vence junto con los aportes del SUSS","condicion":"todos_los_trabajadores","incluye_no_remunerativos_agosto_2026":true}'::jsonb),
    (gen_random_uuid(),'CUOTA_SINDICAL_SOECRA_749/18',0.015,'%',
     'ded_afil','2026-08-01','2026-08-31',false,1,
     'CCT 749/18 art. 56 publicado por SOECRA; acta salarial 17/07/2026 punto 4',
     '749/18',
     '{"base_deduccion":"sindical","destino_pago":"SOECRA","codigo_boleta":"SOECRA_CUOTA_SINDICAL","canal_pago":"CuotaQ","url_pago":"https://www.cuotaq.com/soecra","regla_vencimiento":"dentro de los 15 días posteriores al mes vencido","condicion":"solo_afiliados_con_afiliacion_acreditada","incluye_no_remunerativos_agosto_2026":true}'::jsonb),
    (gen_random_uuid(),'FONDO_CONVENCIONAL_SOECRA_749/18',0.015,'%',
     'contrib_emp','2026-08-01','2026-08-31',false,1,
     'CCT 749/18 art. 61 publicado por SOECRA; acta salarial 17/07/2026 punto 4',
     '749/18',
     '{"base_contribucion":"sindical","destino_pago":"SOECRA","codigo_boleta":"SOECRA_FONDO_CONVENCIONAL","canal_pago":"CuotaQ","url_pago":"https://www.cuotaq.com/soecra","regla_vencimiento":"según DDJJ mensual SOECRA","condicion":"a_cargo_del_empleador","incluye_no_remunerativos_agosto_2026":true}'::jsonb);

COMMIT;
