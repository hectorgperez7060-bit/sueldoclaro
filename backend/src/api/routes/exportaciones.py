"""Controles ARCA y planilla de carga SOECRA desde una carpeta inmutable."""
from __future__ import annotations

import csv
import io
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from api.dependencies.auth import Principal, require_rol
from infrastructure.database import models as m
from infrastructure.database.session import tenant_session
from infrastructure.lsd.catalogo_afip import concepto_arca
from infrastructure.lsd.perfil_arca import faltantes_perfil

router = APIRouter(prefix="/exportaciones", tags=["exportaciones"])
_FUNERARIAS = {"749/18", "761/19"}
_URL_SOECRA = "https://soecra.com.ar/ddjj-empresas/"


def _datos(carpeta: m.CarpetaMensual):
    contenido = carpeta.contenido or {}
    return contenido, contenido.get("snapshot_parametros", {}), contenido.get("detalles", [])


async def _carpeta(s, carpeta_id: str) -> m.CarpetaMensual:
    try:
        cid = uuid.UUID(carpeta_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Identificador inválido") from exc
    carpeta = await s.get(m.CarpetaMensual, cid)
    if carpeta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carpeta mensual no encontrada")
    return carpeta


@router.get("/carpetas/{carpeta_id}/arca-control")
async def control_arca(
    carpeta_id: str,
    principal: Principal = Depends(require_rol("admin", "liquidador", "contador_revisor")),
):
    async with tenant_session(principal.tenant_id) as s:
        carpeta = await _carpeta(s, carpeta_id)
        _, snapshot, detalles = _datos(carpeta)
        empleados = snapshot.get("empleados", {})
        faltantes = []
        for detalle in detalles:
            eid = str(detalle.get("empleado_id", ""))
            foto = empleados.get(eid, {})
            perfil = foto.get("perfil_arca", {})
            for campo in faltantes_perfil(perfil):
                faltantes.append({"empleado_id": eid, "campo": campo})
            for concepto in detalle.get("conceptos", []):
                codigo = concepto.get("codigo", "")
                catalogado = concepto_arca(codigo)
                if catalogado is None or not catalogado.verificado:
                    faltantes.append({
                        "empleado_id": eid, "campo": "concepto_arca",
                        "concepto": codigo,
                    })
            if not detalle.get("bases_lsd"):
                faltantes.append({"empleado_id": eid, "campo": "bases_lsd"})
        empresa = snapshot.get("empresa", {})
        if len("".join(ch for ch in str(empresa.get("cuit", "")) if ch.isdigit())) != 11:
            faltantes.append({"campo": "cuit_empleador"})
        return {
            "listo_para_txt": not faltantes,
            "periodo": carpeta.periodo,
            "version": carpeta.version,
            "faltantes": faltantes,
            "proximo_paso": (
                "Descargar TXT ARCA"
                if not faltantes else
                "Completar los datos indicados y volver a liquidar para fotografiarlos"
            ),
            "aclaracion": (
                "ARCA valida el TXT; después de aceptar la liquidación genera la declaración F.931."
            ),
        }


@router.get("/carpetas/{carpeta_id}/soecra.csv")
async def planilla_soecra(
    carpeta_id: str,
    principal: Principal = Depends(require_rol("admin", "liquidador", "contador_revisor")),
):
    async with tenant_session(principal.tenant_id) as s:
        carpeta = await _carpeta(s, carpeta_id)
        _, snapshot, detalles = _datos(carpeta)
        empleados = snapshot.get("empleados", {})
        empresa = snapshot.get("empresa", {})
        filas = []
        for detalle in detalles:
            cct = detalle.get("cct_numero", "")
            if cct not in _FUNERARIAS:
                continue
            eid = str(detalle.get("empleado_id", ""))
            doc = empleados.get(eid, {}).get("documental", {})
            remunerativo = Decimal("0")
            no_remunerativo = Decimal("0")
            sindical = Decimal("0")
            for concepto in detalle.get("conceptos", []):
                importe = Decimal(str(concepto.get("importe", 0)))
                tipo = str(concepto.get("tipo", "")).upper()\n                if tipo == "REMUNERATIVO":
                    remunerativo += importe
                elif tipo == "NO_REMUNERATIVO":
                    no_remunerativo += importe
                if concepto.get("destino_pago") or "SIND" in concepto.get("codigo", ""):
                    sindical += importe
            filas.append([
                carpeta.periodo, empresa.get("cuit", ""), empresa.get("razon_social", ""),
                cct, doc.get("cuil", ""), f"{doc.get('apellido', '')}, {doc.get('nombre', '')}",
                doc.get("categoria", ""), f"{remunerativo:.2f}", f"{no_remunerativo:.2f}",
                f"{sindical:.2f}", detalle.get("bruto", ""), detalle.get("neto", ""),
            ])
        if not filas:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "La carpeta no contiene empleados de los CCT 749/18 o 761/19",
            )
        out = io.StringIO(newline="")
        writer = csv.writer(out, delimiter=";")
        writer.writerow([
            "periodo", "cuit_empleador", "razon_social", "cct", "cuil_trabajador",
            "trabajador", "categoria", "remunerativo", "no_remunerativo",
            "retenciones_sindicales", "bruto", "neto",
        ])
        writer.writerows(filas)
        contenido = ("sep=;\r\n" + out.getvalue()).encode("utf-8-sig")
        return Response(
            contenido, media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="control-soecra-{carpeta.periodo}-v{carpeta.version}.csv"',
                "X-Sueldo-Claro-Documento": "control-no-oficial",
                "X-SOECRA-DDJJ": _URL_SOECRA,
            },
        )
