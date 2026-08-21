from pathlib import Path

from ui_page import HTML


RAIZ = Path(__file__).parents[2]


def test_migracion_distingue_farmacia_interna_de_actividad_farmacia():
    sql = (RAIZ / "migrations" / "013_ambito_actividad_convenios.sql").read_text()
    assert "farmacia interna es un sector" in sql
    assert "no se asigna automáticamente" in sql
    assert "'122/75','AMBITO_ACTIVIDAD'" in sql
    assert "'414/05','AMBITO_ACTIVIDAD'" in sql
    assert "'659/13','AMBITO_ACTIVIDAD'" in sql


def test_ui_agrupa_dos_convenios_de_farmacia_y_separa_sanidad():
    assert "'414/05':{actividad:'Farmacia comercial / comunitaria'" in HTML
    assert "'659/13':{actividad:'Farmacia comercial / comunitaria'" in HTML
    assert "'122/75':{actividad:'Clínica, sanatorio o geriátrico con internación'" in HTML


def test_boton_actualizar_informa_estado_y_hora():
    assert 'id="btnActualizarGestor"' in HTML
    assert "Actualizando…" in HTML
    assert "gestorActualizado" in HTML
