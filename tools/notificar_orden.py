"""Herramienta: notificar una orden a la cuadrilla asignada.

En el prototipo académico representa el envío por un canal digital.
No simula la confirmación de recepción de la cuadrilla, ya que esa
actividad queda fuera del alcance actual.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def notificar_orden(
    codigo_orden: str,
    codigo_cuadrilla: str,
) -> bool:
    """Registra el envío digital de una orden a una cuadrilla.

    Args:
        codigo_orden: identificador de la orden emitida.
        codigo_cuadrilla: cuadrilla destinataria.

    Returns:
        True cuando la notificación fue procesada correctamente.
    """

    logger.info(
        "notificar_orden -> orden=%s enviada a cuadrilla=%s",
        codigo_orden,
        codigo_cuadrilla,
    )

    return True