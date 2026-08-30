"""Rutas de convenios (CCT): listado con categorías vigentes para la UI."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from api.dependencies.auth import Principal, require_tenant
from infrastructure.database import models as m
from infrastructure.database.session import plain_session
from domain.entities.farmacia_414_05 import CATEGORIAS_FARMACIA, CCT_FARMACIA
from domain.entities.encuadramiento_asistido import sugerir_encuadramiento
from infrastructure.excel.normativa_importer import (
    generar_plantilla_normativa,
    vista_previa_normativa,
)

router = APIRouter(prefix="/convenios", tags=["convenios"])


class ConsultaEncuadramiento(BaseModel):
    actividad: str = Field(default="", max_length=200)
    localidad: str = Field(default="", max_length=120)
    provincia: str = Field(default="", max_length=120)
    tarea: str = Field(default="", max_length=500)


@router.post("/asistente-encuadramiento")
async def asistente_encuadramiento(
    body: ConsultaEncuadramiento,
    _: Principal = Depends(require_tenant),
):
    """Propone CCT explicables; nunca modifica el legajo por sí solo."""
    resultado = sugerir_encuadramiento(
        body.actividad, body.localidad, body.tarea, body.provincia
    )
    async with plain_session() as s:
        categorias = (await s.execute(select(m.CctCategoria).where(
            m.CctCategoria.activa.is_(True)
        ))).scalars().all()
    por_cct: dict[str, list[str]] = {}
    for categoria in categorias:
        por_cct.setdefault(categoria.cct_numero, []).append(categoria.nombre)
    for candidato in resultado["candidatos"]:
        candidato["categorias"] = sorted(por_cct.get(candidato["cct_numero"], []))
    return resultado


@router.get("/paquetes")
async def paquetes_instalados(_: Principal = Depends(require_tenant)):
    """Versiones instaladas por la fábrica, con huella auditable."""
    async with plain_session() as s:
        filas = (await s.execute(
            select(m.CctPaqueteVersion).order_by(
                m.CctPaqueteVersion.cct_numero,
                m.CctPaqueteVersion.instalado_at.desc(),
            )
        )).scalars().all()
    return [{
        "cct_numero": x.cct_numero,
        "version": x.paquete_version,
        "hash_sha256": x.hash_sha256,
        "estado": x.estado,
        "resumen": x.resumen,
        "fuente_manifest": x.fuente_manifest,
        "instalado_at": x.instalado_at,
    } for x in filas]


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


@router.get("/gestor-normativo")
async def gestor_normativo(
    periodo: str = Query(..., description="Período AAAA-MM"),
    _: Principal = Depends(require_tenant),
):
    """Tablero: estructura estable separada de los valores del período."""
    fecha = _fecha_periodo(periodo)
    async with plain_session() as s:
        ccts = (await s.execute(
            select(m.Cct).where(m.Cct.activo.is_(True)).order_by(m.Cct.numero)
        )).scalars().all()
        categorias = (await s.execute(select(m.CctCategoria).where(
            m.CctCategoria.activa.is_(True)
        ))).scalars().all()
        reglas = (await s.execute(select(m.CctReglaEstructural).where(
            m.CctReglaEstructural.activa.is_(True)
        ))).scalars().all()
        escalas = (await s.execute(select(m.EscalaSalarial).where(
            m.EscalaSalarial.valid_from <= fecha,
            (m.EscalaSalarial.valid_to.is_(None)) | (m.EscalaSalarial.valid_to >= fecha),
        ))).scalars().all()
        parametros = (await s.execute(select(m.ParametroLegal).where(
            m.ParametroLegal.cct_numero.is_not(None),
            m.ParametroLegal.valid_from <= fecha,
            (m.ParametroLegal.valid_to.is_(None)) | (m.ParametroLegal.valid_to >= fecha),
        ))).scalars().all()
        escalas_historicas = (await s.execute(select(
            m.EscalaSalarial.cct_numero, m.EscalaSalarial.categoria,
            m.EscalaSalarial.is_verified, m.EscalaSalarial.fuente,
        ))).all()

    salida = []
    for cct in ccts:
        cats = [c for c in categorias if c.cct_numero == cct.numero]
        regs = [r for r in reglas if r.cct_numero == cct.numero]
        esc = [e for e in escalas if e.cct_numero == cct.numero]
        par = [p for p in parametros if p.cct_numero == cct.numero]
        estructura_registrada = bool(cats)
        if estructura_registrada:
            nombres_categorias = {c.nombre for c in cats}
            cats_ok = sum(1 for c in cats if c.is_verified and c.fuente.strip())
        else:
            historicas = [e for e in escalas_historicas if e.cct_numero == cct.numero]
            nombres_categorias = {e.categoria for e in historicas}
            cats_ok = sum(1 for nombre in nombres_categorias if any(
                e.categoria == nombre and e.is_verified and (e.fuente or '').strip()
                for e in historicas
            ))
        # Cuando existe un padrón estructural, una escala histórica cuya
        # categoría ya no está activa no forma parte de la cobertura actual.
        # Se conserva en la base, pero no debe sumar ni bloquear el semáforo.
        if estructura_registrada:
            esc = [e for e in esc if e.categoria in nombres_categorias]
        # Una categoría puede conservar más de una versión histórica/solapada.
        # El semáforo cuenta coberturas únicas, no filas físicas, para no mostrar
        # 248/247 ni bloquear un motor por un duplicado legado.
        esc_ok = len({
            (e.categoria, getattr(e, "zona", "") or "") for e in esc
            if e.is_verified and e.fuente.strip()
        })
        esc_habilitadas = len({
            (e.categoria, getattr(e, "zona", "") or "") for e in esc
            if e.is_verified and e.fuente.strip()
            and getattr(e, "habilitada_liquidacion", True)
        })
        estructura_completa = estructura_registrada and bool(nombres_categorias) and cats_ok == len(nombres_categorias) and bool(regs) and all(
            r.is_verified and r.fuente.strip() for r in regs
        )
        regla_zona = next((r for r in regs if r.codigo in {
            "ZONIFICACION", "COEFICIENTES_TERRITORIALES"
        } and r.is_verified), None)
        zonas_config = (regla_zona.configuracion or {}).get("zonas", {}) if regla_zona else {}
        if regla_zona and zonas_config:
            zonas_validas = (
                set(zonas_config)
                if isinstance(zonas_config, dict)
                else set(zonas_config)
            )
            esc = [e for e in esc if (getattr(e, "zona", "") or "") in zonas_validas]
            esc_ok = len({
                (e.categoria, getattr(e, "zona", "") or "") for e in esc
                if e.is_verified and e.fuente.strip()
            })
            esc_habilitadas = len({
                (e.categoria, getattr(e, "zona", "") or "") for e in esc
                if e.is_verified and e.fuente.strip()
                and getattr(e, "habilitada_liquidacion", True)
            })
        cantidad_zonas = len(zonas_config) if zonas_config else 1
        escalas_esperadas = len(nombres_categorias) * max(cantidad_zonas, 1)
        escala_completa = bool(nombres_categorias) and esc_ok == escalas_esperadas
        motor_periodo_habilitado = escala_completa and esc_habilitadas == escalas_esperadas
        vista_previa_habilitada = False
        if cct.numero in {"260/75", "40/89"} and estructura_completa and escala_completa:
            vista_previa_habilitada = not motor_periodo_habilitado
        if estructura_completa and escala_completa and motor_periodo_habilitado:
            estado = "completo"
        elif esc or par:
            estado = "parcial"
        else:
            estado = "pendiente"
        salida.append({
            "numero": cct.numero, "nombre": cct.nombre, "sindicato": cct.sindicato,
            "periodo": periodo, "estado": estado,
            "estructura": {
                "categorias": len(nombres_categorias), "categorias_verificadas": cats_ok,
                "reglas": len(regs), "registrada": estructura_registrada,
                "completa": estructura_completa,
            },
            "periodo_actual": {
                "escalas": len({(e.categoria, getattr(e, "zona", "") or "") for e in esc}),
                "escalas_verificadas": esc_ok,
                "escalas_habilitadas": esc_habilitadas,
                "escalas_esperadas": escalas_esperadas,
                "parametros": len(par), "completa": escala_completa,
                "motor_habilitado": motor_periodo_habilitado,
                "vista_previa_habilitada": vista_previa_habilitada,
                "mensaje_motor": (
                    "Disponibles: general, larga distancia, lácteos, auxilio, diarios, combustibles y sustancias peligrosas; otras ramas pendientes"
                    if cct.numero == "40/89" and vista_previa_habilitada else None
                ),
            },
        })
    return salida


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


def _estado_item(
    tipo: str,
    codigo: str,
    verificado: bool,
    fuente: str,
    estado_fuente: str = "PENDIENTE_DOCUMENTACION",
    habilitado: bool = True,
) -> dict:
    problemas = []
    if not verificado:
        problemas.append("pendiente de aprobación profesional")
    if not (fuente or "").strip():
        problemas.append("fuente legal faltante")
    if not habilitado:
        problemas.append("dato documentado, motor de liquidación pendiente")
    return {
        "tipo": tipo,
        "codigo": codigo,
        "verificado": bool(verificado),
        "fuente": fuente or "",
        "estado_fuente": estado_fuente,
        "habilitado_liquidacion": habilitado,
        "problemas": problemas,
    }


@router.get("")
async def listar(
    periodo: str | None = Query(None, description="Período AAAA-MM"),
    _: Principal = Depends(require_tenant),
):
    """Convenios activos y categorías vigentes para el período solicitado."""
    fecha = _fecha_periodo(periodo) if periodo else date.today()
    async with plain_session() as s:
        ccts = (await s.execute(
            select(m.Cct).where(m.Cct.activo.is_(True)).order_by(m.Cct.numero)
        )).scalars().all()
        filas = (await s.execute(
            select(
                m.EscalaSalarial.cct_numero,
                m.EscalaSalarial.categoria,
                m.EscalaSalarial.is_verified,
                m.EscalaSalarial.fuente,
                m.EscalaSalarial.valid_from,
                m.EscalaSalarial.valid_to,
            ).distinct()
        )).all()
        categorias_estructurales = (await s.execute(
            select(m.CctCategoria).where(m.CctCategoria.activa.is_(True))
        )).scalars().all()
    cats: dict[str, dict[str, dict]] = {}
    vigentes: set[tuple[str, str]] = set()
    for numero, categoria, verificada, fuente, valid_from, valid_to in filas:
        estado = cats.setdefault(numero, {}).setdefault(
            categoria,
            {"nombre": categoria, "verificada": False, "fuentes": set()},
        )
        estado["verificada"] = estado["verificada"] or bool(verificada)
        if (fuente or "").strip():
            estado["fuentes"].add(fuente.strip())
        if valid_from <= fecha and (valid_to is None or valid_to >= fecha):
            vigentes.add((numero, categoria))
    for categoria in categorias_estructurales:
        estado = cats.setdefault(categoria.cct_numero, {}).setdefault(
            categoria.nombre,
            {"nombre": categoria.nombre, "verificada": False, "fuentes": set()},
        )
        estado["verificada"] = estado["verificada"] or categoria.is_verified
        if categoria.fuente.strip():
            estado["fuentes"].add(categoria.fuente.strip())

    salida = []
    for c in ccts:
        detalles = []
        for item in sorted(cats.get(c.numero, {}).values(), key=lambda x: x["nombre"]):
            detalles.append({
                "nombre": item["nombre"],
                "verificada": item["verificada"],
                "fuentes": sorted(item["fuentes"]),
                "escala_vigente": (c.numero, item["nombre"]) in vigentes,
            })
        salida.append({
            "numero": c.numero,
            "nombre": c.nombre,
            "sindicato": c.sindicato,
            "periodo": periodo or fecha.strftime("%Y-%m"),
            "categorias": [item["nombre"] for item in detalles],
            "categorias_detalle": detalles,
            "tiene_escala_vigente": any(item["escala_vigente"] for item in detalles),
        })
    # El padrón laboral no depende de que Supabase ya tenga una escala monetaria
    # del mes. Esto permite encuadrar el legajo y mantiene bloqueada, por separado,
    # una liquidación sin escala vigente.
    if not any(item["numero"] == CCT_FARMACIA for item in salida):
        salida.append({
            "numero": CCT_FARMACIA,
            "nombre": "Farmacia",
            "sindicato": "ADEF",
            "periodo": periodo or fecha.strftime("%Y-%m"),
            "categorias": list(CATEGORIAS_FARMACIA),
            "categorias_detalle": [
                {"nombre": nombre, "verificada": True, "fuentes": ["CCT 414/05 art. 7"],
                 "escala_vigente": False}
                for nombre in CATEGORIAS_FARMACIA
            ],
            "tiene_escala_vigente": False,
        })
    salida.sort(key=lambda item: item["numero"])
    return salida


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
        _estado_item(
            "escala", f"{e.categoria} v{e.version}", e.is_verified, e.fuente,
            e.estado_fuente, e.habilitada_liquidacion,
        )
        for e in escalas
    ]
    items += [
        _estado_item(
            "parametro", f"{p.codigo} v{p.version}", p.is_verified, p.fuente,
            p.estado_fuente,
        )
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
