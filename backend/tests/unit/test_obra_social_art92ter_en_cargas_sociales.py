"""La diferencia del art. 92 ter también se deposita.

Al abrir la obra social en dos renglones en el recibo, el resto de la
aplicación quedó mirando el código viejo: el resumen de cargas sociales sumaba
sólo el primer renglón y la exportación a ARCA no reconocía el segundo.

Con jornada media eso significaba depositar la mitad de lo que se le retuvo al
trabajador. El recibo estaba bien; el número para pagar, no.

Son dos renglones sólo para que el recibo cierre contra el bruto que muestra.
Para ARCA y para el F.931 es un único concepto.
"""
from pathlib import Path

from infrastructure.lsd.bases_snapshot import codigo_empleador
from infrastructure.lsd.catalogo_afip import concepto_arca, es_generable


ROOT = Path(__file__).resolve().parents[2]
APORTE = "APORTE_OBRA_SOCIAL"
DIFERENCIA = "APORTE_OBRA_SOCIAL_ART92TER"


def test_la_diferencia_va_al_mismo_codigo_de_arca_que_el_aporte():
    base = concepto_arca(APORTE)
    dif = concepto_arca(DIFERENCIA)
    assert dif is not None, "sin esto la exportación a ARCA se bloquea"
    assert dif.codigo_tipo_arca == base.codigo_tipo_arca
    assert dif.grupo == base.grupo
    assert dif.clase_tope == base.clase_tope
    assert dif.verificado is True


def test_la_diferencia_suma_a_la_misma_base_imponible():
    assert codigo_empleador(DIFERENCIA) == codigo_empleador(APORTE) == "OBRA_SOC"


def test_una_liquidacion_con_jornada_parcial_se_puede_exportar():
    """Antes quedaba trabada: "concepto sin código ARCA"."""
    assert es_generable([
        "BASICO", "ANTIGUEDAD", "APORTE_JUBILACION", "APORTE_LEY19032",
        APORTE, DIFERENCIA,
    ])


def test_el_resumen_de_cargas_sociales_suma_los_dos_renglones():
    ui = (ROOT / "src/ui_page.py").read_text(encoding="utf-8")
    assert "const CS_MISMO_CONCEPTO = {" in ui
    assert "APORTE_OBRA_SOCIAL_ART92TER:'APORTE_OBRA_SOCIAL'" in ui
    assert "CONTRIB_OBRA_SOCIAL_ART92TER:'CONTRIB_OBRA_SOCIAL'" in ui
    # Se agrupa por concepto antes de acumular, no por el código del renglón.
    assert "const cod=csCodigo(c.codigo);" in ui
    # La etiqueta ya no puede decir "3 %": con jornada parcial el total
    # depositado es el 3 % de la jornada completa, no del bruto que se muestra.
    assert "APORTE_OBRA_SOCIAL:'Aporte obra social'" in ui
