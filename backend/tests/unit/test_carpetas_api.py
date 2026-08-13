from main import create_app


def test_api_expone_solo_lectura_de_carpetas():
    paths = create_app().openapi()["paths"]
    assert set(paths["/carpetas-mensuales"]) == {"get"}
    assert set(paths["/carpetas-mensuales/{carpeta_id}"]) == {"get"}
