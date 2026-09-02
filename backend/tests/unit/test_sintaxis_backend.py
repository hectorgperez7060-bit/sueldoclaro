"""Red de seguridad mínima para que Vercel nunca reciba Python ilegible."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULOS = sorted((ROOT / "backend" / "src").rglob("*.py")) + [ROOT / "api" / "index.py"]


def test_todos_los_modulos_de_produccion_compilan():
    assert len(MODULOS) >= 71, "la guarda dejó módulos de producción afuera"
    errores = []
    for ruta in MODULOS:
        fuente = ruta.read_text(encoding="utf-8")
        try:
            compile(fuente, str(ruta.relative_to(ROOT)), "exec")
        except SyntaxError as exc:
            errores.append(f"{ruta.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")
    assert errores == [], "Python inválido:\n" + "\n".join(errores)
