-- El borrado fallaba con violacion de clave foranea: carpeta_mensual apunta a
-- liquidacion, y la funcion borraba la liquidacion antes que la carpeta. Yo
-- habia escrito el orden a mano y me equivoque; el orden correcto sale de las
-- claves foraneas reales, primero la tabla que referencia y despues la
-- referida:
--
--   revision_profesional             -> carpeta_mensual, tenant
--   obligacion_pago_mensual          -> carpeta_mensual, tenant
--   carpeta_mensual                  -> liquidacion
--   recibo                           -> liquidacion_detalle
--   liquidacion_detalle              -> liquidacion
--   novedad_mensual                  -> empleado
--   empleado_establecimiento_hist.   -> empleado, establecimiento
--   empleado                         -> establecimiento
--
-- Hay un test que compara este orden contra las claves foraneas declaradas en
-- los modelos, para que la proxima vez lo encuentre la suite y no el usuario.
BEGIN;

CREATE OR REPLACE FUNCTION public.borrar_empresa(p_tenant uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $funcion$
DECLARE
  resultado jsonb := '{}'::jsonb;
  tabla     text;
  filas     integer;
BEGIN
  PERFORM set_config('app.current_tenant', p_tenant::text, true);

  FOREACH tabla IN ARRAY ARRAY[
    'revision_profesional',
    'obligacion_pago_mensual',
    'carpeta_mensual',
    'recibo',
    'liquidacion_detalle',
    'liquidacion',
    'novedad_mensual',
    'empleado_establecimiento_historial',
    'empleado',
    'establecimiento',
    'usuario_tenant'
  ] LOOP
    EXECUTE format('DELETE FROM public.%I WHERE tenant_id = $1', tabla) USING p_tenant;
    GET DIAGNOSTICS filas = ROW_COUNT;
    IF filas > 0 THEN
      resultado := resultado || jsonb_build_object(tabla, filas);
    END IF;
  END LOOP;

  DELETE FROM public.tenant WHERE id = p_tenant;
  GET DIAGNOSTICS filas = ROW_COUNT;
  IF filas = 0 THEN
    RAISE EXCEPTION 'La empresa % no existe', p_tenant;
  END IF;
  resultado := resultado || jsonb_build_object('tenant', filas);

  RETURN resultado;
END;
$funcion$;

REVOKE ALL ON FUNCTION public.borrar_empresa(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.borrar_empresa(uuid) TO sueldoclaro;

COMMIT;
