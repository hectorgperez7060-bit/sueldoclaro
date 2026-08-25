import json
from pathlib import Path

import pytest

from domain.entities.paquete_convenio import validar_paquete
from infrastructure.normativa.compilador_paquete import compilar_paquete


ROOT = Path(__file__).resolve().parents[2]


def paquete_valido():
    return json.loads((ROOT / "normativa/PLANTILLA_PAQUETE.json").read_text(encoding="utf-8"))


def test_plantilla_compila_a_sql_transaccional_y_versionado():
    sql, diagnostico = compilar_paquete(paquete_valido())
    assert diagnostico.valido
    assert diagnostico.resumen["escalas"] == 1
    assert sql.startswith("BEGIN;")
    assert "INSERT INTO public.cct_paquete_version" in sql
    assert "hash_sha256" in sql
    assert sql.rstrip().endswith("COMMIT;")


def test_sql_es_reejecutable_sin_acumular_escalas_ni_parametros():
    datos = paquete_valido()
    datos["periodos"][0]["parametros"] = [{
        "codigo": "ADICIONAL", "valor": "2", "unidad": "%", "ambito": "empleado",
        "fuente": "Acta", "estado_fuente": "VERIFICADA", "verificado": True,
    }]
    sql, _ = compilar_paquete(datos)
    assert "DELETE FROM public.escala_salarial WHERE" in sql
    assert "DELETE FROM public.parametro_legal WHERE" in sql
    assert "ON CONFLICT (cct_numero,paquete_version)" not in sql  # conserva sintaxis con espacio
    assert "ON CONFLICT (cct_numero, paquete_version)" in sql


def test_bloquea_verificado_sin_fuente():
    datos = paquete_valido()
    datos["estructura"]["categorias"][0]["fuente"] = ""
    d = validar_paquete(datos)
    assert not d.valido
    assert any("verificada pero no tiene fuente" in e for e in d.errores)


def test_bloquea_categoria_desconocida_y_escala_duplicada():
    datos = paquete_valido()
    escala = dict(datos["periodos"][0]["escalas"][0])
    escala["categoria"] = "Inventada"
    datos["periodos"][0]["escalas"] += [escala, dict(escala)]
    d = validar_paquete(datos)
    assert any("categoría desconocida" in e for e in d.errores)
    assert any("Escala duplicada" in e for e in d.errores)


def test_bloquea_matriz_incompleta():
    datos = paquete_valido()
    datos["estructura"]["zonas"] = ["A", "B"]
    assert any("matriz declarada completa" in e for e in validar_paquete(datos).errores)


def test_motor_productivo_exige_matriz_y_pruebas():
    datos = paquete_valido()
    datos["motor"]["estado"] = "PRODUCTIVO"
    datos["periodos"][0]["matriz_completa"] = False
    d = validar_paquete(datos)
    assert any("sin pruebas de regresión" in e for e in d.errores)
    assert any("matriz salarial incompleta" in e for e in d.errores)


def test_motor_productivo_exige_escalas_habilitadas():
    datos = paquete_valido()
    datos["motor"]["estado"] = "PRODUCTIVO"
    datos["motor"]["pruebas_regresion"] = ["recibo_real_001"]
    d = validar_paquete(datos)
    assert any("escalas no habilitadas" in e for e in d.errores)


def test_motor_productivo_valido_cuando_todo_esta_verificado():
    datos = paquete_valido()
    datos["motor"]["estado"] = "PRODUCTIVO"
    datos["motor"]["pruebas_regresion"] = ["recibo_real_001"]
    datos["periodos"][0]["escalas"][0]["habilitada"] = True
    assert validar_paquete(datos).valido


def test_escapa_texto_sql_y_no_permite_inyeccion():
    datos = paquete_valido()
    datos["identidad"]["nombre"] = "O'Brien; DROP TABLE cct;--"
    sql, _ = compilar_paquete(datos)
    assert "O''Brien; DROP TABLE cct;--" in sql
    assert sql.count("DROP TABLE") == 1  # queda dentro del literal escapado


def test_compilador_rechaza_paquete_invalido():
    datos = paquete_valido()
    datos["version_paquete"] = ""
    with pytest.raises(ValueError, match="Falta version_paquete"):
        compilar_paquete(datos)


def test_migracion_registra_paquetes_sin_tenant_y_solo_lectura():
    texto = (ROOT / "migrations/026_fabrica_paquetes_convenio.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS public.cct_paquete_version" in texto
    assert "UNIQUE (cct_numero, paquete_version)" in texto
    assert "GRANT SELECT" in texto
    assert "tenant_id" not in texto
