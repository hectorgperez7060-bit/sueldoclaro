"""Hashing de contraseñas con Argon2id."""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()  # Argon2id por defecto


def hash_password(plano: str) -> str:
    return _ph.hash(plano)


def verify_password(plano: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plano)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(hashed: str) -> bool:
    return _ph.check_needs_rehash(hashed)
