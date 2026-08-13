from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import uuid

import pytest

from domain.entities.novedad import DatosNovedadMensual
from infrastructure.database.repositories import NovedadMensualRepo


def _repo():
    session = SimpleNamespace(add=Mock(), flush=AsyncMock(), delete=AsyncMock())
    return NovedadMensualRepo(session), session


@pytest.mark.asyncio
async def test_crear_rechaza_empleado_ajeno_o_inexistente():
    repo, session = _repo()
    repo._empleado_del_tenant = AsyncMock(return_value=None)

    with pytest.raises(LookupError, match="empresa activa"):
        await repo.crear(uuid.uuid4(), uuid.uuid4(), DatosNovedadMensual("2026-08"))

    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_crear_rechaza_duplicado():
    repo, session = _repo()
    repo._empleado_del_tenant = AsyncMock(return_value=object())
    repo.obtener_por_periodo = AsyncMock(return_value=object())

    with pytest.raises(ValueError, match="Ya existen"):
        await repo.crear(uuid.uuid4(), uuid.uuid4(), DatosNovedadMensual("2026-08"))

    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_crear_rechaza_periodo_confirmado():
    repo, session = _repo()
    repo._empleado_del_tenant = AsyncMock(return_value=object())
    repo.obtener_por_periodo = AsyncMock(return_value=None)
    repo._periodo_confirmado = AsyncMock(return_value=True)

    with pytest.raises(ValueError, match="confirmada"):
        await repo.crear(uuid.uuid4(), uuid.uuid4(), DatosNovedadMensual("2026-08"))

    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_crear_persiste_novedad_valida():
    repo, session = _repo()
    repo._empleado_del_tenant = AsyncMock(return_value=object())
    repo.obtener_por_periodo = AsyncMock(return_value=None)
    repo._periodo_confirmado = AsyncMock(return_value=False)
    tenant_id, empleado_id = uuid.uuid4(), uuid.uuid4()

    novedad = await repo.crear(
        tenant_id, empleado_id,
        DatosNovedadMensual("2026-08", dias_trabajados=20),
    )

    assert novedad.tenant_id == tenant_id
    assert novedad.empleado_id == empleado_id
    assert novedad.periodo == "2026-08"
    session.add.assert_called_once_with(novedad)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_editar_y_eliminar_bloqueados_si_hay_liquidacion_confirmada():
    repo, session = _repo()
    existente = SimpleNamespace(
        empleado_id=uuid.uuid4(), periodo="2026-08", tenant_id=uuid.uuid4()
    )
    repo.obtener = AsyncMock(return_value=existente)
    repo._periodo_confirmado = AsyncMock(return_value=True)

    with pytest.raises(ValueError, match="confirmada"):
        await repo.editar(
            existente.tenant_id, uuid.uuid4(), DatosNovedadMensual("2026-08")
        )
    with pytest.raises(ValueError, match="confirmada"):
        await repo.eliminar(existente.tenant_id, uuid.uuid4())

    session.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_editar_no_permite_mover_novedad_a_otro_periodo():
    repo, _ = _repo()
    existente = SimpleNamespace(
        empleado_id=uuid.uuid4(), periodo="2026-08", tenant_id=uuid.uuid4()
    )
    repo.obtener = AsyncMock(return_value=existente)

    with pytest.raises(ValueError, match="no se puede cambiar"):
        await repo.editar(
            existente.tenant_id, uuid.uuid4(), DatosNovedadMensual("2026-09")
        )
