"""Exportaciones ARCA y SOECRA desde una carpeta mensual inmutable."""
from __future__ import annotations

import csv
import io
import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from api.dependencies.auth import Principal, require_rol
from infrastructure.database import models as m
from infrastructure.database.session import tenant_session
from infrastructure.lsd.bases_snapshot import codigo_empleador, codigo_tipo_arca
from infrastructure.lsd.generator import (
    ConceptoLSD, EmpleadorLSD, TrabajadorLSD, build_lsd_bytes,
)
from infrastructure.lsd.perfil_arca import construir_atributos_suss, faltantes_perfil

router = APIRouter(prefix="/exportaciones", tags=["exportaciones"])
_ROLES = Depends(require_rol("admin", "liquidador", "contador_revisor"))
_FUNERARIAS = {"749/18", "761/19"}
_URL_SOECRA = "https://soecra.com.ar/ddjj-empresas/"


def _unidad_lsd(valor: str) -> str:
    u = str(valor or "").strip().lower()
    if u in {"%", "porcentaje"}:
        return "%"
    if u in {"h", "hora", "horas"}:
        return "H"
    if u in {"d", "día", "dia", "días", "dias"}:
        return "D"
    return "$"


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


def _unidad_lsd(unidad: str) -> str:
    u = str(unidad or "").lower()
    if "%" in u:
        return "%"
    if "hora" in u:
        return "H"
    if "día" in u or "dia" in u:
        return "D"
    if "mes" in u:
        return "M"
    return "$"


def _faltantes(carpeta: m.CarpetaMensual) -> list[dict]:
    _, snapshot, detalles = _datos(carpeta)
    empleados = snapshot.get("empleados", {})
    faltantes: list[dict] = []
    for detalle in detalles:
        eid = str(detalle.get("empleado_id", ""))
        foto = empleados.get(eid, {})
        perfil = foto.get("perfil_arca", {})
        for campo in faltantes_perfil(perfil):
            faltantes.append({"empleado_id": eid, "campo": campo})
        doc = foto.get("documental", {})
        if not doc.get("forma_pago"):
            faltantes.append({"empleado_id": eid, "campo": "forma_pago"})
        if doc.get("forma_pago") == "3" and len("".join(filter(str.isdigit, doc.get("cbu", "")))) != 22:
            faltantes.append({"empleado_id": eid, "campo": "cbu_22_digitos"})
        for concepto in detalle.get("conceptos", []):
            if str(concepto.get("tipo", "")).upper() == "CONTRIBUCION":
                continue
            codigo = str(concepto.get("codigo", ""))
            try:
                codigo_empleador(codigo)
                codigo_tipo_arca(codigo)
            except ValueError as exc:
                faltantes.append({
                    "empleado_id": eid, "campo": "concepto_arca",
                    "concepto": codigo, "motivo": str(exc),
                })
        if not detalle.get("bases_lsd"):
            faltantes.append({
                "empleado_id": eid, "campo": "bases_lsd",
                "motivo": detalle.get("error_lsd") or "No fueron fotografiadas",
            })
    empresa = snapshot.get("empresa", {})
    if len("".join(ch for ch in str(empresa.get("cuit", "")) if ch.isdigit())) != 11:
        faltantes.append({"campo": "cuit_empleador"})
    return faltantes


@router.get("/carpetas/{carpeta_id}/arca-control")
async def control_arca(carpeta_id: str, principal: Principal = _ROLES):
    async with tenant_session(principal.tenant_id) as s:
        carpeta = await _carpeta(s, carpeta_id)
        faltantes = _faltantes(carpeta)
        return {
            "listo_para_txt": not faltantes,
            "periodo": carpeta.periodo, "version": carpeta.version,
            "faltantes": faltantes,
            "proximo_paso": (
                "Descargar TXT ARCA" if not faltantes
                else "Completar los datos indicados y volver a liquidar para fotografiarlos"
            ),
            "aclaracion": (
                "ARCA valida el TXT; después de aceptar la liquidación genera la declaración F.931."
            ),
        }


