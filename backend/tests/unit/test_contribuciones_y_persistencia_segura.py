from datetime import date
from decimal import Decimal
from pathlib import Path

from domain.entities.parametros import AmparoSet, ParametroLegal, ParametroSet
from domain.payroll_engine.engine import MotorLiquidacion
from domain.value_objects.dinero import Dinero


def test_descripcion_contribucion_muestra_porcentaje_real_del_parametro():
    parametros = ParametroSet([
        ParametroLegal(
            "CONTRIB_OBRA_SOCIAL", Decimal("0.05"), "%", "empleador",
            date(2026, 1, 1),
        )
    ])
    concepto = MotorLiquidacion(parametros, AmparoSet([]))._contribucion(
        "CONTRIB_OBRA_SOCIAL", "Contribución patronal obra social",
        Dinero(Decimal("2194476.90")),
    )

    assert concepto.descripcion == "Contribución patronal obra social (5%)"
    assert concepto.importe.monto == Decimal("109723.85")


def test_liquidacion_bloqueada_se_descarta_antes_de_crear_carpeta():
    source = (
        Path(__file__).parents[2]
        / "src" / "application" / "use_cases" / "liquidar_periodo.py"
    ).read_text(encoding="utf-8")

    descarte = source.index("if bloqueos or not detalles_out:")
    carpeta = source.index("contenido_carpeta = construir_contenido_carpeta")
    assert descarte < carpeta
    assert "await liq_repo.descartar(liq)" in source[descarte:carpeta]
    assert '"carpeta_mensual": None' in source[descarte:carpeta]
