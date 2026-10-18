"""Cliente Supabase centralizado.

Instancia única del cliente, reutilizada por todas las herramientas que
acceden a la base. Lee credenciales de variables de entorno.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Devuelve el cliente Supabase, instanciándolo una sola vez."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL y SUPABASE_KEY deben estar definidos en .env. "
            "Copia .env.example a .env y rellena los valores."
        )

    return create_client(url, key)
