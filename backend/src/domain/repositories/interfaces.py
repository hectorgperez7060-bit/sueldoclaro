"""Interfaces de repositorio (puertos del dominio).

Se definen en el dominio; la implementación concreta (SQLAlchemy) vive en
infraestructura (Fase 2). El dominio nunca importa el ORM.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional, Protocol

from ..entities.empleado import Empleado
from ..entities.parametros import Amparo, EscalaSalarial, ParametroLegal


class EmpleadoRepository(Protocol):
    def obtener(self, tenant_id: str, empleado_id: str) -> Optional[Empleado]: ...
    def listar(self, tenant_id: str) -> List[Empleado]: ...


class ParametroLegalRepository(Protocol):
    def vigentes_a(self, fecha: date) -> List[ParametroLegal]: ...


class EscalaSalarialRepository(Protocol):
    def vigente(self, cct_numero: str, categoria: str, fecha: date) -> Optional[EscalaSalarial]: ...


class AmparoRepository(Protocol):
    def vigentes(self, cct_numero: str, fecha: date) -> List[Amparo]: ...
