"""Cuota de la ART calculada desde el contrato del establecimiento.

La cuota de riesgos del trabajo es, en todos los contratos, una alícuota sobre
la remuneración sujeta a aportes más una suma fija por trabajador. Los dos
valores están en el contrato y ya se cargan en el establecimiento, así que
pedirle al empleador el importe mensual de cada persona al momento de imprimir
el recibo es pedirle que haga a mano una cuenta que el sistema tiene.

Se calcula sólo cuando el contrato está cargado y vigente en el período. Si
falta la alícuota, o el contrato no cubre el mes, no se estima nada: se
devuelve ``None`` y el empleador informa el importe, como antes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

DOS_DECIMALES = Decimal("0.01")


@dataclass(frozen=True)
class ContratoArt:
    """Lo que dice el contrato de afiliación cargado en el establecimiento."""

    nombre: str
    alicuota_pct: Optional[Decimal]
    suma_fija: Optional[Decimal]
    vigencia_desde: Optional[date]
    vigencia_hasta: Optional[date]
    comprobante: str = ""

    def cubre(self, fecha: date) -> bool:
        if self.vigencia_desde and fecha < self.vigencia_desde:
            return False
        if self.vigencia_hasta and fecha > self.vigencia_hasta:
            return False
        return True


@dataclass(frozen=True)
class CuotaArt:
    importe: Decimal
    descripcion: str
    detalle: str


def calcular_cuota_art(
    contrato: Optional[ContratoArt],
    base_remunerativa: Decimal,
    fecha: date,
) -> Optional[CuotaArt]:
    """Alícuota sobre la remuneración más la suma fija por trabajador.

    Devuelve ``None`` -y no un cero, que se leería como "no corresponde"- cuando
    no hay contrato cargado, cuando no cubre el período o cuando no tiene
    alícuota. En esos casos el importe lo sigue informando el empleador.
    """
    if contrato is None or not contrato.cubre(fecha):
        return None
    if contrato.alicuota_pct is None:
        return None

    alicuota = Decimal(str(contrato.alicuota_pct))
    if alicuota < 0:
        raise ValueError("La alícuota de ART no puede ser negativa")
    fija = Decimal(str(contrato.suma_fija or 0))
    if fija < 0:
        raise ValueError("La suma fija de ART no puede ser negativa")

    # Como en el resto del sistema: se redondea una sola vez, al final.
    base = Decimal(str(base_remunerativa))
    importe = (base * alicuota / Decimal("100") + fija).quantize(
        DOS_DECIMALES, rounding=ROUND_HALF_UP
    )

    nombre = (contrato.nombre or "").strip() or "ART contratada"
    detalle = (
        f"{alicuota.normalize():f}% sobre $ {base.quantize(Decimal('0.01'))}"
        + (f" más suma fija $ {fija.quantize(Decimal('0.01'))}" if fija else "")
    )
    return CuotaArt(
        importe=importe,
        descripcion=f"ART - {nombre} (alícuota del contrato)",
        detalle=detalle,
    )
