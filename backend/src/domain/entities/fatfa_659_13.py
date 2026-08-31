"""Reglas de adicionales del CCT 659/13 FATFA.

Las fórmulas permanentes provienen del CCT homologado por Resolución ST 94/2013.
Los importes de bloqueo/título son referencias temporales de la escala FATFA
agosto 2026 y se reciben desde la base, nunca quedan fijados en el motor.
"""
from __future__ import annotations

from decimal import Decimal

from domain.payroll_engine.config import ReglaAdicionalConfig


CCT_FATFA = "659/13"


def configurar_adicionales_fatfa(
    basico_aprendiz: Decimal,
    referencias_titulo: dict[str, Decimal],
) -> tuple[tuple[ReglaAdicionalConfig, ...], tuple[tuple[str, Decimal], ...]]:
    """Convierte los arts. 7, 22 y 23 en reglas explícitas y auditables."""
    reglas = [
        ReglaAdicionalConfig(
            "FATFA_CAP_AUXILIAR", "Certificado de Auxiliar de Farmacia",
            Decimal("0.10"), "referencia_mas_antiguedad:APRENDIZ",
            "22.a",
        ),
        ReglaAdicionalConfig(
            "FATFA_CAP_TECNICO", "Técnico en Gestión de Farmacia",
            Decimal("0.20"), "referencia_mas_antiguedad:APRENDIZ",
            "22.b",
        ),
        ReglaAdicionalConfig(
            "FATFA_CAP_PROFESIONAL", "Actualización y capacitación profesional",
            Decimal("0.30"), "referencia:BLOQUEO_DT", "22.c",
        ),
        ReglaAdicionalConfig(
            "FATFA_TITULO_SECUNDARIO", "Título secundario admitido",
            Decimal("0.05"), "basico_categoria_mas_antiguedad", "22.c",
        ),
        ReglaAdicionalConfig(
            "FATFA_ADMINISTRATIVO", "Tareas administrativas (5 años)",
            Decimal("0.10"), "basico_categoria_mas_antiguedad", "22.d",
        ),
        ReglaAdicionalConfig(
            "FATFA_PERFUMERIA", "Tareas de perfumería (5 años)",
            Decimal("0.10"), "basico_categoria_mas_antiguedad", "22.e",
        ),
        ReglaAdicionalConfig(
            "FATFA_IDIOMA", "Idioma extranjero requerido",
            Decimal("0.10"), "basico_categoria_mas_antiguedad", "22.f",
            requiere_cantidad=True,
        ),
        ReglaAdicionalConfig(
            "FATFA_VEHICULO", "Uso de bicicleta, motocicleta o ciclomotor propio",
            Decimal("0.15"), "basico_categoria_mas_antiguedad", "22.g",
        ),
        ReglaAdicionalConfig(
            "FATFA_FALLA_CAJA", "Fondo compensador por falla de caja",
            Decimal("0.20"), "basico_categoria", "23",
            naturaleza="no_remunerativo",
        ),
    ]
    for codigo, descripcion, referencia in (
        ("FATFA_BLOQUEO_DT", "Bloqueo de título — Director Técnico", "BLOQUEO_DT"),
        ("FATFA_BLOQUEO_DT_NR", "Suma NR bloqueo — Director Técnico", "BLOQUEO_DT_NR"),
        ("FATFA_AUX_BLOQUEO", "Auxiliar con bloqueo de título (80%)", "AUX_BLOQUEO"),
        ("FATFA_AUX_BLOQUEO_NR", "Suma NR auxiliar con bloqueo", "AUX_BLOQUEO_NR"),
        ("FATFA_TITULO_60", "Título de Farmacéutico (60%)", "TITULO_60"),
        ("FATFA_TITULO_60_NR", "Suma NR título de Farmacéutico", "TITULO_60_NR"),
    ):
        reglas.append(ReglaAdicionalConfig(
            codigo, descripcion, Decimal("1"), f"referencia:{referencia}",
            "7", naturaleza="no_remunerativo",
        ))

    referencias = [("APRENDIZ", Decimal(basico_aprendiz))]
    referencias.extend((clave, Decimal(valor)) for clave, valor in referencias_titulo.items())
    return tuple(reglas), tuple(referencias)
