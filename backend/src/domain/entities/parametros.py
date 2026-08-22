"""Parámetros legales versionados y set de amparos (dominio puro).

Ningún valor legal vive hardcodeado en el motor: el motor recibe estos objetos
y solo lee de ellos (sección 0.2 del prompt maestro).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from ..value_objects.dinero import Dinero
from ..value_objects.periodo import Periodo


@dataclass(frozen=True)
class ParametroLegal:
    codigo: str                 # p.ej. "APORTE_JUBILACION"
    valor: Decimal
    unidad: str                 # "%" (fracción, 0.11 == 11%) | "ARS"
    ambito: str                 # "empleado" | "empleador"
    valid_from: date
    valid_to: Optional[date] = None
    is_verified: bool = False
    fuente: str = ""
    cct_numero: Optional[str] = None      # concepto propio de un convenio (null = global)
    incidencias: Optional[dict] = None    # qué bases integra / qué aportes dispara


@dataclass(frozen=True)
class EscalaSalarial:
    cct_numero: str
    categoria: str
    basico: Dinero
    valid_from: date
    valid_to: Optional[date] = None
    is_verified: bool = False
    fuente: str = ""
    # Escala PROVISORIA: reutiliza un básico verificado anterior por una vigencia
    # acotada y explícita (dato versionado). Exige confirmación antes de liquidar.
    provisoria: bool = False
    # Vacío = escala nacional. Los convenios regionalizados usan el código
    # definido por su regla estructural (por ejemplo A, B, C, C_AUSTRAL).
    zona: str = ""
    # Unidad declarada por la fuente: MENSUAL u HORA. Nunca se infiere por el monto.
    unidad_escala: str = "MENSUAL"
    # Una escala puede estar documentada pero todavía no ser liquidable por el motor.
    habilitada_liquidacion: bool = True
    estado_fuente: str = "VERIFICADA_OFICIAL"
    basico_puro: Optional[Dinero] = None
    adicional_zona: Optional[Dinero] = None


@dataclass(frozen=True)
class Amparo:
    """Cautelar que suspende un artículo de la Ley 27.802 / Decreto 407/2026.

    ``concepto_afectado`` es el código interno del motor de cálculo cuyo régimen
    cambia cuando el amparo está vigente.
    """

    cct_numero: str
    articulo_suspendido: str    # "L27802:131", "D407:5", ...
    concepto_afectado: str      # código interno del motor, p.ej. "APORTE_MODERNIZACION"
    estado: str                 # "vigente" | "revocada" | "firme"
    valid_from: date
    valid_to: Optional[date] = None
    juzgado: str = ""
    is_verified: bool = False


@dataclass(frozen=True)
class CuotaArt101:
    """Cuota sindical del Art. 101 (afiliados), configurable por filial/localidad.

    NO existe un valor nacional por defecto: cada filial/jurisdiccion define su
    porcentaje y vigencia, y solo se aplica si ``is_verified`` es True.
    """

    cct_numero: str
    porcentaje: Decimal
    valid_from: date
    valid_to: Optional[date] = None
    sindicato: Optional[str] = None
    filial: Optional[str] = None
    localidad: Optional[str] = None
    fuente: str = ""
    is_verified: bool = False


def resolver_cuota_art101(
    candidatas: List[CuotaArt101],
    cct_numero: str,
    localidad: Optional[str],
    filial: Optional[str],
    fecha: date,
) -> Optional[CuotaArt101]:
    """Elige la cuota Art. 101 OFICIAL vigente que corresponde a un afiliado.

    Reglas (sin inventar nada):
    - Solo cuotas del mismo CCT, ``is_verified`` y vigentes a ``fecha``.
    - Prioridad: coincidencia por ``filial``; si no, por ``localidad``.
    - Si hay varias, gana la de ``valid_from`` mas reciente.
    - Si no hay coincidencia, devuelve None (el sistema NO aplica porcentaje).
    """
    def vigente(c: CuotaArt101) -> bool:
        return c.valid_from <= fecha and (c.valid_to is None or c.valid_to >= fecha)

    elegibles = [c for c in candidatas
                 if c.cct_numero == cct_numero and c.is_verified and vigente(c)]
    if not elegibles:
        return None
    if filial:
        por_filial = [c for c in elegibles if (c.filial or "") == filial]
        if por_filial:
            return max(por_filial, key=lambda c: c.valid_from)
    if localidad:
        por_localidad = [c for c in elegibles if (c.localidad or "") == localidad]
        if por_localidad:
            return max(por_localidad, key=lambda c: c.valid_from)
    return None


class ParametroSet:
    """Conjunto de parámetros vigentes para una liquidación."""

    def __init__(self, parametros: List[ParametroLegal]):
        self._por_codigo: Dict[str, ParametroLegal] = {p.codigo: p for p in parametros}
        self._todos: List[ParametroLegal] = list(parametros)

    def con_extra(self, parametro: ParametroLegal) -> "ParametroSet":
        """Devuelve un ParametroSet nuevo con un parametro adicional (p.ej. la
        cuota Art. 101 ya resuelta por filial/localidad). No muta el original."""
        return ParametroSet(self._todos + [parametro])

    def conceptos_convenio(self, cct_numero: str) -> List[ParametroLegal]:
        """Conceptos en ARS propios de un convenio (NR/adicionales), ya filtrados
        por período. El motor los aplica leyendo sus ``incidencias`` —sin saber
        de qué convenio se trata."""
        return [p for p in self._todos
                if p.cct_numero == cct_numero and p.unidad == "ARS"
                and p.ambito != "contrib_emp"]

    @staticmethod
    def categoria_coincide(requerida: Optional[str], categoria: str) -> bool:
        """Compara categorías declarativas sin depender de un convenio."""
        if not requerida:
            return True
        tabla = str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun")

        def normalizar(texto: str) -> str:
            return " ".join(str(texto or "").translate(tabla).casefold().split())

        return normalizar(requerida) == normalizar(categoria)

    def conceptos_sin_regla_jornada(
        self, cct_numero: str, categoria: str, proporcion_jornada: Decimal
    ) -> List[ParametroLegal]:
        """Conceptos aplicables que no autorizan liquidación a jornada parcial."""
        if proporcion_jornada == Decimal("1"):
            return []
        resultado = []
        for parametro in self.conceptos_convenio(cct_numero):
            incidencias = parametro.incidencias or {}
            if not self.categoria_coincide(incidencias.get("categoria"), categoria):
                continue
            if incidencias.get("regla_jornada") == "solo_completa":
                resultado.append(parametro)
        return resultado

    def contribuciones_convenio(self, cct_numero: str) -> List[ParametroLegal]:
        """Obligaciones patronales propias del convenio, fijas o porcentuales."""
        return [p for p in self._todos
                if p.cct_numero == cct_numero and p.ambito == "contrib_emp"]

    def deducciones_convenio(self, cct_numero: str) -> List[ParametroLegal]:
        """Deducciones porcentuales propias de un convenio (aportes/cuotas), ya
        filtradas por período. La condición de aplicación va en ``ambito``:
        ``ded_todos`` (todo comprendido) | ``ded_afil`` (solo afiliados) |
        ``ded_noafil`` (solo no afiliados)."""
        return [p for p in self._todos
                if p.cct_numero == cct_numero and p.unidad == "%"
                and (p.ambito or "").startswith("ded_")]

    def _obtener(self, codigo: str) -> ParametroLegal:
        if codigo not in self._por_codigo:
            raise KeyError(f"Parámetro legal faltante: {codigo}")
        return self._por_codigo[codigo]

    def fraccion(self, codigo: str) -> Decimal:
        """Devuelve el valor como fracción (0.11 para 11%)."""
        p = self._obtener(codigo)
        if p.unidad != "%":
            raise ValueError(f"{codigo} no es un porcentaje")
        return p.valor

    def valor_ars(self, codigo: str) -> Dinero:
        p = self._obtener(codigo)
        if p.unidad != "ARS":
            raise ValueError(f"{codigo} no es un valor en ARS")
        return Dinero(p.valor)

    def existe(self, codigo: str) -> bool:
        return codigo in self._por_codigo

    def hay_no_verificados(self) -> bool:
        return any(not p.is_verified for p in self._por_codigo.values())

    def pendientes_normativos(self) -> List[ParametroLegal]:
        """Reglas no aprobadas o sin respaldo documental."""
        return [
            p for p in self._todos
            if not p.is_verified or not (p.fuente or "").strip()
        ]


class AmparoSet:
    """Conjunto de amparos; decide qué régimen aplicar por concepto."""

    def __init__(self, amparos: Optional[List[Amparo]] = None):
        self._amparos: List[Amparo] = list(amparos) if amparos else []

    def amparo_vigente(
        self, cct_numero: str, concepto_afectado: str, periodo: Periodo
    ) -> Optional[Amparo]:
        """Devuelve el amparo aplicable al concepto en el período, o None."""
        ref = periodo.primer_dia()
        for a in self._amparos:
            if a.cct_numero != cct_numero:
                continue
            if a.concepto_afectado != concepto_afectado:
                continue
            if a.estado != "vigente":
                continue
            if a.valid_from > ref:
                continue
            if a.valid_to is not None and a.valid_to < ref:
                continue
            return a
        return None
