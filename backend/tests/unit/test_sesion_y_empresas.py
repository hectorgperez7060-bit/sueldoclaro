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
    # Se borra el contenido antes que la empresa, y dentro de la sesion con
    # el tenant seteado, porque esas tablas tienen RLS.
    assert "tenant_session(str(tenant_id))" in auth
    bloque = auth[auth.index("_TABLAS_DEL_TENANT"):auth.index("@router.delete")]
    orden = re.findall(r'"([a-z_]+)"', bloque)
    for hija, madre in (("liquidacion_detalle", "liquidacion"),
                        ("obligacion_pago_mensual", "carpeta_mensual"),
                        ("empleado_establecimiento_historial", "empleado")):
        assert orden.index(hija) < orden.index(madre), f"{hija} debe borrarse antes que {madre}"
    assert orden[-1] == "establecimiento"

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
