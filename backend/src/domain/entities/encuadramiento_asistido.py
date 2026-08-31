"""Asistencia explicable para elegir CCT sin reemplazar la decisión laboral."""
from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from domain.entities.farmacia_414_05 import AMBITO_TERRITORIAL_414_05


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or ""))
    return " ".join("".join(c for c in base if not unicodedata.combining(c)).upper().split())


@dataclass(frozen=True)
class ReglaActividad:
    cct: str
    nombre: str
    palabras_actividad: tuple[str, ...]
    palabras_tarea: tuple[str, ...] = ()


REGLAS = (
    ReglaActividad("122/75", "Clínicas, sanatorios y establecimientos con internación",
                   ("CLINICA", "SANATORIO", "GERIATRICO", "INTERNACION", "HOSPITAL"),
                   ("ENFERMER", "MUCAMA", "CAMILLER", "RADIOLOG", "LABORATOR")),
    ReglaActividad("130/75", "Empleados de Comercio",
                   ("COMERCIO", "VENTA", "SUPERMERCADO", "MAYORISTA", "MINORISTA"),
                   ("VENDEDOR", "CAJERO", "ADMINISTRATIVO", "MAESTRANZA")),
    ReglaActividad("260/75", "Metalúrgicos",
                   ("METALURG", "METALMECAN", "SIDERURG", "FABRICA METAL"),
                   ("SOLDADOR", "TORNERO", "MECANICO", "OPERARIO")),
    ReglaActividad("389/04", "Gastronómicos y hoteleros",
                   ("HOTEL", "RESTAURANT", "GASTRONOM", "BAR ", "CONFITERIA", "ALOJAMIENTO"),
                   ("MOZO", "COCINER", "RECEPCION", "MUCAMA")),
    ReglaActividad("40/89", "Camioneros",
                   ("TRANSPORTE", "LOGISTICA", "DISTRIBUCION", "FLETE", "CAMION"),
                   ("CHOFER", "REPARTIDOR", "CAMION", "AUXILIAR")),
    ReglaActividad("76/75", "Construcción",
                   ("CONSTRUCCION", "OBRA CIVIL", "ALBANIL", "EDIFICACION"),
                   ("OFICIAL", "MEDIO OFICIAL", "AYUDANTE", "SERENO")),
)


def _contiene(texto: str, palabras: tuple[str, ...]) -> bool:
    return any(p in texto for p in palabras)


def sugerir_encuadramiento(
    actividad: str, localidad: str, tarea: str, provincia: str = "",
) -> dict:
    act, loc, tar, prov = map(_normalizar, (actividad, localidad, tarea, provincia))
    faltantes = []
    if not act:
        faltantes.append("Actividad real del establecimiento")
    if not loc:
        faltantes.append("Localidad del lugar de trabajo")
    if not tar:
        faltantes.append("Tarea principal del empleado")

    candidatos = []
    es_farmacia = "FARMACIA" in act or "FARMACEUT" in act
    es_cementerio = any(p in act for p in ("CEMENTERIO", "CREMATORIO", "PANTEON", "PARQUE CEMENTERIO"))
    es_funeraria = any(p in act for p in ("FUNERARIA", "COCHERIA", "POMPAS FUNEBRES", "CASA VELATORIA", "SERVICIO FUNEBRE"))
    es_municipal = "MUNICIPAL" in act or "MUNICIPIO" in act

    if es_cementerio and es_municipal:
        faltantes.append(
            "Los cementerios municipales están excluidos del CCT 761/19; "
            "confirmar si existe concesión privada"
        )
    elif es_cementerio:
        candidatos.append({
            "cct_numero": "761/19",
            "nombre": "Cementerios privados, parques cementerio y crematorios",
            "confianza": "media",
            "motivos": [
                "La actividad declarada corresponde a un cementerio, parque cementerio o crematorio",
                "El CCT 761/19 encuadra establecimientos privados y concesiones privadas",
            ],
            "advertencias": [
                "Confirmar que no sea explotación municipal directa",
                "Seleccionar manualmente la zona con respaldo documental",
                "La escala agosto 2026 es provisoria y no está habilitada para liquidación definitiva",
            ],
        })
    elif es_funeraria:
        candidatos.append({
            "cct_numero": "749/18",
            "nombre": "Cocherías, pompas fúnebres y casas velatorias",
            "confianza": "media",
            "motivos": [
                "La actividad declarada corresponde a servicios funerarios o cochería",
                "El encuadramiento se determina por la actividad real del establecimiento",
            ],
            "advertencias": [
                "La escala agosto 2026 es provisoria y no está habilitada para liquidación definitiva",
                "Los aportes convencionales contradictorios permanecen bloqueados",
            ],
        })
    elif es_farmacia:
        if loc in AMBITO_TERRITORIAL_414_05:
            candidatos.append({
                "cct_numero": "414/05", "nombre": "Farmacias alcanzadas por ADEF",
                "confianza": "alta",
                "motivos": [
                    "La actividad declarada es farmacia",
                    f"{localidad.strip()} integra el ámbito territorial del art. 3 del CCT 414/05",
                ],
                "advertencias": [],
            })
        elif loc:
            candidatos.append({
                "cct_numero": "659/13", "nombre": "Farmacias FATFA-COFA",
                "confianza": "media",
                "motivos": ["La actividad declarada es farmacia", "La localidad no integra el ámbito ADEF cargado"],
                "advertencias": ["Confirmar la asociación empresaria y el ámbito territorial antes de guardar"],
            })
        else:
            for numero, nombre in (("414/05", "Farmacias alcanzadas por ADEF"),
                                   ("659/13", "Farmacias FATFA-COFA")):
                candidatos.append({
                    "cct_numero": numero, "nombre": nombre, "confianza": "baja",
                    "motivos": ["La actividad declarada es farmacia"],
                    "advertencias": ["Falta la localidad para separar ADEF de FATFA"],
                })
    else:
        for regla in REGLAS:
            coincide_actividad = _contiene(act, regla.palabras_actividad)
            coincide_tarea = _contiene(tar, regla.palabras_tarea)
            if not coincide_actividad:
                continue
            motivos = [f"La actividad coincide con {regla.nombre}"]
            if coincide_tarea:
                motivos.append("La tarea informada es compatible con esa actividad")
            candidatos.append({
                "cct_numero": regla.cct, "nombre": regla.nombre,
                "confianza": "alta" if coincide_tarea else "media",
                "motivos": motivos,
                "advertencias": ([] if coincide_tarea else
                                  ["Revisar la categoría según las tareas efectivamente realizadas"]),
            })

    if not candidatos and act:
        faltantes.append("No existe una coincidencia segura con los convenios instalados")

    return {
        "candidatos": candidatos,
        "faltantes": faltantes,
        "puede_aplicar_automaticamente": len(candidatos) == 1
        and candidatos[0]["confianza"] == "alta" and not faltantes,
        "criterio": "Actividad real + ámbito territorial + tarea efectiva",
        "provincia_informada": prov,
    }
