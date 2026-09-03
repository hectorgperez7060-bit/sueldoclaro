-- Borrar una empresa fallaba con "permission denied for table
-- revision_profesional". No es un capricho: revision_profesional y
-- obligacion_pago_mensual son registros que la aplicacion no puede borrar de a
-- uno, a proposito, porque son la constancia de un cierre y de una obligacion
-- pagada. Pero borrar la empresa entera si es una operacion legitima.
--
-- En vez de darle DELETE suelto al rol de la aplicacion, el borrado completo
-- vive en una funcion SECURITY DEFINER: la aplicacion solo puede ejecutar esta
-- operacion, entera y en orden, y sigue sin poder borrar una constancia
-- aislada. La funcion setea app.current_tenant porque esas tablas tienen
-- FORCE ROW LEVEL SECURITY y ni el dueno se saltea la politica.
BEGIN;

GRANT DELETE ON public.revision_profesional TO postgres;
GRANT DELETE ON public.obligacion_pago_mensual TO postgres;

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

  -- De hija a madre: nunca se borra una fila que otra todavia referencia.
  FOREACH tabla IN ARRAY ARRAY[
    'revision_profesional',
    'obligacion_pago_mensual',
    'recibo',
    'liquidacion_detalle',
    'liquidacion',
    'carpeta_mensual',
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