@router.get("/carpetas/{carpeta_id}/arca.txt")
async def descargar_arca(
    carpeta_id: str,
    fecha_pago: date = Query(...),
    fecha_rubrica: date | None = Query(default=None),
    numero_liquidacion: int = Query(default=1, ge=1, le=99999),
    principal: Principal = _ROLES,
):
    async with tenant_session(principal.tenant_id) as s:
        carpeta = await _carpeta(s, carpeta_id)
        faltantes = _faltantes(carpeta)
        if faltantes:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                {"mensaje": "El TXT ARCA está bloqueado", "faltantes": faltantes},
            )
        _, snapshot, detalles = _datos(carpeta)
        empresa = snapshot["empresa"]
        fotos = snapshot["empleados"]
        trabajadores = []
        for detalle in detalles:
            eid = str(detalle["empleado_id"])
            foto, doc = fotos[eid], fotos[eid]["documental"]
            perfil = foto["perfil_arca"]
            conceptos = []
            total_haberes = Decimal("0")
            for c in detalle.get("conceptos", []):
                tipo = str(c.get("tipo", "")).upper()
                if tipo == "CONTRIBUCION":
                    continue
                codigo = str(c["codigo"])
                importe = Decimal(str(c["importe"]))
                if tipo not in {"DEDUCCION", "DESCUENTO"}:
                    total_haberes += importe
                conceptos.append(ConceptoLSD(
                    codigo=codigo_empleador(codigo),
                    importe=importe,
                    signo="D" if tipo in {"DEDUCCION", "DESCUENTO"} else "C",
                    cantidad=Decimal(str(c.get("cantidad") or 0)),
                    unidad=_unidad_lsd(c.get("unidad", "")),
                ))
            trabajadores.append(TrabajadorLSD(
                cuil=doc["cuil"], legajo=doc.get("legajo", ""),
                dependencia_revista=doc.get("lugar_trabajo", ""),
                cbu=doc.get("cbu", ""), dias_tope=int(perfil["dias_trabajados"]),
                fecha_pago=fecha_pago.strftime("%Y%m%d"),
                fecha_rubrica=fecha_rubrica.strftime("%Y%m%d") if fecha_rubrica else "",
                forma_pago=doc["forma_pago"], conceptos=conceptos,
                attrs_suss=construir_atributos_suss(
                    perfil, conyuge=bool(doc.get("conyuge_a_cargo", False)),
                    hijos=int(doc.get("cantidad_hijos", 0)), tiene_cct=bool(doc.get("cct_numero")),
                ),
                remun_total=total_haberes,
                bases=[Decimal(str(v)) for v in detalle["bases_lsd"]],
            ))
        empleador = EmpleadorLSD(
            cuit=empresa["cuit"], periodo=carpeta.periodo.replace("-", ""),
            tipo_liq="M", nro_liq=numero_liquidacion, dias_base=30,
        )
        contenido = build_lsd_bytes(empleador, trabajadores)
        nombre = f"ARCA-LSD-{carpeta.periodo}-v{carpeta.version}.txt"
        return Response(
            contenido, media_type="text/plain; charset=iso-8859-1",
            headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
        )


@router.get("/carpetas/{carpeta_id}/soecra.csv")
async def planilla_soecra(carpeta_id: str, principal: Principal = _ROLES):
    async with tenant_session(principal.tenant_id) as s:
        carpeta = await _carpeta(s, carpeta_id)
        _, snapshot, detalles = _datos(carpeta)
        empleados, empresa = snapshot.get("empleados", {}), snapshot.get("empresa", {})
        filas = []
        for detalle in detalles:
            cct = detalle.get("cct_numero", "")
            if cct not in _FUNERARIAS:
                continue
            eid = str(detalle.get("empleado_id", ""))
            doc = empleados.get(eid, {}).get("documental", {})
            remunerativo = no_remunerativo = sindical = Decimal("0")
            for concepto in detalle.get("conceptos", []):
                importe = Decimal(str(concepto.get("importe", 0)))
                tipo = str(concepto.get("tipo", "")).upper()
                if tipo == "REMUNERATIVO":
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
