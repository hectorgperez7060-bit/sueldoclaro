-- Corrige la base de las deducciones de SOECRA del CCT 761/19.
--
-- La migración 054 cargó incidencias.base_deduccion con el texto descriptivo
-- "total de remuneraciones", donde el motor espera uno de sus tres selectores
-- (sindical | remunerativa | no_remunerativa_sindical). Con ese valor el motor
-- aborta al liquidar con ValueError y el recibo no llega a emitirse.
--
-- La prosa pasa a base_deduccion_texto_convencional y el selector queda en
-- "remunerativa", que es lo que dicen los arts. 75 y 76 del convenio. No cambia
-- ningún importe ni ningún estado documental: las escalas siguen provisorias,
-- no verificadas y deshabilitadas para liquidación.
--
-- Es idempotente: se puede correr más de una vez sin efecto adicional.

BEGIN;

UPDATE public.parametro_legal
   SET incidencias = '{"base_deduccion": "remunerativa", "base_deduccion_texto_convencional": "total de remuneraciones (CCT 761/19 arts. 75 y 76)", "canal_pago": "CuotaQ", "codigo_boleta": "SOECRA_APORTE_SOLIDARIO", "condicion": "solo_no_afiliados", "destino_pago": "SOECRA", "reserva_documental": "acuerdo no homologado; verificar el texto del art. 76 en la versión homologada del CCT. El acta del 17/07/2026 no extiende el aporte a las sumas no remunerativas, a diferencia del punto 4 del acta del CCT 749/18: la base queda limitada a lo remunerativo hasta que se verifique el texto homologado.", "sumas_no_remunerativas_incluidas": false, "url_pago": "https://www.cuotaq.com/soecra", "vigencia_declarada": "julio y agosto de 2026 por prórroga"}'::jsonb
 WHERE codigo = 'APORTE_SOLIDARIO_SOECRA_761/19'
   AND cct_numero = '761/19'
   AND incidencias->>'base_deduccion' IS DISTINCT FROM 'remunerativa';

UPDATE public.parametro_legal
   SET incidencias = '{"base_deduccion": "remunerativa", "base_deduccion_texto_convencional": "total de remuneraciones (CCT 761/19 arts. 75 y 76)", "canal_pago": "CuotaQ", "codigo_boleta": "SOECRA_CUOTA_SINDICAL", "condicion": "solo_afiliados_con_afiliacion_acreditada", "destino_pago": "SOECRA", "regla_vencimiento": "dentro de los 15 días posteriores al mes vencido", "reserva_documental": "verificar contra el texto homologado antes de habilitar la retención. El acta del 17/07/2026 no extiende el aporte a las sumas no remunerativas, a diferencia del punto 4 del acta del CCT 749/18: la base queda limitada a lo remunerativo hasta que se verifique el texto homologado.", "sumas_no_remunerativas_incluidas": false, "url_pago": "https://www.cuotaq.com/soecra"}'::jsonb
 WHERE codigo = 'CUOTA_SINDICAL_SOECRA_761/19'
   AND cct_numero = '761/19'
   AND incidencias->>'base_deduccion' IS DISTINCT FROM 'remunerativa';

-- Huella del paquete: el JSON de normativa cambió, así que la versión instalada
-- deja de ser la 0.2.0-PROVISORIO y pasa a registrarse aparte.
UPDATE public.cct_paquete_version
   SET paquete_version = '0.2.1-PROVISORIO',
       hash_sha256 = 'e68340fc5bb36801c0e89ff075bfec78c324abc51e32f48aa41a7ca941c064b7',
       instalado_at = now()
 WHERE cct_numero = '761/19'
   AND paquete_version <> '0.2.1-PROVISORIO';

-- Control: no debe quedar ninguna deducción con una base que el motor no conozca.
DO $$
DECLARE
  invalidas int;
BEGIN
  SELECT count(*) INTO invalidas
    FROM public.parametro_legal
   WHERE incidencias ? 'base_deduccion'
     AND incidencias->>'base_deduccion' NOT IN
         ('sindical','remunerativa','no_remunerativa_sindical');
  IF invalidas > 0 THEN
    RAISE EXCEPTION 'Quedan % deducciones con una base que el motor no interpreta', invalidas;
  END IF;
END $$;

COMMIT;
