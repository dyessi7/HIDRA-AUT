"""Subagente EmisorDeOrden.

Responsabilidad única: generar código único de orden y persistir el registro
en la tabla ordenes. Es la única entrada autorizada a esa tabla desde el
sistema multiagéntico.

Reemplaza la tarea "Emitir y anotar la orden" del AS-IS, eliminando la doble
anotación (sistema + cuaderno) que generaba inconsistencias en cambio de turno.
"""
from __future__ import annotations

import logging

from graph.state import EstadoDespacho
from models.dominio import ResultadoDespacho
from tools.registrar_orden import registrar_orden

logger = logging.getLogger(__name__)


def ejecutar(estado: EstadoDespacho) -> EstadoDespacho:
    """Nodo LangGraph del EmisorDeOrden."""
    cuadrilla = estado.get("cuadrilla_recomendada")
    if cuadrilla is None:
        raise RuntimeError(
            "EmisorDeOrden invocado sin cuadrilla recomendada. "
            "Esto es un bug del flujo: el orquestador debe verificar antes."
        )

    orden = registrar_orden(
        codigo_aviso=estado["codigo_aviso"],
        codigo_cuadrilla=cuadrilla.codigo_cuadrilla,
        prioridad=estado["prioridad"],
    )

    mensaje = (
        f"Orden {orden.codigo_orden} emitida. "
        f"Aviso {orden.codigo_aviso} asignado a cuadrilla {orden.codigo_cuadrilla} "
        f"con prioridad {orden.prioridad.value}."
    )
    logger.info("EmisorDeOrden -> %s", mensaje)

    return {
        **estado,
        "orden_emitida": orden,
        "resultado": ResultadoDespacho.ORDEN_EMITIDA,
        "mensaje_final": mensaje,
    }
