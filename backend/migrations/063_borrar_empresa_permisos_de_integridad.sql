-- Segunda mitad del arreglo de la migracion 062. Borrar la empresa seguia
-- fallando con "permission denied for table revision_profesional", pero ya no
-- en el DELETE de esa tabla sino en el DELETE de tenant: Postgres verifica las
-- dos claves foraneas que apuntan a tenant con un
--
--   SELECT 1 FROM revision_profesional WHERE tenant_id = $1 FOR KEY SHARE
--
-- y esa clausula de bloqueo exige UPDATE ademas de SELECT. A estas dos tablas
-- se les habia revocado todo lo que no fuera INSERT y SELECT, asi que ni el
-- dueno podia hacer la verificacion.
--
-- El permiso se le da al dueno de las tablas (postgres), que es con quien corre
-- la funcion borrar_empresa. El rol de la aplicacion, sueldoclaro, sigue con
-- INSERT y SELECT nada mas sobre revision_profesional: no puede modificar ni
-- borrar una constancia de cierre.
BEGIN;

GRANT UPDATE, DELETE ON public.revision_profesional TO postgres;
GRANT UPDATE, DELETE ON public.obligacion_pago_mensual TO postgres;

COMMIT;
