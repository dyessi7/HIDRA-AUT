"""Herramienta: registrar una orden de trabajo en la base.

Usada por el EmisorDeOrden al final del ciclo de despacho.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime

from models.dominio import Orden, Prioridad
from tools.supabase_client import get_client

logger = logging.getLogger(__name__)


def _generar_codigo_orden() -> str:
    """Genera un identificador único con formato OT-YYYY-NNNN."""

    anio = datetime.now().year
    sufijo = random.randint(1, 9999)

    return f"OT-{anio}-{sufijo:04d}"


def registrar_orden(
    codigo_aviso: str,
    codigo_cuadrilla: str,
    prioridad: str,
    max_reintentos: int = 3,
) -> Orden:
    """Inserta una nueva orden en la tabla ordenes.

    Genera un codigo_orden único y reintenta si colisiona.

    Args:
        codigo_aviso: referencia al aviso.
        codigo_cuadrilla: referencia a la cuadrilla asignada.
        prioridad: "alta" o "normal".
        max_reintentos: cantidad máxima de intentos de inserción.

    Returns:
        La Orden recién creada.

    Raises:
        RuntimeError: si no se logra registrar una orden válida.
        TypeError: si Supabase devuelve una estructura inesperada.
    """

    client = get_client()
    prioridad_enum = Prioridad(prioridad)

    for intento in range(max_reintentos):
        codigo_orden = _generar_codigo_orden()

        try:
            response = (
                client.table("ordenes")
                .insert(
                    {
                        "codigo_orden": codigo_orden,
                        "codigo_aviso": codigo_aviso,
                        "codigo_cuadrilla": codigo_cuadrilla,
                        "prioridad": prioridad_enum.value,
                    }
                )
                .execute()
            )

            data = response.data

            if not isinstance(data, list) or not data:
                raise TypeError(
                    "Supabase no devolvió la orden registrada."
                )

            row = data[0]

            if not isinstance(row, dict):
                raise TypeError(
                    "Supabase devolvió una orden con formato inesperado."
                )

            orden = Orden.desde_dict(row)

            logger.info(
                "registrar_orden exitoso codigo=%s aviso=%s cuadrilla=%s",
                orden.codigo_orden,
                orden.codigo_aviso,
                orden.codigo_cuadrilla,
            )

            return orden

        except Exception as exc:
            if (
                "duplicate key" in str(exc).lower()
                and intento < max_reintentos - 1
            ):
                logger.warning(
                    "registrar_orden colisión codigo=%s intento=%d, reintentando",
                    codigo_orden,
                    intento + 1,
                )
                continue

            raise

    raise RuntimeError(
        "No se pudo generar codigo_orden único "
        f"tras {max_reintentos} intentos"
    )
