"""La sesion no se corta sola y las empresas se pueden borrar.

Dos cosas que hacian perder trabajo:

1. Los refresh tokens vivian en un diccionario en memoria del proceso. En
   Vercel cada request puede caer en una instancia distinta y cada instancia
   tiene su propia memoria, asi que a los 15 minutos el /auth/refresh no
   encontraba el jti, devolvia 401 y la aplicacion echaba al usuario en medio
   de la carga, borrandole con localStorage.clear() todo lo que habia escrito.

2. No habia forma de borrar una empresa cargada por error.
"""
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _leer(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_los_refresh_tokens_se_guardan_en_la_base_no_en_memoria():
    tokens = _leer("src/infrastructure/security/tokens.py")
    assert "class RefreshStore" not in tokens, "quedo el store en memoria"
    assert "_store_singleton" not in tokens

    store = _leer("src/infrastructure/security/refresh_store.py")
    assert "refresh_token" in store
    # Validar y quemar en un solo paso: dos pedidos simultaneos con el mismo
    # refresh no pueden renovarse los dos.
    assert "DELETE FROM refresh_token" in store and "RETURNING jti" in store
    assert "expira_en > now()" in store

    auth = _leer("src/api/routes/auth.py")
    assert "get_refresh_store" not in auth
    assert "await refresh_store.consumir(jti, sub)" in auth
    assert "await refresh_store.guardar(jti, usuario_id)" in auth

    sql = _leer("migrations/059_refresh_token_persistente.sql")
    assert "CREATE TABLE IF NOT EXISTS public.refresh_token" in sql
    assert "REFERENCES public.usuario(id)" in sql


def test_el_motor_no_se_queda_con_conexiones_tomadas_en_serverless():
    sesion = _leer("src/infrastructure/database/session.py")
    assert "NullPool" in sesion
    assert 'os.getenv("VERCEL")' in sesion
    # Detras del pooler no se puede cachear la sentencia preparada.
    assert '"statement_cache_size": 0' in sesion


def test_se_puede_borrar_una_empresa_con_confirmacion():
    auth = _leer("src/api/routes/auth.py")
    assert '@router.delete("/empresas/{empresa_id}"' in auth
    # Irreversible: pide el CUIT escrito a mano y ser admin de esa empresa.
    assert "confirmacion_cuit" in auth
    assert "Solo un administrador de la empresa puede borrarla" in auth
    assert "Es la única empresa de tu cuenta" in auth
    # El borrado entero lo hace una funcion de la base: el rol de la
    # aplicacion no tiene DELETE sobre la constancia de un cierre ni sobre una
    # obligacion pagada, y no se lo damos suelto solo para esto.
    assert "SELECT public.borrar_empresa(:tid)" in auth
    assert 'accion="borrar", entidad="tenant"' in auth

    sql = _leer("migrations/062_funcion_borrar_empresa.sql")
    assert "SECURITY DEFINER" in sql
    assert "SET search_path = public, pg_temp" in sql
    # Esas tablas tienen FORCE ROW LEVEL SECURITY: ni el dueño se saltea la
    # politica, asi que la funcion tiene que setear el tenant.
    assert "set_config('app.current_tenant'" in sql
    # La aplicacion puede ejecutarla, nadie mas.
    assert "REVOKE ALL ON FUNCTION public.borrar_empresa(uuid) FROM PUBLIC" in sql
    assert "GRANT EXECUTE ON FUNCTION public.borrar_empresa(uuid) TO sueldoclaro" in sql

    # La empresa se borra al final, cuando ya no queda nada que la referencie.
    ultima = _leer("migrations/064_borrar_empresa_orden_correcto.sql")
    assert ultima.index("DELETE FROM public.tenant") > ultima.index("END LOOP")


def _orden_de_borrado() -> list[str]:
    """El orden que usa la última versión de la función borrar_empresa."""
    sql = _leer("migrations/064_borrar_empresa_orden_correcto.sql")
    bloque = sql[sql.index("FOREACH tabla IN ARRAY"):sql.index("END LOOP")]
    return re.findall(r"'([a-z_]+)'", bloque) + ["tenant"]


def test_el_orden_de_borrado_respeta_las_claves_foraneas_declaradas():
    """Este test existe porque el orden lo escribí a mano y me equivoqué.

    carpeta_mensual apunta a liquidacion, y la primera versión borraba la
    liquidación antes que la carpeta: la base rechazaba el borrado con una
    violación de clave foránea y el usuario veía "referencia datos que no
    existen". En vez de volver a revisar la lista a ojo, se compara contra las
    claves foráneas que declaran los modelos.
    """
    from infrastructure.database import models  # noqa: F401  registra las tablas
    from infrastructure.database.base import Base

    orden = _orden_de_borrado()
    posicion = {tabla: indice for indice, tabla in enumerate(orden)}

    comprobadas = 0
    for tabla in Base.metadata.tables.values():
        if tabla.name not in posicion:
            continue
        for clave in tabla.foreign_keys:
            referida = clave.column.table.name
            if referida == tabla.name or referida not in posicion:
                continue
            comprobadas += 1
            assert posicion[tabla.name] < posicion[referida], (
                f"{tabla.name} apunta a {referida}: hay que borrarla antes"
            )
    assert comprobadas >= 6, "no se leyeron las claves foráneas de los modelos"


def test_el_borrado_puede_verificar_las_claves_foraneas_de_la_empresa():
    """Lo que hacía fallar el borrado incluso con la tabla ya vacía.

    Al borrar la empresa, Postgres verifica las dos claves foráneas que
    apuntan a ``tenant`` con un ``SELECT ... FOR KEY SHARE``, y esa cláusula
    de bloqueo exige UPDATE además de SELECT. A esas dos tablas se les había
    revocado todo lo que no fuera INSERT y SELECT, así que ni el dueño podía
    hacer la verificación.
    """
    sql = _leer("migrations/063_borrar_empresa_permisos_de_integridad.sql")
    assert "GRANT UPDATE, DELETE ON public.revision_profesional TO postgres" in sql
    assert "GRANT UPDATE, DELETE ON public.obligacion_pago_mensual TO postgres" in sql
    # El permiso es para el dueño, no para la aplicación: sueldoclaro no
    # aparece en ningún GRANT de estas migraciones sobre revision_profesional.
    assert "revision_profesional TO sueldoclaro" not in sql
    assert "revision_profesional TO sueldoclaro" not in _leer(
        "migrations/062_funcion_borrar_empresa.sql")

    ui = _leer("src/ui_page.py")
    assert "async function borrarEmpresa(" in ui
    assert "🗑️ Borrar" in ui


def test_al_cortarse_la_sesion_no_se_borra_lo_que_la_persona_escribio():
    ui = _leer("src/ui_page.py")
    assert "localStorage.clear()" not in ui, "salir() no puede borrar el borrador"
    assert "['sc_access','sc_refresh','sc_tenant'].forEach(k=>localStorage.removeItem(k))" in ui
    # Autoguardado y recuperacion de lo escrito.
    assert "function restaurarBorrador()" in ui
    assert "document.addEventListener('input', e=>borradorAnotar(e.target), true)" in ui
    # Nunca pisa un dato ya cargado: solo completa campos vacios.
    assert "if(el.value==='' && valor!==''&&valor!=null)" in ui
    assert "lo que estabas cargando quedó guardado" in ui


def test_la_cuenta_distingue_estudio_contable_de_empresa():
    """Un estudio lleva clientes; una empresa se liquida a sí misma.

    Mostrarle a una empresa la capa de "clientes" solo le complica la carga:
    tiene que inventar un grupo, elegir empresa activa y crear "clientes" que
    en realidad son ella misma.
    """
    schemas = _leer("src/application/dto/schemas.py")
    assert 'MODOS_CUENTA = ("ESTUDIO", "EMPRESA")' in schemas
    assert "class PerfilCuenta" in schemas

    modelos = _leer("src/infrastructure/database/models.py")
    assert "modo_cuenta" in modelos

    auth = _leer("src/api/routes/auth.py")
    assert '@router.get("/perfil", response_model=PerfilCuenta)' in auth
    # Se puede cambiar de modo sin recargar nada: solo cambia qué se muestra.
    assert '@router.put("/perfil/modo", response_model=PerfilCuenta)' in auth

    sql = _leer("migrations/061_modo_cuenta_estudio_o_empresa.sql")
    # Las cuentas que ya existen no cambian de comportamiento.
    assert "DEFAULT 'ESTUDIO'" in sql
    assert "CHECK (modo_cuenta IN ('ESTUDIO', 'EMPRESA'))" in sql

    ui = _leer("src/ui_page.py")
    assert "function elegirModoCuenta(" in ui and "function aplicarModoCuenta(" in ui
    assert "modo_cuenta:modoElegidoAlCrear" in ui
    # En modo empresa se esconde la capa de clientes entera.
    for oculto in ("btnNuevaEmpresaLateral", "btnNuevaEmpresaSeccion",
                   "campoNuevaEmpresaGrupo", "col-grupo-cliente"):
        assert oculto in ui


def test_al_entrar_se_recupera_el_borrador_y_se_aplica_el_modo():
    """Guardar el borrador no sirve de nada si nadie lo vuelve a leer."""
    ui = _leer("src/ui_page.py")
    entrar = ui[ui.index("async function entrar(){"):]
    entrar = entrar[:entrar.index("\nfunction toggleAlta")]
    assert "restaurarBorrador()" in entrar
    assert "avisarBorradorRecuperado(" in entrar
    assert "cargarPerfilCuenta()" in entrar
