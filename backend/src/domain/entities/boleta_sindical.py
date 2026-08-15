"""Agrupación auditable de obligaciones sindicales por destino de pago."""
from __future__ import annotations

from decimal import Decimal


def agrupar_obligaciones_sindicales(detalles: list[dict]) -> list[dict]:
    """Agrupa conceptos ya calculados sin volver a aplicar porcentajes.

    La clave contempla convenio, entidad, boleta, filial y localidad. Esto
    permite que una empresa tenga varios convenios y que un mismo gremio exija
    más de una boleta para el mismo período.
    """
    grupos: dict[tuple, dict] = {}
    for detalle in detalles:
        cct = detalle.get("cct_numero") or ""
        filial = detalle.get("filial_sindical") or ""
        localidad = detalle.get("localidad") or ""
        empleado_id = str(detalle.get("empleado_id") or "")
        for concepto in detalle.get("conceptos", []):
            destino = (concepto.get("destino_pago") or "").strip()
            codigo_boleta = (concepto.get("codigo_boleta") or "").strip()
            if not destino or not codigo_boleta:
                continue
            clave = (cct, destino, codigo_boleta, filial, localidad)
            grupo = grupos.setdefault(clave, {
                "cct_numero": cct,
                "destino_pago": destino,
                "codigo_boleta": codigo_boleta,
                "filial_sindical": filial or None,
                "localidad": localidad or None,
                "importe": Decimal("0"),
                "empleados": set(),
                "conceptos": {},
            })
            importe = Decimal(str(concepto["importe"]))
            grupo["importe"] += importe
            if empleado_id:
                grupo["empleados"].add(empleado_id)
            codigo = str(concepto.get("codigo") or "SIN_CODIGO")
            grupo["conceptos"][codigo] = grupo["conceptos"].get(codigo, Decimal("0")) + importe

    salida = []
    for grupo in grupos.values():
        salida.append({
            **{k: v for k, v in grupo.items() if k not in {"empleados", "conceptos", "importe"}},
            "cantidad_empleados": len(grupo["empleados"]),
            "importe": str(grupo["importe"].quantize(Decimal("0.01"))),
            "conceptos": {
                codigo: str(importe.quantize(Decimal("0.01")))
                for codigo, importe in sorted(grupo["conceptos"].items())
            },
        })
    return sorted(
        salida,
        key=lambda x: (
            x["cct_numero"], x["destino_pago"], x["codigo_boleta"],
            x["filial_sindical"] or "", x["localidad"] or "",
        ),
    )
