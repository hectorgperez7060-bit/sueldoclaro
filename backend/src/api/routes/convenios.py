"""Rutas de convenios (CCT): listado con categorías vigentes para la UI."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select

from api.dependencies.auth import Principal, require_tenant
from infrastructure.database import models as m
from infrastructure.database.session import plain_session
from infrastructure.excel.normativa_importer import (
    generar_plantilla_normativa,
    vista_previa_normativa,
)

router = APIRouter(prefix="/convenios", tags=["convenios"])


@router.get("/plantilla-normativa")
async def plantilla_normativa(_: Principal = Depends(require_tenant)):
    return Response(
        content=generar_plantilla_normativa(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_normativa.xlsx"},
    )


@router.post("/preview-normativa")
async def preview_normativa(
    archivo: UploadFile,
    _: Principal = Depends(require_tenant),
):
    return vista_previa_normativa(await archivo.read())


def _fecha_periodo(periodo: str) -> date:
    try:
        anio_s, mes_s = periodo.split("-")
        if len(anio_s) != 4 or len(mes_s) != 2:
            raise ValueError
        return date(int(anio_s), int(mes_s), 28)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "El período debe tener formato AAAA-MM",
        ) from exc


def _estado_item(tipo: str, codigo: str, verificado: bool, fuente: str) -> dict:
    problemas = []
    if not verificado:
        problemas.append("pendiente de aprobación profesional")
    if not (fuente or "").strip():
        problemas.append("fuente legal faltante")
    return {
        "tipo": tipo,
        "codigo": codigo,
        "verificado": bool(verificado),
        "fuente": fuente or "",
        "problemas": problemas,
    }


@router.get("")
async def listar(_: Principal = Depends(require_tenant)):
    """Convenios activos con sus categorías (datos globales, sin tenant)."""
    async with plain_session() as s:
        ccts = (await s.execute(
            select(m.Cct).where(m.Cct.activo.is_(True)).order_by(m.Cct.numero)
        )).scalars().all()
        filas = (await s.execute(
            select(m.EscalaSalarial.cct_numero, m.EscalaSalarial.categoria).distinct()
        )).all()
    cats: dict[str, list[str]] = {}
    for numero, categoria in filas:
        cats.setdefault(numero, []).append(categoria)
    return [
        {
            "numero": c.numero,
            "nombre": c.nombre,
            "sindicato": c.sindicato,
            "categorias": sorted(cats.get(c.numero, [])),
        }
        for c in ccts
    ]


@router.get("/{numero}/estado-normativo")
async def estado_normativo(
    numero: str,
    periodo: str = Query(..., description="Período AAAA-MM"),
    _: Principal = Depends(require_tenant),
):
    """Semáforo documental. No modifica ni aprueba reglas."""
    fecha = _fecha_periodo(periodo)
    async with plain_session() as s:
        cct = (await s.execute(select(m.Cct).where(m.Cct.numero == numero))).scalar_one_or_none()
        if cct is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Convenio no encontrado")

        escalas = (await s.execute(select(m.EscalaSalarial).where(
            m.EscalaSalarial.cct_numero == numero,
            m.EscalaSalarial.valid_from <= fecha,
            (m.EscalaSalarial.valid_to.is_(None)) | (m.EscalaSalarial.valid_to >= fecha),
        ))).scalars().all()
        parametros = (await s.execute(select(m.ParametroLegal).where(
            (m.ParametroLegal.cct_numero.is_(None)) | (m.ParametroLegal.cct_numero == numero),
            m.ParametroLegal.valid_from <= fecha,
            (m.ParametroLegal.valid_to.is_(None)) | (m.ParametroLegal.valid_to >= fecha),
        ))).scalars().all()
        amparos = (await s.execute(select(m.AmparoCct).where(
            m.AmparoCct.cct_numero == numero,
            m.AmparoCct.valid_from <= fecha,
            (m.AmparoCct.valid_to.is_(None)) | (m.AmparoCct.valid_to >= fecha),
        ))).scalars().all()

    items = [
        _estado_item("escala", f"{e.categoria} v{e.version}", e.is_verified, e.fuente)
        for e in escalas
    ]
    items += [
        _estado_item("parametro", f"{p.codigo} v{p.version}", p.is_verified, p.fuente)
        for p in parametros
    ]
    items += [
        _estado_item("amparo", a.articulo_suspendido, a.is_verified, a.fuente)
        for a in amparos
    ]
    faltantes = []
    if not escalas:
        faltantes.append("No hay escala salarial vigente para el período")
    if not parametros:
        faltantes.append("No hay parámetros legales vigentes para el período")
    pendientes = [item for item in items if item["problemas"]]
    return {
        "cct_numero": numero,
        "nombre": cct.nombre,
        "sindicato": cct.sindicato,
        "periodo": periodo,
        "apto_produccion": not faltantes and not pendientes,
        "resumen": {
            "total_reglas": len(items),
            "aprobadas": len(items) - len(pendientes),
            "pendientes": len(pendientes),
        },
        "faltantes": faltantes,
        "items": items,
    }
