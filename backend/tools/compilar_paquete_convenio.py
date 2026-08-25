#!/usr/bin/env python3
"""Uso: python backend/tools/compilar_paquete_convenio.py paquete.json salida.sql"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from infrastructure.normativa.compilador_paquete import cargar_paquete, compilar_paquete  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: compilar_paquete_convenio.py MANIFIESTO.json SALIDA.sql", file=sys.stderr)
        return 2
    try:
        sql, diagnostico = compilar_paquete(cargar_paquete(sys.argv[1]))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    Path(sys.argv[2]).write_text(sql, encoding="utf-8")
    print(json.dumps(diagnostico.resumen, ensure_ascii=False, indent=2))
    print(f"SQL generado: {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
