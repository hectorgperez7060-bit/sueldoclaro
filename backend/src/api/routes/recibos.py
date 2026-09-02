"""Descarga de recibos PDF generados por el backend."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.dependencies.auth import Principal, require_rol
from infrastructure.pdf.recibo import generar_recibo_pdf

router = APIRouter(prefix="/recibos", tags=["recibos"])


class ConceptoPdf(BaseModel):
    codigo: str = ""
    descripcion: str
    tipo: Literal["remunerativo", "no_remunerativo", "deduccion", "contribucion"]
    importe: Decimal
    base_calculo: Optional[Decimal] = None
    unidad: str
    cantidad: Decimal
    # Metadatos ya calculados por el motor. Permiten agrupar el costo laboral por
    # destino real (sindicato, obra social) sin nombrar gremios en el PDF.
    destino_pago: Optional[str] = None
    codigo_boleta: Optional[str] = None


class DatosPagoPdf(BaseModel):
    fecha: str
    lugar: str
    forma: str = "No informada"
    # Datos del lugar de trabajo (LCT art. 140). Si no se informan, el PDF los
    # muestra como "No informado": nunca se completan por inferencia.
    establecimiento: Optional[str] = None
    domicilio_trabajo: Optional[str] = None


class DatosCargasPdf(BaseModel):
    """Último depósito de aportes y contribuciones (Ley 17.250 art. 12)."""

    fecha: date
    periodo: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    banco: str = Field(min_length=1)


class ReciboPdfIn(BaseModel):
    periodo: str
    empresa: dict
    empleado: dict
    pago: DatosPagoPdf
    cargas_sociales: DatosCargasPdf
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
