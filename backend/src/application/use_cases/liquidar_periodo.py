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
from domain.entities.carpeta_mensual import (
    construir_contenido_carpeta, huella_carpeta, obligaciones_desde_contenido,
)
from domain.entities.escala_verificada import evaluar_escala
from domain.entities.parametros import ParametroLegal as ParamDom
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.payroll_engine.uom import (
    armar_recibo_uom, calcular_adicional_uom, calcular_base_uom, calcular_compensacion_abril_julio_uom,
    calcular_complemento_imgr, calcular_gratificacion_uom, habilitar_vista_previa_uom,
)
from domain.payroll_engine.uocra import (
    ComponentesFondoCese, DecisionProfesionalFcl, FeriadoDetalladoUocra,
    HoraExtraDetalladaUocra,
    HechosQuincenalesUocra, TasasAportesUocra, armar_recibo_uocra,
    calcular_aportes_y_contribuciones, calcular_base_quincenal,
    calcular_adicionales_tarea_uocra,
    calcular_feriados_detallados, calcular_fondo_cese,
    calcular_horas_extra_detalladas, resolver_alicuota_fcl,
)
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
    TenantRepo,
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
            "feriados_trabajados": 0,
            "feriados_no_trabajados": 0,
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
            "feriados_trabajados": int(getattr(novedad, "feriados_trabajados", 0) or 0),
            "feriados_no_trabajados": int(getattr(novedad, "feriados_no_trabajados", 0) or 0),
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
            "horas_normales_q1": getattr(novedad, "horas_normales_q1", None),
            "horas_normales_q2": getattr(novedad, "horas_normales_q2", None),
            "asistencia_perfecta_q1": getattr(novedad, "asistencia_perfecta_q1", None),
            "asistencia_perfecta_q2": getattr(novedad, "asistencia_perfecta_q2", None),
            "feriados_uocra_detalle": tuple(getattr(novedad, "feriados_uocra_detalle", None) or []),
            "fcl_criterio_aniversario": getattr(novedad, "fcl_criterio_aniversario", None),
            "fcl_aprobado_por": getattr(novedad, "fcl_aprobado_por", None),
            "fcl_fundamento": getattr(novedad, "fcl_fundamento", None),
            "base_contribucion_uocra_mes_anterior": getattr(
                novedad, "base_contribucion_uocra_mes_anterior", None
            ),
            "horas_extra_uocra_detalle": tuple(
                getattr(novedad, "horas_extra_uocra_detalle", None) or []
            ),
            "horas_extra_uocra_acumuladas_anio": getattr(
                novedad, "horas_extra_uocra_acumuladas_anio", 0
            ),
            "horas_hormigon_manual_uocra": getattr(novedad, "horas_hormigon_manual_uocra", 0),
            "horas_altura_uocra": getattr(novedad, "horas_altura_uocra", 0),
            "altura_metros_uocra": getattr(novedad, "altura_metros_uocra", None),
            "camioneros_detalle": dict(getattr(novedad, "camioneros_detalle", None) or {}),
            "uom_detalle": dict(getattr(novedad, "uom_detalle", None) or {}),
        }
    return res


