-- 065: cerrar la superficie publica de PostgREST y completar las politicas
-- del rol del backend.
--
-- Cuatro tablas habian quedado accesibles con la clave publica del proyecto.
-- La mas grave es refresh_token: con esa clave se podian leer o escribir los
-- tokens de sesion de los usuarios y entrar como ellos. Los catalogos de
-- convenios tampoco tienen por que ser escribibles desde afuera.
--
-- El modelo de acceso del proyecto es: RLS prendida en todas las tablas, y el
-- rol del backend (sueldoclaro) entra por una politica <tabla>_backend_access.
-- Ese rol NO tiene BYPASSRLS: si una tabla queda con RLS y sin politica, el
-- backend deja de ver sus filas. Por eso cada ENABLE de aca abajo viene con su
-- politica correspondiente.
--
-- Sin FORCE: las tablas por empresa si usan FORCE, porque ahi el aislamiento
-- por tenant tiene que alcanzar tambien al backend. Estas no son por empresa.

ALTER TABLE public.refresh_token ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cct_categoria ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cct_regla_estructural ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cuota_sindical_art101 ENABLE ROW LEVEL SECURITY;

CREATE POLICY refresh_token_backend_access ON public.refresh_token
  FOR ALL TO sueldoclaro USING (true) WITH CHECK (true);

CREATE POLICY cct_categoria_backend_access ON public.cct_categoria
  FOR ALL TO sueldoclaro USING (true) WITH CHECK (true);

CREATE POLICY cct_regla_estructural_backend_access ON public.cct_regla_estructural
  FOR ALL TO sueldoclaro USING (true) WITH CHECK (true);

CREATE POLICY cuota_sindical_art101_backend_access ON public.cuota_sindical_art101
  FOR ALL TO sueldoclaro USING (true) WITH CHECK (true);

-- Tres tablas ya tenian RLS prendida de antes pero se habian quedado sin
-- politica para el backend, asi que el backend leia CERO filas de ellas.
--
-- cct_zona_vigencia era la costosa: tiene las 25 zonas verificadas de UOCRA
-- (A, B, C y C_AUSTRAL). Al no poder leerlas, toda liquidacion de construccion
-- cortaba con "La provincia X no tiene una zona salarial verificada", que
-- ademas es un mensaje enganoso: los datos estaban cargados y verificados.
CREATE POLICY cct_zona_vigencia_backend_access ON public.cct_zona_vigencia
  FOR ALL TO sueldoclaro USING (true) WITH CHECK (true);

CREATE POLICY cct_paquete_version_backend_access ON public.cct_paquete_version
  FOR ALL TO sueldoclaro USING (true) WITH CHECK (true);

CREATE POLICY contador_profesional_backend_access ON public.contador_profesional
  FOR ALL TO sueldoclaro USING (true) WITH CHECK (true);

-- borrar_empresa es SECURITY DEFINER y estaba expuesta en
-- /rest/v1/rpc/borrar_empresa: se podia invocar sin siquiera estar logueado,
-- pasandole el uuid de una empresa. El backend la sigue llamando con su
-- propio rol desde /auth, asi que revocarla afuera no afecta la app.
REVOKE ALL ON FUNCTION public.borrar_empresa(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.borrar_empresa(uuid) FROM anon;
REVOKE ALL ON FUNCTION public.borrar_empresa(uuid) FROM authenticated;
