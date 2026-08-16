"""Descarga de recibos PDF generados por el backend."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from api.dependencies.auth import Principal, require_rol
from infrastructure.pdf.recibo import generar_recibo_pdf

router = APIRouter(prefix="/recibos", tags=["recibos"])


class ConceptoPdf(BaseModel):
    descripcion: str
    tipo: Literal["remunerativo", "no_remunerativo", "deduccion", "contribucion"]
    importe: Decimal


class ReciboPdfIn(BaseModel):
    periodo: str
    empresa: dict
    empleado: dict
    conceptos: list[ConceptoPdf]
    bruto: Decimal
    total_deducciones: Decimal
    neto: Decimal


@router.post("/pdf")
async def descargar_pdf(
    body: ReciboPdfIn,
    _: Principal = Depends(require_rol("admin", "liquidador")),
):
    pdf = generar_recibo_pdf(body.model_dump())
    filename = f"recibo-{body.periodo}.pdf"
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
