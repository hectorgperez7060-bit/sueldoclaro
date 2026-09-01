"""Contrato instalable y visual de Sueldo Claro."""
from __future__ import annotations

import base64
import struct

from pwa_assets import ICON_192_B64, ICON_512_B64
from ui_page import HTML


def _png_size(encoded: str) -> tuple[int, int]:
    raw = base64.b64decode(encoded)
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", raw[16:24])


def test_iconos_pwa_tienen_dimensiones_reales():
    assert _png_size(ICON_192_B64) == (192, 192)
    assert _png_size(ICON_512_B64) == (512, 512)


def test_ui_declara_manifest_iconos_y_modo_instalable():
    assert 'rel="manifest" href="/manifest.webmanifest"' in HTML
    assert 'rel="apple-touch-icon" href="/icon-192.png"' in HTML
    assert 'name="theme-color" content="#087f72"' in HTML
    assert "navigator.serviceWorker.register('/sw.js')" in HTML
    assert "beforeinstallprompt" in HTML
    assert "Instalar Sueldo Claro" in HTML


def test_ui_conserva_navegacion_y_secciones_funcionales():
    for seccion in (
        "seccionInicio", "seccionEmpresas", "seccionConvenios",
        "seccionEstablecimientos", "seccionEmpleados", "seccionNovedades",
        "seccionLiquidar", "seccionHistorial",
    ):
        assert f'id="{seccion}"' in HTML
    assert "function irA(" in HTML
    assert "function alternarMenu(" in HTML


def test_service_worker_no_cachea_datos_privados():
    main = (
        __import__("pathlib").Path(__file__).resolve().parents[2]
        / "src" / "main.py"
    ).read_text(encoding="utf-8")

    assert '@app.get("/manifest.webmanifest"' in main
    assert '@app.get("/sw.js"' in main
    assert '@app.get("/icon-{size}.png"' in main
    assert "if(!SHELL.includes(u.pathname)) return;" in main
    assert "/liquidaciones" not in main.split('script = """', 1)[1].split('"""', 1)[0]
