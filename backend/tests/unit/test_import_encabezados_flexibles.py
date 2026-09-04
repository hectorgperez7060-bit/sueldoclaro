"""El importador tiene que entender la planilla como la trae el estudio.

Cada estudio arma el Excel a su manera: tildes, "CUIL/CUIT", fechas en
dd/mm/aaaa, apellido y nombre en una sola celda, importes con signo peso. Antes
cualquiera de esas variantes rechazaba el archivo entero.
"""
from __future__ import annotations

import io
from decimal import Decimal

from openpyxl import Workbook

from infrastructure.excel.importer import parsear, parsear_con_mapeo
from infrastructure.excel.mapeo_columnas import detectar_mapeo, normalizar, partir_nombre_completo


CUIL_1 = "20123456786"
CUIL_2 = "27234567891"


def _libro(filas: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    for fila in filas:
        ws.append(fila)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_normalizar_saca_tildes_y_puntuacion():
    assert normalizar("Categoría") == "categoria"
    assert normalizar("CUIL / CUIT") == "cuil cuit"
    assert normalizar("  Fecha de Ingreso  ") == "fecha de ingreso"


def test_encabezados_con_tildes_y_sinonimos_se_reconocen():
    filas = [
        ["Apellido", "Nombre", "CUIL/CUIT", "Fecha de ingreso", "Convenio", "Categoría"],
        ["Pérez", "Juan", CUIL_1, "01/07/2021", "130/75", "Administrativo A"],
    ]
    validos, errores = parsear(_libro(filas))
    assert errores == []
    assert len(validos) == 1
    assert validos[0]["apellido"] == "Pérez"
    assert validos[0]["nombre"] == "Juan"
    assert str(validos[0]["fecha_ingreso"]) == "2021-07-01"


def test_apellido_y_nombre_en_una_sola_celda():
    filas = [
        ["Apellido y Nombre", "CUIL", "Ingreso", "Gremio", "Puesto"],
        ["Pérez, Juan Carlos", CUIL_1, "01/07/2021", "130/75", "Administrativo A"],
    ]
    validos, errores, mapeo = parsear_con_mapeo(_libro(filas))
    assert errores == []
    assert validos[0]["apellido"] == "Pérez"
    assert validos[0]["nombre"] == "Juan Carlos"
    assert mapeo["nombre_completo_partido"] is True


def test_partir_nombre_completo_respeta_el_orden_del_encabezado():
    assert partir_nombre_completo("Pérez, Juan") == ("Pérez", "Juan")
    assert partir_nombre_completo("Pérez Juan", "Apellido y Nombre") == ("Pérez", "Juan")
    assert partir_nombre_completo("Juan Pérez", "Nombre y Apellido") == ("Pérez", "Juan")


def test_fechas_en_formato_argentino_y_importes_con_peso():
    filas = [
        ["Apellido", "Nombre", "CUIL", "Fecha de alta", "CCT", "Categoria", "Sueldo"],
        ["Pérez", "Juan", CUIL_1, "01/07/2021", "130/75", "Administrativo A", "$ 1.234.567,89"],
    ]
    validos, errores = parsear(_libro(filas))
    assert errores == []
    assert str(validos[0]["remuneracion_pactada"]) == "1234567.89"


def test_cuil_cargado_como_numero_no_se_rechaza():
    filas = [
        ["Apellido", "Nombre", "CUIL", "Fecha de ingreso", "Convenio", "Categoría"],
        ["Pérez", "Juan", float(CUIL_1), "01/07/2021", "130/75", "Administrativo A"],
    ]
    validos, errores = parsear(_libro(filas))
    assert errores == []
    assert validos[0]["cuil"] == CUIL_1


def test_titulo_arriba_del_encabezado_no_rompe_la_lectura():
    filas = [
        ["NÓMINA AL 31/08/2026 - LA EMPRESA S.A."],
        [],
        ["Apellido", "Nombre", "CUIL", "Fecha de ingreso", "Convenio", "Categoría"],
        ["Pérez", "Juan", CUIL_1, "01/07/2021", "130/75", "Administrativo A"],
    ]
    validos, errores, mapeo = parsear_con_mapeo(_libro(filas))
    assert errores == []
    assert mapeo["fila_encabezado"] == 3
    assert len(validos) == 1


def test_filas_vacias_al_pie_se_ignoran():
    filas = [
        ["Apellido", "Nombre", "CUIL", "Fecha de ingreso", "Convenio", "Categoría"],
        ["Pérez", "Juan", CUIL_1, "01/07/2021", "130/75", "Administrativo A"],
        [None, None, None, None, None, None],
        ["", "", "", "", "", ""],
    ]
    validos, errores = parsear(_libro(filas))
    assert errores == []
    assert len(validos) == 1


def test_columna_faltante_explica_como_titularla():
    filas = [
        ["Apellido", "Nombre", "CUIL", "Fecha de ingreso", "Convenio"],
        ["Pérez", "Juan", CUIL_1, "01/07/2021", "130/75"],
    ]
    validos, errores = parsear(_libro(filas))
    assert validos == []
    texto = " ".join(errores[0]["errores"])
    assert "categoria" in texto
    assert "puesto" in texto or "cargo" in texto  # sugiere títulos alternativos


def test_columnas_desconocidas_se_informan_pero_no_frenan():
    filas = [
        ["Apellido", "Nombre", "CUIL", "Fecha de ingreso", "Convenio", "Categoría", "Obra social"],
        ["Pérez", "Juan", CUIL_1, "01/07/2021", "130/75", "Administrativo A", "OSECAC"],
    ]
    validos, errores, mapeo = parsear_con_mapeo(_libro(filas))
    assert errores == []
    assert len(validos) == 1
    assert "Obra social" in mapeo["ignoradas"]


def test_afiliacion_acepta_las_formas_habituales():
    filas = [
        ["Apellido", "Nombre", "CUIL", "Fecha de ingreso", "Convenio", "Categoría", "Afiliado"],
        ["Pérez", "Juan", CUIL_1, "01/07/2021", "130/75", "Administrativo A", "NO"],
        ["López", "Ana", CUIL_2, "15/03/2022", "130/75", "Vendedor B", "X"],
    ]
    validos, errores = parsear(_libro(filas))
    assert errores == []
    assert validos[0]["afiliado_sindicato"] is False
    assert validos[1]["afiliado_sindicato"] is True


def test_encabezado_canonico_sigue_funcionando():
    """La plantilla que descarga la app no puede dejar de andar."""
    filas = [
        ["nombre", "apellido", "cuil", "fecha_ingreso", "cct_numero", "categoria"],
        ["Juan", "Pérez", CUIL_1, "2021-07-01", "130/75", "Administrativo A"],
    ]
    validos, errores = parsear(_libro(filas))
    assert errores == []
    assert validos[0]["nombre"] == "Juan"
    assert validos[0]["apellido"] == "Pérez"


def test_mapeo_explica_cada_columna_interpretada():
    encabezado = ["Apellido", "Nombre", "CUIL/CUIT", "Fecha de ingreso", "Convenio", "Categoría"]
    indices, interpretacion, ignoradas = detectar_mapeo(encabezado)
    assert set(indices) >= {"apellido", "nombre", "cuil", "fecha_ingreso", "cct_numero", "categoria"}
    assert ignoradas == []
    por_columna = {i["columna_archivo"]: i["interpretada_como"] for i in interpretacion}
    assert por_columna["CUIL/CUIT"] == "cuil"
    assert por_columna["Convenio"] == "cct_numero"


def test_sin_columna_de_horas_el_empleado_queda_a_jornada_completa():
    """Lo habitual es la jornada completa: no hay que saber las horas del convenio."""
    filas = [
        ["Apellido", "Nombre", "CUIL", "Fecha de ingreso", "Convenio", "Categoría"],
        ["Arancibia", "Oscar", CUIL_1, "01/07/2021", "76/75", "Oficial Especializado"],
    ]
    validos, errores = parsear(_libro(filas))
    assert errores == []
    assert validos[0]["proporcion_jornada"] == 1


def test_horas_por_encima_de_dos_tercios_se_avisan_al_importar():
    """Mejor rechazar la fila explicando, que crear un legajo que falla al liquidar."""
    filas = [
        ["Apellido", "Nombre", "CUIL", "Fecha de ingreso", "Convenio", "Categoría", "Horas semanales"],
        ["Arancibia", "Oscar", CUIL_1, "01/07/2021", "76/75", "Oficial Especializado", 40],
    ]
    validos, errores = parsear(_libro(filas))
    assert validos == []
    texto = " ".join(errores[0]["errores"])
    assert "92 ter" in texto
    assert "jornada completa" in texto


def test_jornada_parcial_genuina_se_importa_prorrateada():
    """Media jornada está por debajo de 2/3: se prorratea y no se avisa nada."""
    filas = [
        ["Apellido", "Nombre", "CUIL", "Fecha de ingreso", "Convenio", "Categoría", "Horas semanales"],
        ["Rodríguez", "Valeria", CUIL_2, "01/07/2021", "130/75", "Administrativo A", 24],
    ]
    validos, errores = parsear(_libro(filas), horas_por_cct={"130/75": 48})
    assert errores == []
    assert validos[0]["proporcion_jornada"] == Decimal("0.5")
