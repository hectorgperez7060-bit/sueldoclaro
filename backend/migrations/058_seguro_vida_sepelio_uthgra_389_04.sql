-- UTHGRA–FEHGRA CCT 389/04 · seguro de vida y sepelio.
-- Art. 23.3: aporte del trabajador 1% + contribución del empleador 1%,
-- calculados sobre el total de las remuneraciones.
-- Fuente oficial: https://www.uthgra.org.ar/wp-content/uploads/2016/08/ConvFEHGRA.pdf
-- Canal oficial vigente: https://boletasuthgra.org.ar/

BEGIN;

DELETE FROM public.parametro_legal
 WHERE cct_numero = '389/04'
   AND codigo IN (
       'SEGURO_VIDA_SEPELIO_UTHGRA_389/04',
       'SEGURO_VIDA_SEPELIO_UTHGRA_EMP_389/04'
   );

INSERT INTO public.parametro_legal
    (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,
     estado_fuente,is_verified,version,cct_numero,incidencias)
VALUES
    (gen_random_uuid(),'SEGURO_VIDA_SEPELIO_UTHGRA_389/04',0.01,'%',
     'ded_todos',DATE '2004-09-16',NULL,
     'CCT 389/04 art. 23.3 publicado por UTHGRA',
     'VERIFICADA_OFICIAL',true,1,'389/04',
     '{"base_deduccion":"remunerativa","destino_pago":"UTHGRA","codigo_boleta":"UTHGRA_SEGURO_VIDA_SEPELIO","canal_pago":"Boletas UTHGRA","url_pago":"https://boletasuthgra.org.ar/","regla_vencimiento":"según vencimiento informado por la boleta UTHGRA","condicion":"todos_los_trabajadores"}'::jsonb),
    (gen_random_uuid(),'SEGURO_VIDA_SEPELIO_UTHGRA_EMP_389/04',0.01,'%',
     'contrib_emp',DATE '2004-09-16',NULL,
     'CCT 389/04 art. 23.3 publicado por UTHGRA',
     'VERIFICADA_OFICIAL',true,1,'389/04',
     '{"base_contribucion":"remunerativa","destino_pago":"UTHGRA","codigo_boleta":"UTHGRA_SEGURO_VIDA_SEPELIO","canal_pago":"Boletas UTHGRA","url_pago":"https://boletasuthgra.org.ar/","regla_vencimiento":"según vencimiento informado por la boleta UTHGRA","condicion":"a_cargo_del_empleador"}'::jsonb);

COMMIT;