class LiquidarPeriodo:
    async def ejecutar(self, tenant_id: str, periodo_str: str, tipo: str,
                       novedades: Dict[str, dict], usuario_id: str,
                       confirmar_provisorios: bool = False) -> dict:
        periodo = Periodo.desde_texto(periodo_str)
        fecha_ref = date(periodo.anio, periodo.mes, 28)

        async with tenant_session(tenant_id) as s:
            params_repo = ParametrosRepo(s)
            parametros = await params_repo.parametro_set(fecha_ref)
            empresa = await TenantRepo(s).obtener(uuid.UUID(tenant_id))
            if empresa is None:
                raise ValueError("Empresa no encontrada")
            regimen = empresa.regimen_contribucion_patronal
            tasas_patronales = {
                "PRIVADO_18": (
                    Decimal("0.18"),
                    "ARCA — Ley 27.541 art. 19 inc. b: alícuota patronal 18%",
                ),
                "SERVICIOS_COMERCIO_204": (
                    Decimal("0.204"),
                    "ARCA — Ley 27.541 art. 19 inc. a: alícuota patronal 20,40%",
                ),
            }
            if (
                empresa.condicion_mipyme == "CERTIFICADO_VIGENTE"
                and (
                    empresa.certificado_mipyme_vigente_hasta is None
                    or empresa.certificado_mipyme_vigente_hasta < fecha_ref
                )
            ):
                raise ValueError(
                    "El Certificado MiPyME no está vigente para el período liquidado"
                )
            if regimen not in tasas_patronales:
                raise ValueError(
                    "Completá actividad y situación MiPyME de la empresa antes de liquidar"
                )
            tasa_patronal, fuente_patronal = tasas_patronales[regimen]
            parametros = parametros.con_extra(ParamDom(
                "CONTRIB_JUBILACION", tasa_patronal, "%", "empleador",
                fecha_ref, None, True, fuente_patronal, None,
                {
                    "modo_liquidacion": empresa.modo_liquidacion,
                    "regimen_empresa": regimen,
                    "fundamento_empresa": empresa.fundamento_regimen_patronal,
                },
            ))

            empleados = await EmpleadoRepo(s).listar()
            novedades_guardadas = await NovedadMensualRepo(s).listar_periodo(
                uuid.UUID(tenant_id), periodo_str
            )
            horas_extra = resolver_horas_extra(empleados, novedades_guardadas, novedades)
            liq_repo = LiquidacionRepo(s)

            snapshot = {
                "periodo": periodo_str,
                "generado": fecha_ref.isoformat(),
                "empresa": {
                    # Identificación documental del empleador: sin esto una carpeta
                    # vieja no puede reconstruir el recibo sin volver a pedir datos.
                    "razon_social": empresa.razon_social,
                    "cuit": empresa.cuit,
                    "modo_liquidacion": empresa.modo_liquidacion,
                    "actividad_sector": empresa.actividad_sector,
                    "condicion_mipyme": empresa.condicion_mipyme,
                    "certificado_mipyme_vigente_hasta": (
                        empresa.certificado_mipyme_vigente_hasta.isoformat()
                        if empresa.certificado_mipyme_vigente_hasta else None
                    ),
                    "respaldo_regimen_patronal": empresa.respaldo_regimen_patronal,
                    "regimen_contribucion_patronal": regimen,
                    "fundamento_regimen_patronal": empresa.fundamento_regimen_patronal,
                },
                "empleados": {},
            }
            liq = await liq_repo.crear(uuid.UUID(tenant_id), periodo_str, tipo, snapshot)

            detalles_out = []
            bloqueos = []
            for emp in empleados:
                cct_cfg = await params_repo.cct_config(emp.cct_numero, fecha_ref)
                zona_escala, error_zona = await params_repo.zona_escala(
                    emp.cct_numero, emp.establecimiento_id, fecha_ref
                )
                if error_zona:
                    bloqueos.append({
                        "empleado_id": str(emp.id), "cct_numero": emp.cct_numero,
                        "categoria": emp.categoria, "provisorio": False,
                        "requiere_confirmacion": False, "motivo": error_zona,
                    })
                    continue
                escala = await params_repo.escala(
                    emp.cct_numero, emp.categoria, fecha_ref, zona_escala
                )
                amparos = await params_repo.amparos(emp.cct_numero)
                vista_previa_contador = bool(
                    emp.cct_numero == "260/75" and escala is not None
                    and escala.is_verified
                    and not getattr(escala, "habilitada_liquidacion", True)
                )
                escala_documentada = escala
                vigente_uom = (
                    habilitar_vista_previa_uom(escala_documentada)
                    if vista_previa_contador else escala
                )

                # Regla GENERAL (cualquier CCT/categoría/período): solo se usa
                # una escala vigente verificada o una fila provisoria vigente
                # confirmada expresamente. Nunca se estima ni se pone en cero.
                escala_provisoria = None
                evaluacion = evaluar_escala(
                    vigente_uom, confirmado=confirmar_provisorios
                )
                if cct_cfg is None or not evaluacion.puede_liquidar:
                    bloqueos.append({
                        "empleado_id": str(emp.id),
                        "cct_numero": emp.cct_numero,
                        "categoria": emp.categoria,
                        "provisorio": evaluacion.provisorio,
                        "requiere_confirmacion": evaluacion.requiere_confirmacion,
                        "motivo": (
                            "Falta la configuración del convenio para el período"
                            if cct_cfg is None else (evaluacion.motivo or evaluacion.nota)
                        ),
                    })
                    continue  # no se liquida a este empleado (sin cero ni estimación)
                escala = evaluacion.escala
                if evaluacion.provisorio:
                    escala_provisoria = {
                        "nota": evaluacion.nota,
                        "escala_desde": escala.valid_from.isoformat(),
                    }

                sin_regla_jornada = parametros.conceptos_sin_regla_jornada(
                    emp.cct_numero, emp.categoria, emp.proporcion_jornada
                )
                if sin_regla_jornada:
                    bloqueos.append({
                        "empleado_id": str(emp.id),
                        "cct_numero": emp.cct_numero,
                        "categoria": emp.categoria,
                        "provisorio": evaluacion.provisorio,
                        "requiere_confirmacion": False,
                        "motivo": (
                            "No existe una regla verificada para jornada parcial en: "
                            + ", ".join(p.codigo for p in sin_regla_jornada)
                        ),
                    })
                    continue

                # Cuota Art.101 (afiliados): el repositorio la resuelve por
                # CCT + localidad/filial y la inyecta como ded_afil. Si no hay
                # cuota oficial verificada, NO se aplica ningun % y se avisa.
                aviso_cuota_afiliado = None
                cuota_sindical_verificada = None
                params_emp = parametros
                if emp.afiliado_sindicato:
                    cuota = await params_repo.resolver_art101(
                        emp.cct_numero, emp.localidad, emp.filial_sindical, fecha_ref)
                    if cuota is not None:
                        cuota_sindical_verificada = cuota.porcentaje
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
                es_motor_uocra = emp.cct_numero == "76/75"
                es_motor_uom = emp.cct_numero == "260/75"
                if es_motor_uocra:
                    try:
                        base = calcular_base_quincenal(escala, HechosQuincenalesUocra(
                            nv.get("horas_normales_q1"), nv.get("horas_normales_q2"),
                            nv.get("asistencia_perfecta_q1"), nv.get("asistencia_perfecta_q2"),
                        ))
                        feriados = calcular_feriados_detallados(escala, tuple(
                            FeriadoDetalladoUocra(
                                date.fromisoformat(item["fecha"]), bool(item["trabajado"]),
                                bool(item["cumple_requisito_art168"]),
                                Decimal(str(item["horas_jornada_anterior"])),
                                Dinero(Decimal(str(item.get("remuneraciones_accesorias", 0)))),
                            ) for item in nv.get("feriados_uocra_detalle", ())
                        ))
                        total_feriados = sum((f.adicional_a_pagar.monto for f in feriados), Decimal("0"))
                        extras = calcular_horas_extra_detalladas(escala, tuple(
                            HoraExtraDetalladaUocra(
                                date.fromisoformat(item["fecha"]),
                                Decimal(str(item["hora_inicio"])),
                                Decimal(str(item["horas"])), bool(item.get("es_feriado", False)),
                            ) for item in nv.get("horas_extra_uocra_detalle", ())
                        ), Decimal(str(nv.get("horas_extra_uocra_acumuladas_anio", 0))))
                        adicionales_tarea = calcular_adicionales_tarea_uocra(
                            escala,
                            Decimal(str(nv.get("horas_hormigon_manual_uocra", 0))),
                            Decimal(str(nv.get("horas_altura_uocra", 0))),
                            (Decimal(str(nv["altura_metros_uocra"]))
                             if nv.get("altura_metros_uocra") is not None else None),
                        )
                        total_adicionales = sum((a.importe.monto for a in adicionales_tarea), Decimal("0"))
                        decision = None
                        if nv.get("fcl_criterio_aniversario"):
                            decision = DecisionProfesionalFcl(
                                nv["fcl_criterio_aniversario"], nv.get("fcl_aprobado_por") or "",
                                nv.get("fcl_fundamento") or "",
                            )
                        alicuota = resolver_alicuota_fcl(emp.fecha_ingreso, periodo, decision)
                        fondo = calcular_fondo_cese(ComponentesFondoCese(
                            basico=base.basico_total, asistencia=base.asistencia_total,
                            adicionales_remunerativos=Dinero(total_feriados + total_adicionales),
                            horas_extra_valor_normal=extras.valor_normal,
                            recargos_legales_horas_extra=extras.recargo_legal,
                        ), alicuota)
                        base_rem = Dinero(
                            base.remunerativo_total.monto + total_feriados
                            + extras.total.monto + total_adicionales
                        )
                        base_anterior = nv.get("base_contribucion_uocra_mes_anterior")
                        tasas = TasasAportesUocra(
                            parametros.fraccion("APORTE_JUBILACION"),
                            parametros.fraccion("APORTE_LEY19032"),
                            parametros.fraccion("APORTE_OBRA_SOCIAL"),
                            parametros.fraccion("CONTRIB_JUBILACION"),
                            parametros.fraccion("CONTRIB_OBRA_SOCIAL"),
                            parametros.fraccion("APORTE_SOLIDARIO_UOCRA_76/75"),
                            parametros.fraccion("CONTRIB_EMP_UOCRA_76/75"),
                        )
                        aportes = calcular_aportes_y_contribuciones(
                            base_rem, base_rem,
                            Dinero(Decimal(base_anterior)) if base_anterior is not None else None,
                            tasas, emp.afiliado_sindicato, cuota_sindical_verificada,
                        )
                        res = armar_recibo_uocra(
                            emp.cuil, periodo, base, fondo, aportes, feriados, extras,
                            adicionales_tarea,
                        )
                    except (AttributeError, KeyError, TypeError, ValueError) as exc:
                        bloqueos.append({
                            "empleado_id": str(emp.id), "cct_numero": emp.cct_numero,
                            "categoria": emp.categoria, "provisorio": False,
                            "requiere_confirmacion": False,
                            "motivo": f"Liquidación UOCRA bloqueada: {exc}",
                        })
                        continue
                elif es_motor_uom:
                    try:
                        detalle_uom = nv.get("uom_detalle") or {}
                        base = calcular_base_uom(
                            escala,
                            (Decimal(str(detalle_uom["horas_normales"]))
                             if detalle_uom.get("horas_normales") is not None else None),
                            dom_emp.proporcion_jornada,
                        )
                        if detalle_uom.get("ingresos_computables_imgr") is None:
                            raise ValueError("informá los ingresos computables para IMGR, sin horas extra")
                        imgr = calcular_complemento_imgr(
                            params_emp.valor_ars(next(
                                p.codigo for p in params_emp.variables_convenio("260/75")
                                if (p.incidencias or {}).get("tipo") == "garantia_ingreso"
                                and (p.incidencias or {}).get("grupo") in escala.fuente
                            )),
                            Dinero(Decimal(str(detalle_uom["ingresos_computables_imgr"]))),
                            dom_emp.proporcion_jornada,
                        )
                        gratificacion = calcular_gratificacion_uom(
                            params_emp.valor_ars("GRATIFICACION_NR_UOM_2026_08"),
                            dom_emp.proporcion_jornada,
                        )
                        compensacion = calcular_compensacion_abril_julio_uom(
                            params_emp.valor_ars("COMPENSACION_ABR_JUL_UOM_CUOTA1"),
                            int(detalle_uom.get("dias_trabajados_abril_julio") or 0),
                            dom_emp.proporcion_jornada,
                            bool(detalle_uom.get("contrato_vigente_31_07")),
                            Dinero(Decimal(str(detalle_uom.get("pagos_a_cuenta_absorbibles") or 0))),
                        )
                        grupo_uom = next(
                            ((p.incidencias or {}).get("grupo")
                             for p in params_emp.variables_convenio("260/75")
                             if (p.incidencias or {}).get("tipo") == "garantia_ingreso"
                             and (p.incidencias or {}).get("grupo") in escala.fuente),
                            None,
                        )
                        if not grupo_uom:
                            raise ValueError("no se pudo identificar la rama UOM de la categoría")
                        catalogo_adicionales = {
                            p.codigo: p for p in params_emp.variables_convenio("260/75")
                            if (p.incidencias or {}).get("tipo") == "adicional_variable"
                            and (p.incidencias or {}).get("grupo") == grupo_uom
                        }
                        adicionales = []
                        for codigo, cantidad in (detalle_uom.get("adicionales") or {}).items():
                            parametro = catalogo_adicionales.get(codigo)
                            if parametro is None:
                                raise ValueError(
                                    f"el adicional {codigo} no corresponde a la rama UOM seleccionada"
                                )
                            incidencias = parametro.incidencias or {}
                            adicionales.append((
                                codigo,
                                incidencias.get("descripcion") or codigo.replace("_", " ").title(),
                                calcular_adicional_uom(
                                    params_emp.valor_ars(codigo),
                                    incidencias.get("modalidad") or "",
                                    Decimal(str(cantidad)),
                                ),
                            ))
                        res = armar_recibo_uom(
                            emp.cuil, periodo, base, gratificacion, compensacion, imgr,
                            parametros.fraccion("APORTE_JUBILACION"),
                            parametros.fraccion("APORTE_LEY19032"),
                            parametros.fraccion("APORTE_OBRA_SOCIAL"),
                            parametros.fraccion("CONTRIB_JUBILACION"),
                            parametros.fraccion("CONTRIB_OBRA_SOCIAL"),
                            params_emp.valor_ars("SEGURO_VIDA_SEPELIO_UOM_TRAB"),
                            params_emp.valor_ars("SEGURO_VIDA_SEPELIO_UOM_EMP"),
                            adicionales,
                        )
                    except (KeyError, StopIteration, TypeError, ValueError) as exc:
                        bloqueos.append({
                            "empleado_id": str(emp.id), "cct_numero": emp.cct_numero,
                            "categoria": emp.categoria, "provisorio": False,
                            "requiere_confirmacion": False,
                            "motivo": f"Liquidación UOM bloqueada: {exc}",
                        })
                        continue
                else:
                    try:
                        motor = MotorLiquidacion(params_emp, amparos)
                        res = motor.liquidar_mensual(
                            dom_emp, periodo, escala, cct_cfg,
                            Novedades(
                                horas_extra_50=Decimal(str(nv.get("horas_extra_50", "0"))),
                                horas_extra_100=Decimal(str(nv.get("horas_extra_100", "0"))),
                                feriados_trabajados=int(nv.get("feriados_trabajados", 0)),
                                feriados_no_trabajados=int(nv.get("feriados_no_trabajados", 0)),
                                premio=Decimal(str(nv.get("premio", "0"))),
                                tipo_premio=nv.get("tipo_premio", "pendiente"),
                                descuento_adicional=Decimal(str(nv.get("descuento_adicional", "0"))),
                                detalle_descuento=nv.get("detalle_descuento", ""),
                                adicionales_convencionales=nv.get("adicionales_convencionales", ()),
                                cantidades_adicionales=nv.get("cantidades_adicionales", ()),
                            ),
                            a_fecha=fecha_ref,
                        )
                    except (AttributeError, KeyError, TypeError, ValueError) as exc:
                        bloqueos.append({
                            "empleado_id": str(emp.id), "cct_numero": emp.cct_numero,
                            "categoria": emp.categoria,
                            "provisorio": bool(escala_provisoria),
                            "requiere_confirmacion": False,
                            "motivo": f"Liquidación bloqueada: {exc}",
                        })
                        continue
                conceptos = [
                    {
                        "codigo": c.codigo, "descripcion": c.descripcion, "tipo": c.tipo.value,
                        "importe": str(c.importe.redondear().monto), "regimen": c.regimen.value,
                        "cantidad": str(c.cantidad),
                        "base_calculo": str(
                            (c.base_calculo or c.importe).redondear().monto
                        ),
                        "unidad": c.unidad,
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
                    # Fotografía documental del trabajador. No interviene en el
                    # cálculo: permite reimprimir el recibo años después sin
                    # consultar la ficha actual, que pudo cambiar.
                    "documental": {
                        "nombre": emp.nombre,
                        "apellido": emp.apellido,
                        "cuil": emp.cuil.valor,
                        "legajo": emp.legajo,
                        "fecha_ingreso": emp.fecha_ingreso.isoformat(),
                        "categoria": emp.categoria,
                        "cct_numero": emp.cct_numero,
                        "modalidad_contrato": getattr(emp, "modalidad_contrato", "") or "",
                        "lugar_trabajo": getattr(emp, "lugar_trabajo", "") or "",
                    },
                    "cct": emp.cct_numero, "categoria": emp.categoria,
                    "basico": str(escala.basico.monto), "zona_escala": escala.zona,
                    "amparos": [a[0] + ":" + (a[2] or "") for a in res.regimenes_aplicados()],
                    "novedades": {
                        "horas_extra_50": str(nv.get("horas_extra_50", "0")),
                        "horas_extra_100": str(nv.get("horas_extra_100", "0")),
                        "feriados_trabajados": int(nv.get("feriados_trabajados", 0)),
                        "feriados_no_trabajados": int(nv.get("feriados_no_trabajados", 0)),
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
                    "escala_provisoria": escala_provisoria,
                    "vista_previa": vista_previa_contador,
                    "pendiente_aprobacion_contador": vista_previa_contador,
                })

            # Una ejecución de "liquidar todos" es atómica: si un empleado no
            # puede calcularse, no se conserva una liquidación parcial ni se
            # crea una versión vacía/engañosa de la carpeta mensual.
            if bloqueos or not detalles_out:
                liquidacion_id = str(liq.id)
                estado = liq.estado
                await liq_repo.descartar(liq)
                return {
                    "id": liquidacion_id,
                    "periodo": periodo_str,
                    "tipo": tipo,
                    "estado": estado,
                    "detalles": [],
                    "bloqueos": bloqueos,
                    "carpeta_mensual": None,
                }

            # Reasignar un objeto nuevo fuerza la detección de cambios de JSONB
            # (sin MutableDict, las mutaciones in-place no se marcan dirty).
            liq.snapshot_parametros = dict(snapshot)
            reglas_pendientes = []
            for p in parametros.pendientes_usados():
                reglas_pendientes.append({
                    "codigo": p.codigo,
                    "cct_numero": p.cct_numero,
                    "verificado": p.is_verified,
                    "fuente": p.fuente,
                })
            if any(d.get("pendiente_aprobacion_contador") for d in detalles_out):
                reglas_pendientes.append({
                    "codigo": "APROBACION_CONTADOR_UOM",
                    "cct_numero": "260/75",
                    "verificado": False,
                    "fuente": "Pendiente de revisión y aprobación por contador público",
                })
            contenido_carpeta = construir_contenido_carpeta(
                periodo=periodo_str, tipo=tipo, liquidacion_id=str(liq.id),
                detalles=detalles_out, snapshot=dict(snapshot),
                reglas_pendientes=reglas_pendientes,
            )
            carpeta_repo = CarpetaMensualRepo(s)
            ultima = await carpeta_repo.ultima(uuid.UUID(tenant_id), periodo_str)
            if ultima is not None:
                actual_comparable = dict(contenido_carpeta)
                anterior_comparable = dict(ultima.contenido or {})
                actual_comparable.pop("liquidacion_id", None)
                anterior_comparable.pop("liquidacion_id", None)
                if huella_carpeta(actual_comparable) == huella_carpeta(anterior_comparable):
                    obligaciones_anteriores = await carpeta_repo.listar_obligaciones(
                        uuid.UUID(tenant_id), ultima.id
                    )
                    liquidacion_id = str(liq.id)
                    estado = liq.estado
                    await liq_repo.descartar(liq)
                    return {
                        "id": liquidacion_id, "periodo": periodo_str, "tipo": tipo,
                        "estado": estado, "detalles": detalles_out, "bloqueos": [],
                        "carpeta_mensual": {
                            "id": str(ultima.id), "version": ultima.version,
                            "estado": ultima.estado, "hash_sha256": ultima.hash_sha256,
                            "apto_produccion": (ultima.contenido or {}).get(
                                "control_normativo", {}
                            ).get("apto_produccion", False),
                            "obligaciones_generadas": len(obligaciones_anteriores),
                            "sin_cambios": True,
                        },
                    }

            carpeta = await carpeta_repo.crear_calculada(
                uuid.UUID(tenant_id), periodo_str, liq.id,
                contenido_carpeta, huella_carpeta(contenido_carpeta),
            )
            obligaciones = await carpeta_repo.crear_obligaciones(
                uuid.UUID(tenant_id), carpeta.id,
                obligaciones_desde_contenido(contenido_carpeta),
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
                "bloqueos": bloqueos,
                "carpeta_mensual": {
                    "id": str(carpeta.id), "version": carpeta.version,
                    "estado": carpeta.estado, "hash_sha256": carpeta.hash_sha256,
                    "apto_produccion": contenido_carpeta["control_normativo"]["apto_produccion"],
                    "obligaciones_generadas": len(obligaciones),
                },
            }
