"""Motor de liquidación puro.

100% dominio: sin BD, sin FastAPI, sin WeasyPrint. Recibe entidades y
parámetros; devuelve un ``ResultadoLiquidacion``. Todo importe es ``Decimal``
vía ``Dinero`` y se redondea (ROUND_HALF_UP, 2 decimales) solo en el importe
final de cada concepto.

Estrategias por amparo (sección 5.4 del prompt): cada concepto afectado por la
reforma declara dos reglas —``regla_ley_27802`` y ``regla_previa``— y el
``AmparoSet`` decide cuál se aplica según el CCT y el período. El concepto
resultante registra qué régimen se usó, para trazabilidad ante inspección.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List

from ..entities.concepto import Concepto, Regimen, TipoConcepto
from ..entities.empleado import Empleado
from ..entities.liquidacion import ResultadoLiquidacion
from ..entities.parametros import AmparoSet, EscalaSalarial, ParametroSet
from ..value_objects.dinero import Dinero
from ..value_objects.periodo import Periodo
from .config import CctConfig


@dataclass(frozen=True)
class Novedades:
    horas_extra_50: Decimal = Decimal("0")
    horas_extra_100: Decimal = Decimal("0")
    premio: Decimal = Decimal("0")
    tipo_premio: str = "pendiente"
    descuento_adicional: Decimal = Decimal("0")
    detalle_descuento: str = ""
    # Para SAC: mejor remuneración mensual devengada del semestre y días trabajados.
    mejor_remuneracion_semestre: Dinero = None  # type: ignore[assignment]
    dias_trabajados_semestre: int = 181
    # Para vacaciones: remuneración habitual del mes.
    remuneracion_habitual: Dinero = None  # type: ignore[assignment]
    # Adicionales habilitados por hechos del mes (título, tarea, idioma, etc.).
    # Las fórmulas viven en CctConfig; aquí sólo ingresan códigos y cantidades.
    adicionales_convencionales: tuple[str, ...] = ()
    cantidades_adicionales: tuple[tuple[str, Decimal], ...] = ()


# Concepto interno afectado por el amparo FAECYS/Comercio (art. 131 Ley 27.802).
_CONCEPTO_MODERNIZACION = "APORTE_MODERNIZACION"


def _desc_nr(codigo: str) -> str:
    """Descripción legible de un concepto no remunerativo de convenio (solo display)."""
    prefijos = {
        "COMERCIO_NR": "Acuerdo no remunerativo",
        "COMERCIO_BONO": "Suma no remun. única (Revisión 2026)",
        "SANIDAD_SUMA_NR": "Suma no remunerativa (acuerdo FATSA)",
        "SANIDAD_DIA": "Día de la Sanidad (pago único)",
    }
    for pref, desc in prefijos.items():
        if codigo.startswith(pref):
            return desc
    return codigo


def _desc_ded(codigo: str) -> str:
    """Descripción legible de una deducción porcentual de convenio (solo display)."""
    prefijos = {
        "APORTE_SOLIDARIO_FATSA": "Aporte solidario FATSA 1%",
        "APORTE_SINDICAL_ART100": "Aporte sindical 2% (art. 100 CCT)",
        "APORTE_FAECYS": "Aporte FAECYS 0,5% (art. 100)",
        "CUOTA_SINDICAL_ART101": "Cuota sindical (art. 101, afiliados)",
        "APORTE_SOLIDARIO": "Aporte solidario (no afiliado)",
        "APORTE_ADEF_REM": "Aporte ADEF sobre remunerativos",
        "APORTE_ADEF_NR": "Aporte ADEF sobre no remunerativos",
        "APORTE_ADEF_ASISTENCIA": "Aporte ADEF asistencia social (junio/diciembre)",
        "CUOTA_SINDICAL_ART47": "Cuota sindical ADEF afiliado (art. 47)",
    }
    for pref, desc in prefijos.items():
        if codigo.startswith(pref):
            return desc
    return codigo


def _desc_contrib_convenio(codigo: str) -> str:
    prefijos = {
        "CONTRIB_EXTRAORDINARIA_FATSA": "Contribución extraordinaria FATSA/OSPSA",
        "CONTRIB_CAPACITACION_FATSA": "Contribución FATSA para formación y capacitación",
    }
    for prefijo, descripcion in prefijos.items():
        if codigo.startswith(prefijo):
            return descripcion
    return codigo


class MotorLiquidacion:
    def __init__(
        self,
        parametros: ParametroSet,
        amparos: AmparoSet,
    ) -> None:
        self._p = parametros
        self._amparos = amparos

    # ------------------------------------------------------------------ #
    # Haberes remunerativos
    # ------------------------------------------------------------------ #
    def _basico(self, empleado: Empleado, escala: EscalaSalarial) -> Dinero:
        """Básico de escala, o el pactado si es mayor."""
        if empleado.remuneracion_pactada and empleado.remuneracion_pactada > escala.basico:
            return empleado.remuneracion_pactada.redondear()
        return escala.basico.redondear()

    def _antiguedad(self, basico: Dinero, anios: int, cct: CctConfig) -> Dinero:
        pct = cct.antiguedad_fraccion(anios)
        return basico.porcentaje(pct).redondear()

    def _presentismo(self, basico: Dinero, antiguedad: Dinero, cct: CctConfig) -> Dinero:
        base = basico + antiguedad
        return base.dividir(cct.presentismo_divisor).redondear()

    def _valor_hora(self, basico: Dinero, antiguedad: Dinero, cct: CctConfig) -> Dinero:
        return (basico + antiguedad).dividir(cct.divisor_horas)  # sin redondear (intermedio)

    # ------------------------------------------------------------------ #
    # Liquidación mensual
    # ------------------------------------------------------------------ #
    def liquidar_mensual(
        self,
        empleado: Empleado,
        periodo: Periodo,
        escala: EscalaSalarial,
        cct: CctConfig,
        novedades: Novedades = Novedades(),
        a_fecha: date = None,  # type: ignore[assignment]
    ) -> ResultadoLiquidacion:
        fecha_calculo = a_fecha or date(periodo.anio, periodo.mes, 28)
        anios = empleado.antiguedad_anios(fecha_calculo)
        conceptos: List[Concepto] = []

        basico = self._basico(empleado, escala)
        # Jornada parcial (LCT art. 92 ter): el básico se prorratea por la
        # proporción de jornada; antigüedad, presentismo, aportes y
        # contribuciones escalan en cascada porque derivan del básico.
        desc_basico = "Sueldo básico"
        if empleado.proporcion_jornada != Decimal("1"):
            basico = basico.porcentaje(empleado.proporcion_jornada).redondear()
            desc_basico = f"Sueldo básico (jornada {empleado.proporcion_jornada})"
        conceptos.append(Concepto(
            "BASICO", desc_basico, TipoConcepto.REMUNERATIVO, basico,
            base_calculo=basico, unidad="mes",
        ))

        # ----- Conceptos NO remunerativos del convenio (data-driven por incidencias) -----
        # El motor NO conoce el convenio: por cada concepto lee 'incidencias'
        # (qué bases integra y qué aportes dispara). Ver ParametroSet.conceptos_convenio.
        nr: List[tuple] = []  # (importe, incidencias)
        for p in self._p.conceptos_convenio(cct.cct_numero):
            imp = Dinero(p.valor)
            if empleado.proporcion_jornada != Decimal("1"):
                imp = imp.porcentaje(empleado.proporcion_jornada)
            imp = imp.redondear()
            nr.append((imp, p.incidencias or {}))
            conceptos.append(Concepto(p.codigo, _desc_nr(p.codigo),
                                      TipoConcepto.NO_REMUNERATIVO, imp,
                                      base_calculo=imp, unidad="suma fija"))

        def _nr(flag: str) -> Dinero:
            total = Dinero.cero()
            for imp, inc in nr:
                if inc.get(flag):
                    total = total + imp
            return total

        # Antigüedad: base = básico + NR que integran antigüedad
        base_antig = (basico + _nr("integra_antiguedad")).redondear()
        antiguedad = base_antig.porcentaje(cct.antiguedad_fraccion(anios)).redondear()
        conceptos.append(
            Concepto("ANTIGUEDAD", f"Antigüedad ({anios} años)", TipoConcepto.REMUNERATIVO,
                     antiguedad, cantidad=Decimal(anios), base_calculo=base_antig,
                     unidad=f"{cct.antiguedad_fraccion(1) * 100}% por año")
        )

        # Adicionales convencionales genéricos. El motor sólo interpreta bases
        # declarativas; no contiene nombres de gremios ni artículos propios.
        solicitados = set(novedades.adicionales_convencionales)
        cantidades = dict(novedades.cantidades_adicionales)
        reglas = {regla.codigo: regla for regla in cct.adicionales}
        desconocidos = solicitados - set(reglas)
        if desconocidos:
            raise ValueError(
                "Adicionales no configurados para el convenio: "
                + ", ".join(sorted(desconocidos))
            )
        grupos: dict[str, list[str]] = {}
        for codigo in solicitados:
            grupo = reglas[codigo].grupo_exclusion
            if grupo:
                grupos.setdefault(grupo, []).append(codigo)
        incompatibles = [codigos for codigos in grupos.values() if len(codigos) > 1]
        if incompatibles:
            raise ValueError(
                "Adicionales incompatibles seleccionados: "
                + "; ".join(", ".join(sorted(codigos)) for codigos in incompatibles)
            )
        for codigo in sorted(solicitados):
            regla = reglas[codigo]
            cantidad = Decimal(cantidades.get(codigo, Decimal("1")))
            if regla.modo_calculo != "remanente_fondo" and cantidad <= 0:
                raise ValueError(f"La cantidad de {codigo} debe ser positiva")
            if regla.requiere_cantidad and codigo not in cantidades:
                raise ValueError(f"El adicional {codigo} requiere una cantidad informada")

            if regla.base == "basico_categoria":
                base_adicional = basico
            elif regla.base == "basico_categoria_mas_antiguedad":
                base_adicional = basico + antiguedad
            elif regla.base.startswith("referencia:"):
                clave = regla.base.split(":", 1)[1]
                base_adicional = Dinero(cct.base_referencia(clave))
                if empleado.proporcion_jornada != Decimal("1"):
                    base_adicional = base_adicional.porcentaje(empleado.proporcion_jornada)
            elif regla.base.startswith("referencia_mas_antiguedad:"):
                clave = regla.base.split(":", 1)[1]
                referencia = Dinero(cct.base_referencia(clave))
                if empleado.proporcion_jornada != Decimal("1"):
                    referencia = referencia.porcentaje(empleado.proporcion_jornada)
                base_adicional = referencia + referencia.porcentaje(
                    cct.antiguedad_fraccion(anios)
                )
            else:
                raise ValueError(f"Base de adicional inválida para {codigo}: {regla.base}")

            multiplicador = cantidad
            importe_directo = None
            if regla.modo_calculo == "proporcion_periodo":
                if not regla.clave_cantidad_base:
                    raise ValueError(f"Falta configurar la base de cantidad para {codigo}")
                cantidad_base = Decimal(cantidades.get(regla.clave_cantidad_base, 0))
                if cantidad_base <= 0:
                    raise ValueError(
                        f"El adicional {codigo} requiere {regla.clave_cantidad_base} positivo"
                    )
                if cantidad > cantidad_base:
                    raise ValueError(
                        f"Las horas de {codigo} no pueden superar las horas totales del período"
                    )
                multiplicador = cantidad / cantidad_base
            elif regla.modo_calculo == "remanente_fondo":
                faltante = Decimal(cantidades.get(codigo, 0))
                if faltante < 0:
                    raise ValueError(f"El faltante informado para {codigo} no puede ser negativo")
                fondo = base_adicional.porcentaje(regla.porcentaje)
                importe_directo = max(fondo.monto - faltante, Decimal("0"))
                cantidad = faltante
            elif regla.modo_calculo != "multiplicador":
                raise ValueError(f"Modo de cálculo inválido para {codigo}")

            importe = (
                Dinero(importe_directo).redondear()
                if importe_directo is not None
                else base_adicional.porcentaje(regla.porcentaje).multiplicar(
                    multiplicador
                ).redondear()
            )
            conceptos.append(Concepto(
                codigo, regla.descripcion, TipoConcepto.REMUNERATIVO,
                importe, cantidad=cantidad, base_calculo=base_adicional,
                unidad=(f"{regla.porcentaje * 100}%"
                        if regla.modo_calculo == "multiplicador"
                        else regla.modo_calculo),
            ))

        # Presentismo: base = básico + NR que integran presentismo + antigüedad
        if cct.aplica_presentismo:
            base_pres = (basico + _nr("integra_presentismo") + antiguedad).redondear()
            presentismo = base_pres.dividir(cct.presentismo_divisor).redondear()
            conceptos.append(
                Concepto(
                    "PRESENTISMO", "Presentismo", TipoConcepto.REMUNERATIVO,
                    presentismo, base_calculo=base_pres,
                    unidad=f"1/{cct.presentismo_divisor}",
                )
            )

        # Horas extra (valor hora sobre básico + antigüedad)
        if novedades.horas_extra_50 > 0:
            vh = self._valor_hora(basico, antiguedad, cct)
            imp = vh.multiplicar(Decimal("1.5")).multiplicar(novedades.horas_extra_50).redondear()
            conceptos.append(
                Concepto("HORAS_EXTRA_50", "Horas extra al 50%", TipoConcepto.REMUNERATIVO,
                         imp, cantidad=novedades.horas_extra_50, base_calculo=vh,
                         unidad="hora x 1,5")
            )
        if novedades.horas_extra_100 > 0:
            vh = self._valor_hora(basico, antiguedad, cct)
            imp = vh.multiplicar(Decimal("2")).multiplicar(novedades.horas_extra_100).redondear()
            conceptos.append(
                Concepto("HORAS_EXTRA_100", "Horas extra al 100%", TipoConcepto.REMUNERATIVO,
                         imp, cantidad=novedades.horas_extra_100, base_calculo=vh,
                         unidad="hora x 2")
            )

        if novedades.premio > 0 and novedades.tipo_premio == "remunerativo":
            conceptos.append(Concepto(
                "PREMIO_REMUNERATIVO", "Premio remunerativo",
                TipoConcepto.REMUNERATIVO, Dinero(novedades.premio).redondear(),
            ))
        elif novedades.premio > 0 and novedades.tipo_premio == "no_remunerativo":
            conceptos.append(Concepto(
                "PREMIO_NO_REMUNERATIVO", "Premio no remunerativo",
                TipoConcepto.NO_REMUNERATIVO, Dinero(novedades.premio).redondear(),
            ))

        # Base remunerativa = suma de conceptos remunerativos
        base = Dinero.cero()
        for c in conceptos:
            if c.tipo == TipoConcepto.REMUNERATIVO:
                base = base + c.importe
        base = base.redondear()

        # Bases de aportes (data-driven): remunerativos + NR que disparan cada aporte
        base_jubilacion = (base + _nr("aporte_jubilacion")).redondear()
        base_obra_social = (base + _nr("aporte_obra_social")).redondear()
        base_sindical = (base + _nr("aporte_sindicato")).redondear()

        # Tope SIPA sobre la seguridad social
        tope = self._p.valor_ars("TOPE_SIPA") if self._p.existe("TOPE_SIPA") else None
        base_jub_t = Dinero.minimo(base_jubilacion, tope) if tope else base_jubilacion
        base_os_t = Dinero.minimo(base_obra_social, tope) if tope else base_obra_social

        # ----- Deducciones del trabajador (cada una sobre SU base) -----
        conceptos.append(self._deduccion("APORTE_JUBILACION", "Jubilación (11%)", base_jub_t))
        conceptos.append(self._deduccion("APORTE_LEY19032", "Ley 19.032 - INSSJP (3%)", base_jub_t))
        conceptos.append(self._deduccion("APORTE_OBRA_SOCIAL", "Obra social (3%)", base_os_t))

        if cct.aplica_cuota_sindical and empleado.afiliado_sindicato:
            # Cuota propia del convenio si está definida; si no, parámetro global.
            pct = cct.cuota_sindical_pct if cct.cuota_sindical_pct is not None \
                else self._p.fraccion("CUOTA_SINDICAL")
            imp = base_sindical.porcentaje(pct).redondear()
            conceptos.append(Concepto("CUOTA_SINDICAL", "Cuota sindical",
                                      TipoConcepto.DEDUCCION, imp,
                                      base_calculo=base_sindical,
                                      unidad=f"{pct * 100}%"))

        # ----- Deducciones porcentuales del convenio (aportes/cuotas, data-driven) -----
        # Cada una lleva su condición de aplicación en 'ambito':
        #   ded_todos  -> a todo trabajador comprendido (p.ej. aporte art.100, FAECYS)
        #   ded_afil   -> solo afiliados (p.ej. cuota art.101)
        #   ded_noafil -> solo no afiliados (p.ej. aporte solidario UOCRA)
        # Base predeterminada: la base sindical (remunerativo + NR cuya
        # incidencia lo dispare). Convenios que exponen importes separados en
        # el recibo pueden declarar ``base_deduccion`` en incidencias:
        #   remunerativa | no_remunerativa_sindical | sindical.
        for d in self._p.deducciones_convenio(cct.cct_numero):
            meses = (d.incidencias or {}).get("meses_aplicacion")
            if meses and periodo.mes not in {int(mes) for mes in meses}:
                continue
            aplica = (d.ambito == "ded_todos"
                      or (d.ambito == "ded_afil" and empleado.afiliado_sindicato)
                      or (d.ambito == "ded_noafil" and not empleado.afiliado_sindicato))
            if aplica:
                selector_base = (d.incidencias or {}).get("base_deduccion", "sindical")
                bases_deduccion = {
                    "sindical": base_sindical,
                    "remunerativa": base,
                    "no_remunerativa_sindical": _nr("aporte_sindicato").redondear(),
                }
                if selector_base not in bases_deduccion:
                    raise ValueError(
                        f"Base de deducción inválida para {d.codigo}: {selector_base}"
                    )
                imp = bases_deduccion[selector_base].porcentaje(d.valor).redondear()
                absorbe_codigos = set((d.incidencias or {}).get("absorbe_codigos", []))
                if absorbe_codigos:
                    absorbido = Dinero.cero()
                    for concepto_existente in conceptos:
                        if concepto_existente.codigo in absorbe_codigos:
                            absorbido = absorbido + concepto_existente.importe
                    imp = Dinero(max(imp.monto - absorbido.monto, Decimal("0"))).redondear()
                conceptos.append(Concepto(d.codigo, _desc_ded(d.codigo),
                                          TipoConcepto.DEDUCCION, imp,
                                          base_calculo=bases_deduccion[selector_base],
                                          unidad=f"{d.valor * 100}%",
                                          destino_pago=(d.incidencias or {}).get("destino_pago"),
                                          codigo_boleta=(d.incidencias or {}).get("codigo_boleta"),
                                          canal_pago=(d.incidencias or {}).get("canal_pago"),
                                          url_pago=(d.incidencias or {}).get("url_pago"),
                                          regla_vencimiento=(d.incidencias or {}).get("regla_vencimiento"),
                                          fuente_pago=(d.incidencias or {}).get("fuente_pago")))

        # ----- Concepto con estrategia por amparo (Ley 27.802 art. 131) -----
        conceptos.append(self._aporte_modernizacion(empleado, periodo, base))

        # ----- Contribuciones patronales (desglose Anexo III) -----
        conceptos.append(self._contribucion("CONTRIB_JUBILACION", "Contrib. jubilación (18%)", base))
        conceptos.append(self._contribucion("CONTRIB_OBRA_SOCIAL", "Contrib. obra social (6%)", base))
        if self._p.existe("CONTRIB_INSSJP"):
            conceptos.append(self._contribucion("CONTRIB_INSSJP", "Contrib. INSSJP", base))
        if self._p.existe("CONTRIB_ASIG_FAM"):
            conceptos.append(self._contribucion("CONTRIB_ASIG_FAM", "Asignaciones familiares", base))

        # Obligaciones patronales propias del convenio. No afectan el neto y
        # conservan sus datos de boleta para la carpeta mensual.
        for p in self._p.contribuciones_convenio(cct.cct_numero):
            incidencias = p.incidencias or {}
            meses = {int(mes) for mes in incidencias.get("meses_aplicacion", [])}
            excluidos = {int(mes) for mes in incidencias.get("meses_excluidos", [])}
            if meses and periodo.mes not in meses:
                continue
            if periodo.mes in excluidos:
                continue
            if p.unidad == "ARS":
                importe = Dinero(p.valor)
                if incidencias.get("prorratea_jornada"):
                    importe = importe.porcentaje(empleado.proporcion_jornada)
            elif p.unidad == "%":
                selector = incidencias.get("base_contribucion", "remunerativa")
                bases = {"remunerativa": base, "sindical": base_sindical}
                if selector not in bases:
                    raise ValueError(f"Base de contribución inválida para {p.codigo}: {selector}")
                importe = bases[selector].porcentaje(p.valor)
            else:
                raise ValueError(f"Unidad de contribución inválida para {p.codigo}: {p.unidad}")
            conceptos.append(Concepto(
                p.codigo, _desc_contrib_convenio(p.codigo), TipoConcepto.CONTRIBUCION,
                importe.redondear(),
                base_calculo=(bases[selector] if p.unidad == "%" else importe),
                unidad=(f"{p.valor * 100}%" if p.unidad == "%" else "suma fija"),
                destino_pago=incidencias.get("destino_pago"),
                codigo_boleta=incidencias.get("codigo_boleta"),
                canal_pago=incidencias.get("canal_pago"),
                url_pago=incidencias.get("url_pago"),
                regla_vencimiento=incidencias.get("regla_vencimiento"),
                fuente_pago=incidencias.get("fuente_pago"),
            ))

        if novedades.descuento_adicional > 0:
            descripcion = "Descuento adicional"
            if novedades.detalle_descuento.strip():
                descripcion += f": {novedades.detalle_descuento.strip()}"
            conceptos.append(Concepto(
                "DESCUENTO_ADICIONAL", descripcion, TipoConcepto.DEDUCCION,
                Dinero(novedades.descuento_adicional).redondear(),
            ))

        return ResultadoLiquidacion(empleado.cuil.valor, periodo, "mensual", conceptos)

    def _deduccion(self, codigo: str, descripcion: str, base: Dinero) -> Concepto:
        pct = self._p.fraccion(codigo)
        imp = base.porcentaje(pct).redondear()
        return Concepto(
            codigo, descripcion, TipoConcepto.DEDUCCION, imp,
            base_calculo=base, unidad=f"{pct * 100}%",
        )

    def _contribucion(self, codigo: str, descripcion: str, base: Dinero) -> Concepto:
        pct = self._p.fraccion(codigo)
        imp = base.porcentaje(pct).redondear()
        return Concepto(
            codigo, descripcion, TipoConcepto.CONTRIBUCION, imp,
            base_calculo=base, unidad=f"{pct * 100}%",
        )

    def _aporte_modernizacion(
        self, empleado: Empleado, periodo: Periodo, base: Dinero
    ) -> Concepto:
        """Aporte creado por el art. 131 de la Ley 27.802.

        - ``regla_ley_27802``: se retiene ``APORTE_MODERNIZACION`` % de la base.
        - ``regla_previa``: no existía => 0 (reactivada por amparo FAECYS/Comercio).
        """
        amparo = self._amparos.amparo_vigente(
            empleado.cct_numero, _CONCEPTO_MODERNIZACION, periodo
        )
        if amparo is not None:
            # regla_previa: el aporte no corre
            return Concepto(
                _CONCEPTO_MODERNIZACION,
                "Aporte modernización (SUSPENDIDO por amparo)",
                TipoConcepto.DEDUCCION,
                Dinero.cero().redondear(),
                base_calculo=base,
                unidad="0% (amparo)",
                regimen=Regimen.PREVIA,
                articulo_amparo=amparo.articulo_suspendido,
            )
        # regla_ley_27802
        imp = base.porcentaje(self._p.fraccion(_CONCEPTO_MODERNIZACION)).redondear()
        return Concepto(
            _CONCEPTO_MODERNIZACION,
            "Aporte modernización (Ley 27.802 art. 131)",
            TipoConcepto.DEDUCCION,
            imp,
            base_calculo=base,
            unidad=f"{self._p.fraccion(_CONCEPTO_MODERNIZACION) * 100}%",
            regimen=Regimen.LEY_27802,
        )

    # ------------------------------------------------------------------ #
    # SAC (medio aguinaldo)
    # ------------------------------------------------------------------ #
    def liquidar_sac(
        self,
        empleado: Empleado,
        periodo: Periodo,
        mejor_remuneracion_semestre: Dinero,
        dias_trabajados_semestre: int = 181,
    ) -> ResultadoLiquidacion:
        """SAC = 50% de la mejor remuneración del semestre, proporcional a días."""
        proporcion = Decimal(dias_trabajados_semestre) / Decimal(181)
        bruto = mejor_remuneracion_semestre.multiplicar(Decimal("0.5")).multiplicar(proporcion)
        bruto = bruto.redondear()
        conceptos: List[Concepto] = [
            Concepto("SAC", "SAC (50% mejor remuneración)", TipoConcepto.REMUNERATIVO, bruto)
        ]
        # Aportes sobre el SAC (seguridad social)
        conceptos.append(self._deduccion("APORTE_JUBILACION", "Jubilación (11%)", bruto))
        conceptos.append(self._deduccion("APORTE_LEY19032", "Ley 19.032 - INSSJP (3%)", bruto))
        conceptos.append(self._deduccion("APORTE_OBRA_SOCIAL", "Obra social (3%)", bruto))
        return ResultadoLiquidacion(empleado.cuil.valor, periodo, "sac", conceptos)

    # ------------------------------------------------------------------ #
    # Vacaciones
    # ------------------------------------------------------------------ #
    @staticmethod
    def dias_vacaciones(anios: int) -> int:
        """LCT art. 150. Antigüedad computada al 31/12 (art. 151)."""
        if anios < 5:
            return 14
        if anios < 10:
            return 21
        if anios < 20:
            return 28
        return 35

    def liquidar_vacaciones(
        self,
        empleado: Empleado,
        periodo: Periodo,
        remuneracion_habitual: Dinero,
    ) -> ResultadoLiquidacion:
        anios = empleado.antiguedad_anios(periodo.ultimo_dia_del_anio())
        dias = self.dias_vacaciones(anios)
        valor_dia = remuneracion_habitual.dividir(Decimal("25"))  # LCT: /25
        imp = valor_dia.multiplicar(Decimal(dias)).redondear()
        conceptos = [
            Concepto("VACACIONES", f"Vacaciones ({dias} días)", TipoConcepto.REMUNERATIVO,
                     imp, cantidad=Decimal(dias))
        ]
        return ResultadoLiquidacion(empleado.cuil.valor, periodo, "vacaciones", conceptos)
