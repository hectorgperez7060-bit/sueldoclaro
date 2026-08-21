"""Regla GENERAL de escala verificada + filtro de NR por categoría.

- La vigencia (incluida la reutilización provisoria) vive en los datos.
- Los importes viven en la migración, no en el dominio ni el motor.
- El NR se aplica solo a la categoría declarada en sus incidencias.
"""
from datetime import date
from decimal import Decimal as D
from pathlib import Path

from domain.entities.empleado import Empleado
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.entities.escala_verificada import (
    MENSAJE_SIN_ESCALA, NOTA_PROVISORIA, evaluar_escala,
)
from domain.entities.farmacia_414_05 import CATEGORIAS_FARMACIA
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import MotorLiquidacion
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero

RAIZ = Path(__file__).parents[2]
MIG_010 = RAIZ / "migrations" / "010_escala_verificada_farmacia_414_05.sql"
ESPECIALIZADO = "Empleado Especializado de Farmacia"


def _escala(desde, hasta, verificada=True, provisoria=False, basico="100"):
    return EscalaSalarial("414/05", ESPECIALIZADO, Dinero(D(basico)),
                          desde, hasta, verificada, "fuente", provisoria)


# ----------------------------------------------------- regla general
def test_vigente_se_liquida():
    ev = evaluar_escala(_escala(date(2026, 7, 1), date(2026, 7, 31)))
    assert ev.estado == "vigente" and ev.puede_liquidar is True and ev.provisorio is False


def test_no_verificada_ni_provisoria_se_bloquea():
    ev = evaluar_escala(_escala(
        date(2026, 7, 1), date(2026, 7, 31), verificada=False, provisoria=False
    ))
    assert ev.estado == "bloqueada" and ev.puede_liquidar is False
    assert ev.escala is None and ev.motivo == MENSAJE_SIN_ESCALA


def test_provisoria_requiere_confirmacion():
    ev = evaluar_escala(_escala(date(2026, 8, 1), date(2026, 8, 31), verificada=False,
                                provisoria=True), confirmado=False)
    assert ev.estado == "provisoria" and ev.provisorio is True
    assert ev.requiere_confirmacion is True and ev.puede_liquidar is False
    assert ev.nota == NOTA_PROVISORIA


def test_provisoria_confirmada_liquida():
    ev = evaluar_escala(_escala(date(2026, 8, 1), date(2026, 8, 31), verificada=False,
                                provisoria=True), confirmado=True)
    assert ev.puede_liquidar is True and ev.escala is not None


def test_sin_escala_bloquea():
    ev = evaluar_escala(None)
    assert ev.estado == "bloqueada" and ev.puede_liquidar is False
    assert ev.motivo == "Sin escala salarial verificada para el período"
    assert MENSAJE_SIN_ESCALA == "Sin escala salarial verificada para el período"


def test_no_reutiliza_escala_previa_sin_vigencia():
    # La regla ya no recibe una escala previa: si no hay vigente, bloquea.
    # No existe forma de reutilizar una escala fuera de su vigencia declarada.
    import inspect
    from domain.entities import escala_verificada
    firma = inspect.signature(escala_verificada.evaluar_escala)
    assert list(firma.parameters) == ["vigente", "confirmado"]
    assert evaluar_escala(None).estado == "bloqueada"


def test_regla_general_sin_convenio_ni_fechas():
    fuente = (RAIZ / "src" / "domain" / "entities" / "escala_verificada.py").read_text()
    assert "414" not in fuente and "farmacia" not in fuente.lower()
    assert "2026" not in fuente


# ----------------------------------------------------- catálogo
def test_catalogo_seis_categorias_oficiales():
    assert len(CATEGORIAS_FARMACIA) == 6 and ESPECIALIZADO in CATEGORIAS_FARMACIA


