from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import uuid

import pytest

from domain.entities.carpeta_mensual import construir_contenido_carpeta, huella_carpeta
from infrastructure.database.repositories import CarpetaMensualRepo


def test_contenido_carpeta_suma_resultado_sin_recalcularlo():
    detalles = [
        {"empleado_id": "1", "bruto": "100.00", "total_deducciones": "20.00", "neto": "80.00", "conceptos": [{"codigo": "A"}]},
        {"empleado_id": "2", "bruto": "250.50", "total_deducciones": "50.10", "neto": "200.40", "conceptos": [{"codigo": "A"}, {"codigo": "B"}]},
    ]
    contenido = construir_contenido_carpeta(
        periodo="2026-08", tipo="mensual", liquidacion_id="liq-1",
        detalles=detalles, snapshot={"reglas": "exactas"}, reglas_pendientes=[],
    )
    assert contenido["cantidad_empleados"] == 2
    assert contenido["cantidad_conceptos"] == 3
    assert contenido["totales"] == {"bruto": "350.50", "deducciones": "70.10", "neto": "280.40"}
    assert contenido["control_normativo"]["apto_produccion"] is True
    assert contenido["obligaciones_sindicales"] == []
    assert len(huella_carpeta(contenido)) == 64


def test_pendientes_normativos_impiden_aptitud_sin_impedir_calculo():
    contenido = construir_contenido_carpeta(
        periodo="2026-08", tipo="mensual", liquidacion_id="liq-1",
        detalles=[], snapshot={}, reglas_pendientes=[{"codigo": "ESCALA", "verificado": False}],
    )
    assert contenido["control_normativo"]["apto_produccion"] is False
    assert contenido["control_normativo"]["pendientes"][0]["codigo"] == "ESCALA"


@pytest.mark.asyncio
async def test_repo_crea_version_siguiente_sin_pisar_anterior():
    resultado = Mock()
    resultado.scalar_one_or_none.return_value = 2
    session = SimpleNamespace(execute=AsyncMock(return_value=resultado), add=Mock(), flush=AsyncMock())
    repo = CarpetaMensualRepo(session)
    tenant, liq = uuid.uuid4(), uuid.uuid4()
    carpeta = await repo.crear_calculada(tenant, "2026-08", liq, {"x": 1}, "a" * 64)
    assert carpeta.version == 3
    assert carpeta.estado == "calculada"
    assert carpeta.liquidacion_id == liq
    session.add.assert_called_once_with(carpeta)
    session.flush.assert_awaited_once()
