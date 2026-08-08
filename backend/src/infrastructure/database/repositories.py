"""Repositorios concretos (implementan los puertos del dominio con el ORM).

El filtrado por tenant lo enforcea RLS a nivel de PostgreSQL: la sesión ya trae
``app.current_tenant`` seteado, así que estas consultas no repiten el filtro
(defensa en profundidad: además se podría filtrar en app).
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.parametros import (
    Amparo as AmparoDom,
    AmparoSet,
    EscalaSalarial as EscalaDom,
    ParametroLegal as ParamDom,
    ParametroSet,
)
from domain.payroll_engine.config import CctConfig
from domain.value_objects.dinero import Dinero

from . import models as m


# --------------------------------------------------------------------------- #
# Auth (tablas scopeadas en la capa de aplicación)
# --------------------------------------------------------------------------- #
class UsuarioRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def por_email(self, email: str) -> Optional[m.Usuario]:
        r = await self.s.execute(select(m.Usuario).where(m.Usuario.email == email.lower()))
        return r.scalar_one_or_none()
