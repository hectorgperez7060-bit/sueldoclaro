"""Caso de uso: liquidar un período (usa el motor puro de la Fase 1).

Persiste la liquidación con un snapshot inmutable de los parámetros usados
(reproducibilidad histórica: sección 6.5 del prompt).
"""
from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Dict

from domain.entities.empleado import Empleado
from domain.entities.jornada import (
    describir_jornada, excede_limite_parcial, horas_desde_reglas,
)
from domain.entities.carpeta_mensual import (
    construir_contenido_carpeta, huella_carpeta, obligaciones_desde_contenido,
)
from domain.entities.escala_verificada import evaluar_escala
from domain.entities.parametros import ParametroLegal as ParamDom
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.payroll_engine.camioneros import (
    ValoresVariablesCamioneros, armar_recibo_camioneros_general,
    calcular_variables_camioneros, novedades_camioneros_desde_dict,
    tramo_transporte_pesado,
)
from domain.payroll_engine.uom import (
    armar_recibo_uom, calcular_adicional_uom, calcular_base_uom, calcular_compensacion_abril_julio_uom,
    calcular_complemento_imgr, calcular_gratificacion_uom,
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
from infrastructure.lsd.bases_snapshot import calcular_bases_snapshot


# Una escala sin fecha de cierre se sigue aplicando sola. A partir de este
# atraso el motor lo dice en el recibo en vez de callarselo.
_MESES_PARA_SOSPECHAR_ESCALA_VIEJA = 1
_CODIGO_ESCALA_SIN_CIERRE = "ESCALA_SIN_CIERRE_DE_VIGENCIA"

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
            # Horas de jornada completa por convenio: sirven para controlar el
            # límite del art. 92 ter y para dejar la jornada escrita en el recibo.
            horas_jornada = await params_repo.horas_jornada_por_cct()
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
                # Regla GENERAL (cualquier CCT/categoría/período): solo se usa
                # una escala vigente verificada o una fila provisoria vigente
                # confirmada expresamente. Nunca se estima ni se pone en cero.
                escala_provisoria = None
                evaluacion = evaluar_escala(
                    escala, confirmado=confirmar_provisorios
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
                # Las horas del convenio ya estan a mano: se las pasamos al
                # motor para que escriba la jornada en el recibo con palabras.
                cct_cfg = replace(
                    cct_cfg,
                    horas_jornada_completa=horas_jornada.get(emp.cct_numero),
                )
                if evaluacion.provisorio:
                    escala_provisoria = {
                        "nota": evaluacion.nota,
                        "escala_desde": escala.valid_from.isoformat(),
                    }

                # Una escala sin fecha de fin se arrastra sola: el motor la da
                # por vigente para siempre. Si el convenio acordo aumentos
                # despues, se liquida de menos y nadie se entera, porque no hay
                # nada que bloquear. Es el unico agujero de la regla general de
                # "antes frenar que estimar": no se puede frenar, pero si se
                # puede avisar.
                escala_desactualizada = None
                if escala.valid_to is None:
                    meses = ((periodo.anio - escala.valid_from.year) * 12
                             + periodo.mes - escala.valid_from.month)
                    if meses >= _MESES_PARA_SOSPECHAR_ESCALA_VIEJA:
                        escala_desactualizada = {
                            "escala_desde": escala.valid_from.isoformat(),
                            "meses_de_atraso": meses,
                            "nota": (
                                f"La escala en uso rige desde "
                                f"{escala.valid_from.isoformat()} y no tiene fecha "
                                f"de cierre, asi que se sigue aplicando "
                                f"{meses} mes(es) despues. Si el convenio acordo "
                                f"aumentos en el medio, este recibo esta pagando "
                                f"de menos. Verificalo contra la escala oficial "
                                f"antes de pagar."
                            ),
                        }

                # LCT art. 92 ter: por encima de los 2/3 de la jornada habitual el
                # contrato deja de ser a tiempo parcial y corresponde la
                # remuneración de jornada completa. El motor no lo resuelve solo:
                # prorratear seria pagar de menos y pagar completo sin que nadie
                # lo decida seria cambiarle el contrato al empleador.
                if excede_limite_parcial(emp.proporcion_jornada):
                    horas_cct = horas_jornada.get(emp.cct_numero)
                    detalle = describir_jornada(emp.proporcion_jornada, horas_cct)
                    bloqueos.append({
                        "empleado_id": str(emp.id),
                        "cct_numero": emp.cct_numero,
                        "categoria": emp.categoria,
                        "provisorio": False,
                        "requiere_confirmacion": False,
                        "motivo": (
                            f"Jornada {detalle}: supera las dos terceras partes de la "
                            "jornada del convenio. El art. 92 ter de la LCT obliga a "
                            "abonar la remuneración de jornada completa, así que no "
                            "corresponde prorratear el básico. Corregí las horas "
                            "semanales en el legajo o cargalo como jornada completa."
                        ),
                    })
                    continue

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
                es_motor_camioneros = emp.cct_numero == "40/89"
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
                elif es_motor_camioneros:
                    try:
                        detalle_cam = nv.get("camioneros_detalle") or {}
                        rama = str(detalle_cam.get("rama") or "general")
                        ramas_porcentuales = {
                            "materia_prima_lactea": (
                                "CAM_RAMA_MATERIA_PRIMA_LACTEA_PCT",
                                "Adicional transporte de materia prima láctea",
                                "conductor",
                            ),
                            "auxilio": (
                                "CAM_RAMA_AUXILIO_PCT", "Adicional camión de auxilio", "conductor",
                            ),
                            "diarios_revistas": (
                                "CAM_RAMA_DIARIOS_REVISTAS_PCT",
                                "Adicional distribución de diarios y revistas", "primera",
                            ),
                            "combustibles": (
                                "CAM_RAMA_COMBUSTIBLES_PCT", "Adicional transporte de combustibles", "primera",
                            ),
                            "sustancias_peligrosas": (
                                "CAM_RAMA_SUSTANCIAS_PELIGROSAS_PCT",
                                "Adicional transporte de sustancias peligrosas", "primera",
                            ),
                        }
                        if rama not in {
                            "general", "larga_distancia", "residuos", "taller", "caudales",
                            "clearing", "expreso_mudanza", "aguas_gaseosas",
                            "logistica", "pozos_petroliferos", "transporte_automoviles",
                            "asfalto_caliente", "transporte_pesado", "zafra",
                            *ramas_porcentuales,
                        }:
                            raise ValueError(
                                f"la rama {rama.replace('_', ' ')} conserva adicionales específicos pendientes de integrar"
                            )
                        detalle_cam = dict(detalle_cam)
                        proporcion_bitren = Decimal(str(detalle_cam.get("unidades_bitrenes") or 0))
                        if proporcion_bitren:
                            categoria_bitren = emp.categoria.translate(
                                str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun")
                            ).casefold()
                            if "conductor" not in categoria_bitren or "primera" not in categoria_bitren:
                                raise ValueError(
                                    "el adicional bitrenes corresponde únicamente a Conductor de Primera Categoría"
                                )
                            if proporcion_bitren < 0 or proporcion_bitren > Decimal("1"):
                                raise ValueError(
                                    "la proporción mensual de conducción de bitrén debe estar entre 0 y 1"
                                )
                        adicional_zafra_pct = Decimal("0")
                        if rama == "zafra":
                            categoria_zafra = emp.categoria.translate(
                                str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun")
                            ).casefold()
                            if "conductor" not in categoria_zafra or "primera" not in categoria_zafra:
                                raise ValueError(
                                    "la integración de zafra requiere Conductor de Primera Categoría"
                                )
                            radio_zafra = str(detalle_cam.get("radio_zafra") or "")
                            codigo_garantia = {
                                "hasta_45": "CAM_ZAFRA_GARANTIA_HASTA_45_KM",
                                "mas_45": "CAM_ZAFRA_GARANTIA_MAS_45_KM",
                            }.get(radio_zafra)
                            if not codigo_garantia:
                                raise ValueError("debe indicar el radio de operación de zafra")
                            garantia_km = params_emp.cantidad(codigo_garantia, "km")
                            detalle_cam["kilometros_extra"] = max(
                                Decimal(str(detalle_cam.get("kilometros_extra") or 0)),
                                garantia_km,
                            )
                            detalle_cam["kilometros_viatico"] = max(
                                Decimal(str(detalle_cam.get("kilometros_viatico") or 0)),
                                garantia_km,
                            )
                            adicional_zafra_pct = params_emp.fraccion(
                                "CAM_ZAFRA_ADICIONAL_TOTAL_PCT"
                            )
                        novedad_cam = novedades_camioneros_desde_dict(detalle_cam)
                        campos_larga_distancia = (
                            "kilometros_extra", "kilometros_viatico", "dias_en_viaje",
                            "viajes_cordilleranos", "permanencias", "simples_presencias",
                            "permanencias_sur", "simples_presencias_sur", "cruces_frontera",
                            "ingresos_egresos_tdf", "traslados_unidad_descarga",
                        )
                        if rama == "general" and any(
                            Decimal(str(detalle_cam.get(campo) or 0)) > 0
                            for campo in campos_larga_distancia
                        ):
                            raise ValueError("los kilómetros, permanencias y traslados requieren rama larga distancia")
                        viajes_autos = Decimal(str(detalle_cam.get("viajes_transporte_automoviles") or 0))
                        if rama != "transporte_automoviles" and viajes_autos:
                            raise ValueError("los viajes de automóviles requieren la rama transporte de automóviles")
                        dias_asfalto = Decimal(str(detalle_cam.get("dias_asfalto_caliente") or 0))
                        if rama != "asfalto_caliente" and dias_asfalto:
                            raise ValueError("los días de asfalto requieren la rama asfalto caliente")
                        if rama in {"larga_distancia", "zafra"} and any(
                            Decimal(str(detalle_cam.get(campo) or 0)) > 0
                            for campo in ("dias_comida", "dias_viatico_especial", "pernoctadas")
                        ):
                            raise ValueError(
                                "larga distancia no usa comida, viático especial ni pernoctada de los ítems 4.1"
                            )
                        adicionales_rama = []
                        recargo_comida_pct = Decimal("0")
                        recargo_viatico_pct = Decimal("0")
                        recargo_codigo = "RESIDUOS_5_3_11"
                        recargo_descripcion = "recolección de residuos"
                        if rama in ramas_porcentuales:
                            codigo_pct, descripcion_pct, requisito = ramas_porcentuales[rama]
                            categoria_normalizada = emp.categoria.translate(
                                str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun")
                            ).casefold()
                            if "conductor" not in categoria_normalizada:
                                raise ValueError("esta rama requiere una categoría de conductor")
                            if requisito == "primera" and "primera" not in categoria_normalizada:
                                raise ValueError("esta rama se calcula sobre conductor de primera categoría")
                            adicionales_rama.append((
                                codigo_pct, descripcion_pct, params_emp.fraccion(codigo_pct)
                            ))
                        if rama == "transporte_pesado":
                            categoria_normalizada = emp.categoria.translate(
                                str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun")
                            ).casefold()
                            modalidad_pesado = str(
                                detalle_cam.get("modalidad_transporte_pesado") or "conductor"
                            )
                            if modalidad_pesado == "conductor":
                                if "conductor" not in categoria_normalizada or "primera" not in categoria_normalizada:
                                    raise ValueError(
                                        "transporte pesado como conductor requiere conductor de primera categoría"
                                    )
                                toneladas = Decimal(str(
                                    detalle_cam.get("toneladas_transporte_pesado") or 0
                                ))
                                codigo_pesado = tramo_transporte_pesado(toneladas)
                                descripcion_pesado = (
                                    f"Adicional transporte pesado ({toneladas} toneladas)"
                                )
                            elif modalidad_pesado in {"auxiliar_mecanico", "auxiliar_hidraulico"}:
                                if "operario" not in categoria_normalizada or "especializado" not in categoria_normalizada:
                                    raise ValueError(
                                        "el auxiliar de carretón requiere la categoría Operarios Especializados"
                                    )
                                codigo_pesado = (
                                    "CAM_PESADO_AUX_MECANICO_PCT"
                                    if modalidad_pesado == "auxiliar_mecanico"
                                    else "CAM_PESADO_AUX_HIDRAULICO_PCT"
                                )
                                descripcion_pesado = (
                                    "Auxiliar especializado de carretón mecánico"
                                    if modalidad_pesado == "auxiliar_mecanico"
                                    else "Auxiliar especializado de carretón hidráulico"
                                )
                            else:
                                raise ValueError("la modalidad de transporte pesado no es válida")
                            adicionales_rama.append((
                                codigo_pesado,
                                descripcion_pesado,
                                params_emp.fraccion(codigo_pesado),
                            ))
                        categoria = emp.categoria.translate(
                            str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun")
                        ).casefold()
                        es_oficial = (
                            "oficial" in categoria and "medio oficial" not in categoria
                            and "gomero" not in categoria
                        )
                        es_medio = "medio oficial" in categoria and "gomero" not in categoria
                        es_lavador = any(x in categoria for x in ("lavador", "engrasador", "ayudante de taller"))
                        grupo_taller = str(detalle_cam.get("grupo_taller") or "")
                        if rama == "taller":
                            if not (es_oficial or es_medio):
                                raise ValueError("la rama taller requiere categoría oficial o medio oficial")
                            if grupo_taller not in {"I", "III"}:
                                raise ValueError("el adicional de taller corresponde únicamente a grupos I y III")
                            codigo = "CAM_TALLER_OFICIAL_PCT" if es_oficial else "CAM_TALLER_MEDIO_PCT"
                            descripcion = "Adicional oficial de taller" if es_oficial else "Adicional medio oficial de taller"
                            adicionales_rama.append((codigo, descripcion, params_emp.fraccion(codigo)))
                        if rama == "residuos":
                            if any(x in categoria for x in ("conductor", "recolector", "peon")):
                                codigo = "CAM_RESIDUOS_OPERATIVO_PCT"
                                adicionales_rama.append((
                                    codigo, "Adicional personal operativo de residuos",
                                    params_emp.fraccion(codigo),
                                ))
                                recargo_comida_pct = params_emp.fraccion("CAM_RESIDUOS_COMIDA_PCT")
                            elif es_oficial or es_medio or es_lavador:
                                codigo_mult = "CAM_MULTIPLICIDAD_OFICIAL_PCT" if es_oficial else "CAM_MULTIPLICIDAD_OTROS_PCT"
                                adicionales_rama.append((
                                    codigo_mult, "Adicional multiplicidad taller de residuos",
                                    params_emp.fraccion(codigo_mult),
                                ))
                                if (es_oficial or es_medio) and grupo_taller in {"I", "III"}:
                                    codigo_t = "CAM_TALLER_OFICIAL_PCT" if es_oficial else "CAM_TALLER_MEDIO_PCT"
                                    adicionales_rama.append((
                                        codigo_t, "Adicional por grupo de taller",
                                        params_emp.fraccion(codigo_t),
                                    ))
                            else:
                                raise ValueError("la categoría no está alcanzada por las reglas modeladas de residuos")
                        if rama == "caudales":
                            if "custodia de camion de caudales" in categoria:
                                codigo = "CAM_CAUDALES_CUSTODIO_PCT"
                                adicionales_rama.append((
                                    codigo, "Adicional custodio de unidad blindada",
                                    params_emp.fraccion(codigo),
                                ))
                            elif es_oficial or es_medio or es_lavador:
                                codigo_mult = "CAM_MULTIPLICIDAD_OFICIAL_PCT" if es_oficial else "CAM_MULTIPLICIDAD_OTROS_PCT"
                                adicionales_rama.append((
                                    codigo_mult, "Adicional multiplicidad taller de caudales",
                                    params_emp.fraccion(codigo_mult),
                                ))
                                if (es_oficial or es_medio) and grupo_taller in {"I", "III"}:
                                    codigo_t = "CAM_TALLER_OFICIAL_PCT" if es_oficial else "CAM_TALLER_MEDIO_PCT"
                                    adicionales_rama.append((
                                        codigo_t, "Adicional por grupo de taller",
                                        params_emp.fraccion(codigo_t),
                                    ))
                            elif not any(x in categoria for x in ("chofer de camion blindado", "chofer con firma")):
                                raise ValueError("la categoría no está alcanzada por las reglas modeladas de caudales")
                        if rama == "clearing":
                            categorias_clearing = (
                                "conductor", "distribuidor domiciliario", "operador de servicios",
                                "auxiliar operativo", "administrativo",
                            )
                            if not any(x in categoria for x in categorias_clearing):
                                raise ValueError("la categoría no está comprendida en clearing y carga postal")
                            codigo = "CAM_CLEARING_PCT"
                            porcentaje = params_emp.fraccion(codigo)
                            adicionales_rama.append((codigo, "Adicional clearing y carga postal", porcentaje))
                            recargo_comida_pct = porcentaje
                            recargo_viatico_pct = porcentaje
                            recargo_codigo = "CLEARING_5_2_2"
                            recargo_descripcion = "clearing y carga postal"
                        if rama == "expreso_mudanza":
                            categorias_expreso = (
                                "conductor", "operario", "peon", "embalador", "recibidor",
                                "clasificador", "encargado", "autoelevador", "administrativo",
                            )
                            if not any(x in categoria for x in categorias_expreso):
                                raise ValueError("la categoría no está comprendida en expreso, mudanzas y encomiendas")
                            codigo = "CAM_EXPRESO_FRIO_PCT" if detalle_cam.get("camara_frio") else "CAM_EXPRESO_PCT"
                            porcentaje = params_emp.fraccion(codigo)
                            descripcion = "Adicional expreso/mudanzas en cámara de frío" if detalle_cam.get("camara_frio") else "Adicional expreso, mudanzas y encomiendas"
                            adicionales_rama.append((codigo, descripcion, porcentaje))
                            recargo_comida_pct = porcentaje
                            recargo_viatico_pct = porcentaje
                            recargo_codigo = "EXPRESO_5_10"
                            recargo_descripcion = "expreso, mudanzas y encomiendas"
                        if rama == "aguas_gaseosas":
                            categoria_20 = any(x in categoria for x in (
                                "conductor", "chofer", "taller", "oficial", "lavador",
                                "engrasador", "administrativo",
                            ))
                            categoria_16 = any(x in categoria for x in (
                                "operario especializado", "maestranza", "sereno",
                            ))
                            if not (categoria_20 or categoria_16):
                                raise ValueError("la categoría no está comprendida en aguas gaseosas")
                            codigo = "CAM_AGUAS_GASEOSAS_20_PCT" if categoria_20 else "CAM_AGUAS_GASEOSAS_16_PCT"
                            adicionales_rama.append((
                                codigo, "Adicional transporte y distribución de aguas gaseosas",
                                params_emp.fraccion(codigo),
                            ))
                        if rama == "logistica":
                            categorias_logistica = (
                                "conductor", "chofer", "operario", "peon", "controlador",
                                "recibidor", "clasificador", "encargado", "autoelevador",
                                "administrativo",
                            )
                            if not any(x in categoria for x in categorias_logistica):
                                raise ValueError("la categoría no está comprendida en operaciones logísticas")
                            codigo = "CAM_LOGISTICA_FRIO_PCT" if detalle_cam.get("camara_frio") else "CAM_LOGISTICA_PCT"
                            porcentaje = params_emp.fraccion(codigo)
                            descripcion = "Adicional logística en cámara de frío" if detalle_cam.get("camara_frio") else "Adicional operaciones logísticas"
                            adicionales_rama.append((codigo, descripcion, porcentaje))
                            recargo_comida_pct = porcentaje
                            recargo_viatico_pct = porcentaje
                            recargo_codigo = "LOGISTICA_5_12"
                            recargo_descripcion = "operaciones logísticas"
                        if rama == "pozos_petroliferos":
                            if "conductor" not in categoria and "chofer" not in categoria:
                                raise ValueError("la rama pozos petrolíferos requiere una categoría de conductor")
                            adicionales_rama.append((
                                "CAM_POZOS_ESPECIALIDAD_PCT", "Adicional pozos petrolíferos",
                                params_emp.fraccion("CAM_POZOS_ESPECIALIDAD_PCT"),
                            ))
                            if detalle_cam.get("cuenca_petrolifera"):
                                adicionales_rama.append((
                                    "CAM_POZOS_CUENCA_PCT", "Adicional por cuenca petrolífera",
                                    params_emp.fraccion("CAM_POZOS_CUENCA_PCT"),
                                ))
                            if detalle_cam.get("la_pampa_mendoza"):
                                if novedad_cam.zona != "COEF_1_20":
                                    raise ValueError("La Pampa/Mendoza requiere informar zona COEF_1_20")
                                adicionales_rama.append((
                                    "CAM_POZOS_LP_MZA_PCT", "Adicional La Pampa/Mendoza",
                                    params_emp.fraccion("CAM_POZOS_LP_MZA_PCT"),
                                ))
                            recargo_comida_pct = params_emp.fraccion("CAM_POZOS_VIATICOS_PCT")
                            recargo_viatico_pct = recargo_comida_pct
                            recargo_codigo = "POZOS_5_7_4"
                            recargo_descripcion = "pozos petrolíferos"
                        if rama == "transporte_automoviles":
                            if "conductor" not in categoria and "chofer" not in categoria:
                                raise ValueError("el transporte de automóviles requiere categoría de conductor")
                        if rama == "asfalto_caliente":
                            if "conductor" not in categoria or "primera" not in categoria:
                                raise ValueError("asfalto caliente requiere conductor de primera categoría")
                            codigo = "CAM_RAMA_COMBUSTIBLES_PCT"
                            adicionales_rama.append((
                                codigo, "Adicional transporte de combustibles",
                                params_emp.fraccion(codigo),
                            ))
                        if novedad_cam.zona != escala.zona:
                            raise ValueError(
                                "la zona de la novedad no coincide con la zona del establecimiento"
                            )
                        valores_cam = ValoresVariablesCamioneros(
                            params_emp.valor_ars("CAM_COMIDA_4_1_12"),
                            params_emp.valor_ars("CAM_VIATICO_ESP_4_1_13"),
                            params_emp.valor_ars("CAM_PERNOCTADA_4_1_14"),
                            params_emp.valor_ars("CAM_HORA_EXTRA_KM_4_2_3").monto,
                            params_emp.valor_ars("CAM_VIATICO_KM_4_2_4").monto,
                            params_emp.valor_ars("CAM_PERMANENCIA_4_2_5"),
                            params_emp.valor_ars("CAM_SIMPLE_PRESENCIA_4_2_5"),
                            params_emp.valor_ars("CAM_PERMANENCIA_SUR_4_2_5"),
                            params_emp.valor_ars("CAM_SIMPLE_PRESENCIA_SUR_4_2_5"),
                            params_emp.valor_ars("CAM_CRUCE_FRONTERA_4_2_17"),
                            params_emp.valor_ars("CAM_INGRESO_EGRESO_TDF_4_2_17"),
                            params_emp.valor_ars("CAM_PLUS_VACACIONAL_3_3_2"),
                            params_emp.valor_ars("CAM_ADICIONAL_BITRENES"),
                        )
                        variables_cam = calcular_variables_camioneros(valores_cam, novedad_cam)
                        res = armar_recibo_camioneros_general(
                            emp.cuil, periodo, escala.basico,
                            dom_emp.antiguedad_anios(fecha_ref), dom_emp.proporcion_jornada,
                            variables_cam,
                            parametros.fraccion("APORTE_JUBILACION"),
                            parametros.fraccion("APORTE_LEY19032"),
                            parametros.fraccion("APORTE_OBRA_SOCIAL"),
                            parametros.fraccion("CONTRIB_JUBILACION"),
                            parametros.fraccion("CONTRIB_OBRA_SOCIAL"),
                            Decimal(str(detalle_cam.get("traslados_unidad_descarga") or 0)),
                            tuple(adicionales_rama), recargo_comida_pct,
                            recargo_viatico_pct, recargo_codigo, recargo_descripcion,
                            Decimal(str(detalle_cam.get("viajes_transporte_automoviles") or 0)),
                            params_emp.fraccion("CAM_AUTOS_JORNALES_POR_VIAJE")
                            if rama == "transporte_automoviles" else Decimal("1"),
                            Decimal(str(detalle_cam.get("dias_asfalto_caliente") or 0)),
                            params_emp.fraccion("CAM_ASFALTO_JORNALES_POR_DIA")
                            if rama == "asfalto_caliente" else Decimal("1"),
                            adicional_zafra_pct,
                        )
                    except (AttributeError, KeyError, TypeError, ValueError) as exc:
                        bloqueos.append({
                            "empleado_id": str(emp.id), "cct_numero": emp.cct_numero,
                            "categoria": emp.categoria, "provisorio": False,
                            "requiere_confirmacion": False,
                            "motivo": f"Liquidación Camioneros bloqueada: {exc}",
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
                try:
                    bases_lsd, trazabilidad_lsd = calcular_bases_snapshot(
                        conceptos, periodo_str, dict(getattr(emp, "perfil_arca", None) or {}),
                    )
                    bases_lsd_out = [str(base) for base in bases_lsd]
                    error_lsd = None
                except ValueError as exc:
                    bases_lsd_out, trazabilidad_lsd = None, {}
                    error_lsd = str(exc)

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
                        "cuil": emp.cuil,
                        "legajo": emp.legajo,
                        "fecha_ingreso": emp.fecha_ingreso.isoformat(),
                        "categoria": emp.categoria,
                        "cct_numero": emp.cct_numero,
                        "modalidad_contrato": getattr(emp, "modalidad_contrato", "") or "",
                        "jornada": describir_jornada(
                            emp.proporcion_jornada, horas_jornada.get(emp.cct_numero)
                        ),
                        "lugar_trabajo": getattr(emp, "lugar_trabajo", "") or "",
                        "cbu": getattr(emp, "cbu", "") or "",
                        "forma_pago": getattr(emp, "forma_pago", "") or "",
                        "cantidad_hijos": int(getattr(emp, "cantidad_hijos", 0) or 0),
                        "conyuge_a_cargo": bool(getattr(emp, "conyuge_a_cargo", False)),
                    },
                    # Perfil ARCA fotografiado: una exportación histórica no puede
                    # consultar la ficha actual porque los códigos pudieron cambiar.
                    "perfil_arca": dict(getattr(emp, "perfil_arca", None) or {}),
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
                    "escala_desactualizada": escala_desactualizada,
                    "vista_previa": False,
                    "modo_servicio": (
                        "AUTOGESTION_EMPLEADOR_ESCALA_PROVISORIA_CONFIRMADA"
                        if escala_provisoria else "AUTOGESTION_EMPLEADOR"
                    ),
                    "bases_lsd": bases_lsd_out,
                    "trazabilidad_lsd": trazabilidad_lsd,
                    "error_lsd": error_lsd,
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
            for detalle in detalles_out:
                aviso = detalle.get("escala_desactualizada")
                if aviso:
                    reglas_pendientes.append({
                        "codigo": _CODIGO_ESCALA_SIN_CIERRE,
                        "cct_numero": detalle.get("cct_numero"),
                        "verificado": False,
                        "fuente": aviso["nota"],
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
