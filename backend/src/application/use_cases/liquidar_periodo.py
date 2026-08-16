"""Caso de uso: liquidar un período (usa el motor puro de la Fase 1).

Persiste la liquidación con un snapshot inmutable de los parámetros usados
(reproducibilidad histórica: sección 6.5 del prompt).
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Dict

from domain.entities.empleado import Empleado
from domain.entities.carpeta_mensual import construir_contenido_carpeta, huella_carpeta
from domain.entities.parametros import ParametroLegal as ParamDom
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo
from infrastructure.database.repositories import (
    AuditRepo,
    CarpetaMensualRepo,
    EmpleadoRepo,
    LiquidacionRepo,
    NovedadMensualRepo,
    ParametrosRepo,
)
from infrastructure.database.session import tenant_session


def resolver_horas_extra(
    empleados: list,
    novedades_guardadas: list,
    novedades_legacy: Dict[str, dict],
) -> Dict[str, dict]:
    """Novedad persistida manda; el body anterior queda como compatibilidad."""
    ids_validos = {str(emp.id) for emp in empleados}
    res = {
        empleado_id: {
            "horas_extra_50": Decimal(str(datos.get("horas_extra_50", "0"))),
            "horas_extra_100": Decimal(str(datos.get("horas_extra_100", "0"))),
            "origen": "body_legacy",
            "premio": Decimal("0"), "tipo_premio": "pendiente",
            "descuento_adicional": Decimal("0"), "detalle_descuento": "",
            "adicionales_convencionales": (), "cantidades_adicionales": (),
        }
        for empleado_id, datos in novedades_legacy.items()
        if empleado_id in ids_validos
    }
    for novedad in novedades_guardadas:
        res[str(novedad.empleado_id)] = {
            "horas_extra_50": Decimal(novedad.horas_extra_50 or 0),
            "horas_extra_100": Decimal(novedad.horas_extra_100 or 0),
            "origen": "novedad_mensual",
            "novedad_id": str(novedad.id),
            "premio": Decimal(novedad.premios or 0),
            "tipo_premio": novedad.tipo_premio or "pendiente",
            "descuento_adicional": Decimal(novedad.descuentos_adicionales or 0),
            "detalle_descuento": novedad.observaciones or "",
            "adicionales_convencionales": tuple(
                getattr(novedad, "adicionales_convencionales", None) or []
            ),
            "cantidades_adicionales": tuple(
                (codigo, Decimal(str(cantidad)))
                for codigo, cantidad in (
                    getattr(novedad, "cantidades_adicionales", None) or {}
                ).items()
            ),
        }
    return res


class LiquidarPeriodo:
    async def ejecutar(self, tenant_id: str, periodo_str: str, tipo: str,
                       novedades: Dict[str, dict], usuario_id: str) -> dict:
        periodo = Periodo.desde_texto(periodo_str)
        fecha_ref = date(periodo.anio, periodo.mes, 28)

        async with tenant_session(tenant_id) as s:
            params_repo = ParametrosRepo(s)
            parametros = await params_repo.parametro_set(fecha_ref)

            empleados = await EmpleadoRepo(s).listar()
            novedades_guardadas = await NovedadMensualRepo(s).listar_periodo(
                uuid.UUID(tenant_id), periodo_str
            )
            horas_extra = resolver_horas_extra(empleados, novedades_guardadas, novedades)
            liq_repo = LiquidacionRepo(s)

            snapshot = {"periodo": periodo_str, "generado": fecha_ref.isoformat(), "empleados": {}}
            liq = await liq_repo.crear(uuid.UUID(tenant_id), periodo_str, tipo, snapshot)

            detalles_out = []
            for emp in empleados:
                cct_cfg = await params_repo.cct_config(emp.cct_numero, fecha_ref)
                escala = await params_repo.escala(emp.cct_numero, emp.categoria, fecha_ref)
                amparos = await params_repo.amparos(emp.cct_numero)
                if cct_cfg is None or escala is None:
                    continue  # sin parámetros no se liquida a este empleado

                # Cuota Art.101 (afiliados): el repositorio la resuelve por
                # CCT + localidad/filial y la inyecta como ded_afil. Si no hay
                # cuota oficial verificada, NO se aplica ningun % y se avisa.
                aviso_cuota_afiliado = None
                params_emp = parametros
                if emp.afiliado_sindicato:
                    cuota = await params_repo.resolver_art101(
                        emp.cct_numero, emp.localidad, emp.filial_sindical, fecha_ref)
                    if cuota is not None:
                        if emp.cct_numero == "414/05":
                            codigo_cuota = "CUOTA_SINDICAL_ART47_414/05"
                            incidencias_cuota = {
                                "base_deduccion": "sindical",
                                "destino_pago": "ADEF",
                                "codigo_boleta": "ADEF_APORTES",
                                "absorbe_codigos": [
                                    "APORTE_ADEF_REM_414/05",
                                    "APORTE_ADEF_NR_414/05",
                                ],
                            }
                        elif emp.cct_numero == "122/75":
                            codigo_cuota = "CUOTA_SINDICAL_FATSA_122/75"
                            incidencias_cuota = {
                                "base_deduccion": "sindical",
                                "destino_pago": "FATSA",
                                "codigo_boleta": "FATSA_122_APORTES",
                                "absorbe_codigos": ["APORTE_SOLIDARIO_FATSA_122/75"],
                            }
                        else:
                            codigo_cuota = f"CUOTA_SINDICAL_ART101_{emp.cct_numero}"
                            incidencias_cuota = {}
                        params_emp = parametros.con_extra(ParamDom(
                            codigo_cuota, cuota.porcentaje, "%", "ded_afil",
                            cuota.valid_from, cuota.valid_to, True, cuota.fuente,
                            emp.cct_numero, incidencias_cuota))
                    else:
                        articulo = {
                            "414/05": "art. 47 ADEF",
                            "122/75": "cuota asociacional del sindicato FATSA correspondiente",
                        }.get(emp.cct_numero, "art. 101")
                        aviso_cuota_afiliado = (
                            f"Cuota sindical de afiliado ({articulo}) pendiente de verificar "
                            "para esta localidad/filial"
                        )
                motor = MotorLiquidacion(params_emp, amparos)
                dom_emp = Empleado(
                    nombre=emp.nombre, apellido=emp.apellido, cuil=Cuil(emp.cuil),
                    fecha_ingreso=emp.fecha_ingreso, cct_numero=emp.cct_numero,
                    categoria=emp.categoria, legajo=emp.legajo,
                    remuneracion_pactada=Dinero(Decimal(emp.remuneracion_pactada)) if emp.remuneracion_pactada else None,
                    afiliado_sindicato=emp.afiliado_sindicato,
                    proporcion_jornada=Decimal(emp.proporcion_jornada or 1),
                    localidad=emp.localidad,
                    filial_sindical=emp.filial_sindical,
                )
                nv = horas_extra.get(str(emp.id), {})
                res = motor.liquidar_mensual(
                    dom_emp, periodo, escala, cct_cfg,
                    Novedades(
                        horas_extra_50=Decimal(str(nv.get("horas_extra_50", "0"))),
                        horas_extra_100=Decimal(str(nv.get("horas_extra_100", "0"))),
                        premio=Decimal(str(nv.get("premio", "0"))),
                        tipo_premio=nv.get("tipo_premio", "pendiente"),
                        descuento_adicional=Decimal(str(nv.get("descuento_adicional", "0"))),
                        detalle_descuento=nv.get("detalle_descuento", ""),
                        adicionales_convencionales=nv.get("adicionales_convencionales", ()),
                        cantidades_adicionales=nv.get("cantidades_adicionales", ()),
                    ),
                    a_fecha=fecha_ref,
                )
                conceptos = [
                    {
                        "codigo": c.codigo, "descripcion": c.descripcion, "tipo": c.tipo.value,
                        "importe": str(c.importe.redondear().monto), "regimen": c.regimen.value,
                        "articulo_amparo": c.articulo_amparo,
                        "destino_pago": c.destino_pago,
                        "codigo_boleta": c.codigo_boleta,
                        "canal_pago": c.canal_pago,
                        "url_pago": c.url_pago,
                        "regla_vencimiento": c.regla_vencimiento,
                        "fuente_pago": c.fuente_pago,
                    }
                    for c in res.conceptos
                ]
                await liq_repo.agregar_detalle(
                    uuid.UUID(tenant_id), liq.id, emp.id, conceptos,
                    bruto=res.bruto.monto, deducciones=res.total_deducciones.monto, neto=res.neto.monto,
                )
                snapshot["empleados"][str(emp.id)] = {
                    "cct": emp.cct_numero, "categoria": emp.categoria,
                    "basico": str(escala.basico.monto),
                    "amparos": [a[0] + ":" + (a[2] or "") for a in res.regimenes_aplicados()],
                    "novedades": {
                        "horas_extra_50": str(nv.get("horas_extra_50", "0")),
                        "horas_extra_100": str(nv.get("horas_extra_100", "0")),
                        "origen": nv.get("origen", "sin_novedades"),
                        "novedad_id": nv.get("novedad_id"),
                        "premio": str(nv.get("premio", "0")),
                        "tipo_premio": nv.get("tipo_premio", "pendiente"),
                        "descuento_adicional": str(nv.get("descuento_adicional", "0")),
                        "adicionales_convencionales": list(
                            nv.get("adicionales_convencionales", ())
                        ),
                        "cantidades_adicionales": {
                            codigo: str(cantidad)
                            for codigo, cantidad in nv.get("cantidades_adicionales", ())
                        },
                    },
                }
                detalles_out.append({
                    "empleado_id": str(emp.id),
                    "cct_numero": emp.cct_numero,
                    "localidad": emp.localidad,
                    "filial_sindical": emp.filial_sindical,
                    "bruto": str(res.bruto.monto),
                    "total_deducciones": str(res.total_deducciones.monto),
                    "neto": str(res.neto.monto),
                    "conceptos": conceptos,
                    "aviso_cuota_afiliado": aviso_cuota_afiliado,
                    "aviso_art101": aviso_cuota_afiliado,
                })

            # Reasignar un objeto nuevo fuerza la detección de cambios de JSONB
            # (sin MutableDict, las mutaciones in-place no se marcan dirty).
            liq.snapshot_parametros = dict(snapshot)
            reglas_pendientes = []
            for p in parametros.pendientes_normativos():
                reglas_pendientes.append({
                    "codigo": p.codigo,
                    "cct_numero": p.cct_numero,
                    "verificado": p.is_verified,
                    "fuente": p.fuente,
                })
            contenido_carpeta = construir_contenido_carpeta(
                periodo=periodo_str, tipo=tipo, liquidacion_id=str(liq.id),
                detalles=detalles_out, snapshot=dict(snapshot),
                reglas_pendientes=reglas_pendientes,
            )
            carpeta = await CarpetaMensualRepo(s).crear_calculada(
                uuid.UUID(tenant_id), periodo_str, liq.id,
                contenido_carpeta, huella_carpeta(contenido_carpeta),
            )
            await AuditRepo(s).registrar(
                accion="liquidar", entidad="liquidacion", entidad_id=str(liq.id),
                tenant_id=uuid.UUID(tenant_id), usuario_id=uuid.UUID(usuario_id),
                payload_diff={"periodo": periodo_str, "detalles": len(detalles_out)},
            )
            await AuditRepo(s).registrar(
                accion="crear", entidad="carpeta_mensual", entidad_id=str(carpeta.id),
                tenant_id=uuid.UUID(tenant_id), usuario_id=uuid.UUID(usuario_id),
                payload_diff={
                    "periodo": periodo_str, "version": carpeta.version,
                    "estado": carpeta.estado, "hash_sha256": carpeta.hash_sha256,
                },
            )
            return {
                "id": str(liq.id), "periodo": periodo_str, "tipo": tipo,
                "estado": liq.estado, "detalles": detalles_out,
                "carpeta_mensual": {
                    "id": str(carpeta.id), "version": carpeta.version,
                    "estado": carpeta.estado, "hash_sha256": carpeta.hash_sha256,
                    "apto_produccion": contenido_carpeta["control_normativo"]["apto_produccion"],
                },
            }
