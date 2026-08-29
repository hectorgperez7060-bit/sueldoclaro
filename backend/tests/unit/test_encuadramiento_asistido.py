from domain.entities.encuadramiento_asistido import sugerir_encuadramiento


def test_farmacia_merlo_es_adef_y_no_comercio():
    r = sugerir_encuadramiento(
        "Farmacia comercial", "Merlo", "Atención de mostrador y recetas", "Buenos Aires"
    )
    assert [c["cct_numero"] for c in r["candidatos"]] == ["414/05"]
    assert r["candidatos"][0]["confianza"] == "alta"
    assert r["puede_aplicar_automaticamente"] is True


def test_farmacia_sin_localidad_no_adivina_entre_adef_y_fatfa():
    r = sugerir_encuadramiento("Farmacia", "", "Cajera")
    assert {c["cct_numero"] for c in r["candidatos"]} == {"414/05", "659/13"}
    assert "Localidad del lugar de trabajo" in r["faltantes"]
    assert r["puede_aplicar_automaticamente"] is False


def test_clinica_con_tarea_compatible_propone_sanidad():
    r = sugerir_encuadramiento("Clínica con internación", "Morón", "Enfermera")
    assert r["candidatos"][0]["cct_numero"] == "122/75"
    assert r["candidatos"][0]["confianza"] == "alta"


def test_actividad_desconocida_no_fuerza_convenio():
    r = sugerir_encuadramiento("Consultoría tecnológica", "CABA", "Programación")
    assert r["candidatos"] == []
    assert any("coincidencia segura" in x for x in r["faltantes"])
