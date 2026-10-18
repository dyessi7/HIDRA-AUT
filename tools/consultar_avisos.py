"""Herramienta: consultar avisos abiertos en una zona.

Usada por el AnalistaDeFalla para agrupar reportes de la misma falla
y por el orquestador para verificar vigencia del caso.
"""

from __future__ import annotations

import logging

from models.dominio import Aviso
from tools.supabase_client import get_client

logger = logging.getLogger(__name__)


def consultar_avisos(
    zona: str,
    estado: str = "en_cola",
) -> list[Aviso]:
    """Devuelve los avisos abiertos en una zona dada.

    Args:
        zona: nombre de la zona geográfica, ej. "Porvenir Norte".
        estado: filtro por estado del aviso. Default "en_cola".

    Returns:
        Lista de Aviso (puede estar vacía).
    """

    client = get_client()

    response = (
        client.table("avisos")
        .select("*")
        .eq("zona", zona)
        .eq("estado", estado)
        .execute()
    )

    data = response.data

    if not isinstance(data, list):
        raise TypeError(
            "Supabase devolvió un formato inesperado al consultar avisos."
        )

    avisos: list[Aviso] = []

    for row in data:
        if not isinstance(row, dict):
            raise TypeError(
                "Supabase devolvió una fila de aviso con formato inesperado."
            )

        avisos.append(
            Aviso.desde_dict(row)
        )

    logger.info(
        "consultar_avisos zona=%s estado=%s -> %d resultados",
        zona,
        estado,
        len(avisos),
    )

    return avisos


def verificar_estado_aviso(
    codigo_aviso: str,
) -> str | None:
    """Devuelve el estado actual del aviso o None si no existe."""

    client = get_client()

    response = (
        client.table("avisos")
        .select("estado")
        .eq("codigo_aviso", codigo_aviso)
        .limit(1)
        .execute()
    )

    data = response.data

    if not isinstance(data, list):
        raise TypeError(
            "Supabase devolvió un formato inesperado al verificar el aviso."
        )

    if not data:
        logger.warning(
            "verificar_estado_aviso codigo=%s -> no encontrado",
            codigo_aviso,
        )
        return None

    row = data[0]

    if not isinstance(row, dict):
        raise TypeError(
            "Supabase devolvió una fila de aviso con formato inesperado."
        )

    estado = row.get("estado")

    if not isinstance(estado, str):
        raise TypeError(
            "El estado del aviso devuelto por Supabase no es válido."
        )

    logger.info(
        "verificar_estado_aviso codigo=%s -> %s",
        codigo_aviso,
        estado,
    )

    return estado