# ----------------------------------------------------- NR por categoría (motor)
def _parametros_con_nr() -> ParametroSet:
    desde = date(2026, 1, 1)
    incid = {"categoria": ESPECIALIZADO, "regla_jornada": "solo_completa",
             "integra_antiguedad": False,
             "integra_presentismo": False, "aporte_jubilacion": False,
             "aporte_obra_social": False, "aporte_sindicato": True}
    return ParametroSet([
        ParametroLegal("APORTE_JUBILACION", D("0.11"), "%", "empleado", desde),
        ParametroLegal("APORTE_LEY19032", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_MODERNIZACION", D("0.01"), "%", "empleado", desde),
        ParametroLegal("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", desde),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0.06"), "%", "empleador", desde),
        ParametroLegal("FARMACIA_NR_ESPECIALIZADO_414/05", D("54100.54"), "ARS", "no_rem",
                       desde, None, True, "recibo", "414/05", incid),
    ])


def _cfg():
    return CctConfig("414/05", D("0"), D("12"), D("200"), aplica_presentismo=False,
                     aplica_cuota_sindical=False,
                     antiguedad_escalones=((1, D("0.05")), (2, D("0.10")), (5, D("0.20"))))


def _liquidar(categoria):
    emp = Empleado("N", "A", Cuil("27240320520"), date(2018, 4, 9), "414/05", categoria, "1",
                   afiliado_sindicato=True)
    escala = EscalaSalarial("414/05", categoria, Dinero(D("1828730.75")),
                            date(2026, 7, 1), date(2026, 7, 31), True, "f")
    from domain.value_objects.periodo import Periodo
    return MotorLiquidacion(_parametros_con_nr(), AmparoSet()).liquidar_mensual(
        emp, Periodo(2026, 7), escala, _cfg(), a_fecha=date(2026, 7, 28))


def test_nr_solo_para_categoria_declarada():
    esp = _liquidar(ESPECIALIZADO)
    assert any(c.codigo == "FARMACIA_NR_ESPECIALIZADO_414/05" for c in esp.conceptos)
    nr = next(c for c in esp.conceptos if c.codigo.startswith("FARMACIA_NR"))
    assert nr.importe.redondear().monto == D("54100.54")
    # Otras categorías (aunque tengan escala) NO reciben el NR.
    for otra in [c for c in CATEGORIAS_FARMACIA if c != ESPECIALIZADO]:
        res = _liquidar(otra)
        assert not any(c.codigo.startswith("FARMACIA_NR") for c in res.conceptos), otra


def test_nr_no_se_prorratea_sin_regla_verificada_de_jornada_parcial():
    emp = Empleado(
        "N", "A", Cuil("27240320520"), date(2018, 4, 9), "414/05",
        ESPECIALIZADO, "1", afiliado_sindicato=True,
        proporcion_jornada=D("0.5"),
    )
    escala = EscalaSalarial(
        "414/05", ESPECIALIZADO, Dinero(D("1828730.75")),
        date(2026, 7, 1), date(2026, 7, 31), True, "f",
    )
    from domain.value_objects.periodo import Periodo
    import pytest
    with pytest.raises(ValueError, match="sin regla verificada para jornada parcial"):
        MotorLiquidacion(_parametros_con_nr(), AmparoSet()).liquidar_mensual(
            emp, Periodo(2026, 7), escala, _cfg(), a_fecha=date(2026, 7, 28)
        )


# ----------------------------------------------------- importes solo en migración
def test_importes_no_estan_en_dominio_ni_motor():
    base = RAIZ / "src" / "domain"
    for archivo in base.rglob("*.py"):
        texto = archivo.read_text()
        assert "1828730.75" not in texto, archivo
        assert "54100.54" not in texto, archivo
    assert not (RAIZ / "src" / "domain" / "entities" / "farmacia_escala_414_05.py").exists()


def test_migracion_010_datos_y_provisorio():
    sql = MIG_010.read_text()
    assert "1828730.75" in sql and "54100.54" in sql
    assert "escala_salarial" in sql and "parametro_legal" in sql
    # Columna e idempotencia.
    assert "ADD COLUMN IF NOT EXISTS provisoria" in sql
    assert "IF NOT FOUND" in sql and "WHERE NOT EXISTS" in sql
    # NR acotado a julio con categoría declarada.
    assert "\"categoria\":\"Empleado Especializado de Farmacia\"" in sql
    assert '"regla_jornada":"solo_completa"' in sql
    assert "DATE '2026-07-31'" in sql
    # Provisorio de agosto con vigencia propia y marca provisoria.
    assert "DATE '2026-08-01'" in sql and "DATE '2026-08-31'" in sql
    assert "provisoria = true" in sql or ", true\n" in sql
    # No carga septiembre ni otras categorías.
    assert "2026-09" not in sql
    for otra in ["Categoría Inicial A", "Categoría Inicial B",
                 "Cajero, Perfumería y Administrativo", "Empleado de Farmacia", "Farmacéutico"]:
        assert otra not in sql
