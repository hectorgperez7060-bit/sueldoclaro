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
from domain.entities.parametros import ParametroLegal as ParamDom
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo
from infrastructure.database.repositories import (
    AuditRepo,
    EmpleadoRepo,
    LiquidacionRepo,
    ParametrosRepo,
)
from infrastructure.database.session import tenant_session


class LiquidarPeriodo:
    async def ejecutar(self, tenant_id: str, periodo_str: str, tipo: str,
                       novedades: Dict[str, dict], usuario_id: str) -> dict:
        periodo = Periodo.desde_texto(periodo_str)
        fecha_ref = date(periodo.anio, periodo.mes, 28)

        async with tenant_session(tenant_id) as s:
            params_repo = ParametrosRepo(s)
            parametros = await params_repo.parametro_set(fecha_ref)

            empleados = await EmpleadoRepo(s).listar()
            liq_repo = LiquidacionRepo(s)

            snapshot = {"periodo": periodo_str, "generado": fecha_ref.isoformat(), "empleados": {}}
            liq = await liq_repo.crear(uuid.UUID(tenant_id), periodo_str, tipo, snapshot)

            detalles_out = []
            for emp in empleados:
                cct_cfg = await params_repo.cct_config(emp.cct_numero)
                escala = await params_repo.escala(emp.cct_numero, emp.categoria, fecha_ref)
                amparos = await params_repo.amparos(emp.cct_numero)
                if cct_cfg is None or escala is None:
                    continue  # sin parámetros no se liquida a este empleado

                # Cuota Art.101 (afiliados): el repositorio la resuelve por
                # CCT + localidad/filial y la inyecta como ded_afil. Si no hay
                # cuota oficial verificada, NO se aplica ningun % y se avisa.
                aviso_art101 = None
                params_emp = parametros
                if emp.afiliado_sindicato:
                    cuota = await params_repo.resolver_art101(
                        emp.cct_numero, emp.localidad, emp.filial_sindical, fecha_ref)
                    if cuota is not None:
                        params_emp = parametros.con_extra(ParamDom(
                            f"CUOTA_SINDICAL_ART101_{emp.cct_numero}", cuota.porcentaje, "%",
                            "ded_afil", cuota.valid_from, cuota.valid_to, True, cuota.fuente,
                            emp.cct_numero, {}))
                    else:
                        aviso_art101 = ("Cuota sindical de afiliado pendiente de verificar "
                                        "para esta localidad/filial")
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
                nv = novedades.get(str(emp.id), {})
                res = motor.liquidar_mensual(
                    dom_emp, periodo, escala, cct_cfg,
                    Novedades(
                        horas_extra_50=Decimal(str(nv.get("horas_extra_50", "0"))),
                        horas_extra_100=Decimal(str(nv.get("horas_extra_100", "0"))),
                    ),
                    a_fecha=fecha_ref,
                )
                conceptos = [
                    {
                        "codigo": c.codigo, "descripcion": c.descripcion, "tipo": c.tipo.value,
                        "importe": str(c.importe.redondear().monto), "regimen": c.regimen.value,
                        "articulo_amparo": c.articulo_amparo,
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
                }
                detalles_out.append({
                    "empleado_id": str(emp.id),
                    "bruto": str(res.bruto.monto),
                    "total_deducciones": str(res.total_deducciones.monto),
                    "neto": str(res.neto.monto),
                    "conceptos": conceptos,
                    "aviso_art101": aviso_art101,
                })

            # Reasignar un objeto nuevo fuerza la detección de cambios de JSONB
            # (sin MutableDict, las mutaciones in-place no se marcan dirty).
            liq.snapshot_parametros = dict(snapshot)
            await AuditRepo(s).registrar(
                accion="liquidar", entidad="liquidacion", entidad_id=str(liq.id),
                tenant_id=uuid.UUID(tenant_id), usuario_id=uuid.UUID(usuario_id),
                payload_diff={"periodo": periodo_str, "detalles": len(detalles_out)},
            )
            return {
                "id": str(liq.id), "periodo": periodo_str, "tipo": tipo,
                "estado": liq.estado, "detalles": detalles_out,
            }
