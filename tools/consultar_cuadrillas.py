"""Herramienta: consultar cuadrillas disponibles por especialidad.

Usada por el CoordinadorDeCuadrillas para encontrar candidatas que
puedan atender un tipo de falla específico.
"""

from __future__ import annotations

import logging

from models.dominio import Cuadrilla
from tools.supabase_client import get_client

logger = logging.getLogger(__name__)


def consultar_cuadrillas(
    especialidad: str,
    estado: str = "libre",
) -> list[Cuadrilla]:
    """Devuelve las cuadrillas que coinciden con la especialidad y están disponibles.

    Args:
        especialidad: tipo de falla que la cuadrilla puede atender.
        estado: filtro por estado. Default "libre".

    Returns:
        Lista de Cuadrilla (puede estar vacía).
    """

    client = get_client()

    response = (
        client.table("cuadrillas")
        .select("*")
        .eq("especialidad", especialidad)
        .eq("estado", estado)
        .execute()
    )

    data = response.data

    if not isinstance(data, list):
        raise TypeError(
            "Supabase devolvió un formato inesperado al consultar cuadrillas."
        )

    cuadrillas: list[Cuadrilla] = []

    for row in data:
        if not isinstance(row, dict):
            raise TypeError(
                "Supabase devolvió una fila de cuadrilla "
                "con formato inesperado."
            )

        cuadrillas.append(
            Cuadrilla.desde_dict(row)
        )

    logger.info(
        "consultar_cuadrillas especialidad=%s estado=%s -> %d resultados",
        especialidad,
        estado,
        len(cuadrillas),
    )

    return cuadrillas