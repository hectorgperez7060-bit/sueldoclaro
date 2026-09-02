from main import create_app


def test_api_expone_solo_lectura_de_carpetas():
    paths = create_app().openapi()["paths"]
    assert set(paths["/carpetas-mensuales"]) == {"get"}
    assert set(paths["/carpetas-mensuales/{carpeta_id}"]) == {"get"}


def test_filtro_de_periodo_es_opcional_para_ver_todo_el_historial():
    operacion = create_app().openapi()["paths"]["/carpetas-mensuales"]["get"]
    periodo = next(p for p in operacion["parameters"] if p["name"] == "periodo")
    assert periodo["required"] is False
