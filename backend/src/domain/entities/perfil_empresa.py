"""Resolución pura del régimen general de contribuciones de una empresa."""

SECTORES = {
    "PENDIENTE", "COMERCIO", "SERVICIOS", "INDUSTRIA",
    "CONSTRUCCION", "AGRO", "MINERIA", "OTRO",
}
CONDICIONES_MIPYME = {"PENDIENTE", "CERTIFICADO_VIGENTE", "SUPERA_LIMITES"}


def resolver_regimen_contribucion(
    actividad_sector: str,
    condicion_mipyme: str,
) -> tuple[str, str]:
    """Deriva la alícuota; nunca la acepta como dato elegido por el usuario."""
    if actividad_sector not in SECTORES:
        raise ValueError("Actividad inválida")
    if condicion_mipyme not in CONDICIONES_MIPYME:
        raise ValueError("Condición MiPyME inválida")
    if condicion_mipyme == "CERTIFICADO_VIGENTE":
        return (
            "PRIVADO_18",
            "Certificado MiPyME vigente informado por la empresa",
        )
    if (
        condicion_mipyme == "SUPERA_LIMITES"
        and actividad_sector in {"COMERCIO", "SERVICIOS"}
    ):
        return (
            "SERVICIOS_COMERCIO_204",
            "Comercio/servicios por encima de los límites MiPyME",
        )
    if condicion_mipyme == "SUPERA_LIMITES":
        return (
            "PRIVADO_18",
            "Empleador privado no incluido en comercio/servicios 20,40%",
        )
    return "PENDIENTE", ""
