"""La escala sin fecha de cierre, que se arrastra sola y paga de menos.

Toda la app está construida sobre "antes frenar que estimar": si no hay escala
vigente para el período, no se liquida. Pero una escala cargada sin fecha de
cierre nunca deja de estar vigente, así que no hay nada que frenar: se sigue
aplicando mes tras mes. Si el convenio acordó aumentos en el medio, el recibo
sale de menos y nadie se entera.

Pasó de verdad con Comercio: la escala de julio quedó abierta y la paritaria
había acordado 1,9 % en agosto y otro 1,9 % en septiembre.

No se puede frenar —quien decide si esa escala sigue siendo la buena es el
empleador, no el sistema— pero sí se puede avisar, y fuerte.
"""
from pathlib import Path

from domain.entities.carpeta_mensual import faltantes_para_revision


ROOT = Path(__file__).resolve().parents[2]
CODIGO = "ESCALA_SIN_CIERRE_DE_VIGENCIA"


def _leer(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _carpeta(pendientes):
    return {"control_normativo": {"apto_produccion": True, "pendientes": pendientes}}


def test_el_aviso_no_impide_cerrar_el_mes():
    """Es una advertencia para mirar antes de pagar, no una regla incumplida."""
    verificadas = [{"estado": "verificada"}]
    assert faltantes_para_revision(_carpeta([{"codigo": CODIGO}]), verificadas) == []


def test_una_regla_normativa_de_verdad_sigue_impidiendo_cerrar():
    verificadas = [{"estado": "verificada"}]
    faltantes = faltantes_para_revision(
        _carpeta([{"codigo": "ESCALA_SIN_FUENTE"}]), verificadas)
    assert faltantes, "una regla pendiente real tiene que seguir bloqueando"


def test_el_motor_detecta_la_escala_que_se_arrastra():
    caso = _leer("src/application/use_cases/liquidar_periodo.py")
    # Se dispara sólo cuando la escala no tiene cierre de vigencia.
    assert "if escala.valid_to is None:" in caso
    assert "_MESES_PARA_SOSPECHAR_ESCALA_VIEJA" in caso
    # Y viaja hasta el detalle del empleado y hasta la carpeta del período.
    assert '"escala_desactualizada": escala_desactualizada,' in caso
    assert "_CODIGO_ESCALA_SIN_CIERRE" in caso


def test_el_aviso_dice_que_hacer_y_no_solo_que_algo_pasa():
    caso = _leer("src/application/use_cases/liquidar_periodo.py")
    for frase in ("no tiene fecha", "pagando", "escala oficial"):
        assert frase in caso, frase
    # Lleva los datos para poder juzgarlo: desde cuándo rige y cuánto se arrastra.
    assert '"escala_desde"' in caso and '"meses_de_atraso"' in caso


def test_se_ve_donde_la_persona_decide_liquidar():
    ui = _leer("src/ui_page.py")
    assert "ESCALA SIN CIERRE DE VIGENCIA" in ui
    # No alcanza la etiqueta: el texto completo se muestra junto al empleado.
    assert "esc(det.escala_desactualizada.nota)" in ui
