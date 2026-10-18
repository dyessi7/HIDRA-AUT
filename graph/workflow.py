"""Grafo LangGraph del ciclo de despacho multiagéntico.

Topología del grafo (ver bpmn/to_be_asignacion_despacho.bpmn):

    START
      |
      v
  analizar_falla  (AnalistaDeFalla)
      |
      v
  coordinar_cuadrilla  (CoordinadorDeCuadrillas)
      |
      v
  [¿hay cuadrilla?]
      |-- no --> sin_cuadrilla --> END
      |
      |-- sí --> verificar_vigencia
                      |
                      v
                 [¿sigue vigente?]
                      |-- no --> caso_cancelado --> END
                      |
                      |-- sí --> emitir_orden
                                      |
                                      v
                              notificar_cuadrilla
                                      |
                                      v
                                     END
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any, cast

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents import (
    analista_falla,
    coordinador_cuadrillas,
    emisor_orden,
    orquestador,
)
from graph.state import EstadoDespacho

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


def construir_grafo() -> CompiledStateGraph:
    """Construye y compila el grafo del flujo de despacho."""

    grafo = StateGraph(EstadoDespacho)

    # Nodos principales
    grafo.add_node(
        "analizar_falla",
        cast(Any, analista_falla.ejecutar),
    )

    grafo.add_node(
        "coordinar_cuadrilla",
        cast(Any, coordinador_cuadrillas.ejecutar),
    )

    grafo.add_node(
        "verificar_vigencia",
        cast(Any, orquestador.verificar_vigencia),
    )

    grafo.add_node(
        "emitir_orden",
        cast(Any, emisor_orden.ejecutar),
    )

    grafo.add_node(
        "notificar_cuadrilla",
        cast(Any, orquestador.notificar_cuadrilla),
    )

    # Nodos terminales alternativos
    grafo.add_node(
        "sin_cuadrilla",
        cast(Any, orquestador.resolver_sin_cuadrilla),
    )

    grafo.add_node(
        "caso_cancelado",
        cast(Any, orquestador.resolver_caso_cancelado),
    )

    # Inicio del flujo
    grafo.add_edge(
        START,
        "analizar_falla",
    )

    grafo.add_edge(
        "analizar_falla",
        "coordinar_cuadrilla",
    )

    # Decisión: ¿hay cuadrilla disponible?
    grafo.add_conditional_edges(
        "coordinar_cuadrilla",
        orquestador.ruta_tras_coordinacion,
        {
            "sin_cuadrilla": "sin_cuadrilla",
            "verificar_vigencia": "verificar_vigencia",
        },
    )

    # Decisión: ¿el aviso sigue vigente?
    grafo.add_conditional_edges(
        "verificar_vigencia",
        orquestador.ruta_tras_verificacion,
        {
            "emitir": "emitir_orden",
            "cancelado": "caso_cancelado",
        },
    )

    # Flujo exitoso
    grafo.add_edge(
        "emitir_orden",
        "notificar_cuadrilla",
    )

    grafo.add_edge(
        "notificar_cuadrilla",
        END,
    )

    # Flujos alternativos
    grafo.add_edge(
        "sin_cuadrilla",
        END,
    )

    grafo.add_edge(
        "caso_cancelado",
        END,
    )

    return grafo.compile()


def ejecutar_caso(
    codigo_aviso: str,
    zona: str,
    tipo_falla: str,
    prioridad: str,
) -> dict:
    """Ejecuta el grafo completo para un caso dado."""

    workflow = construir_grafo()

    estado_inicial: EstadoDespacho = {
        "codigo_aviso": codigo_aviso,
        "zona": zona,
        "tipo_falla": tipo_falla,
        "prioridad": prioridad,
    }

    logger.info("=" * 60)

    logger.info(
        "INICIO caso %s zona=%s tipo=%s prioridad=%s",
        codigo_aviso,
        zona,
        tipo_falla,
        prioridad,
    )

    logger.info("=" * 60)

    resultado = workflow.invoke(estado_inicial)

    logger.info("=" * 60)

    logger.info(
        "FIN caso %s -> %s",
        codigo_aviso,
        resultado.get("resultado"),
    )

    logger.info(
        "Mensaje: %s",
        resultado.get("mensaje_final"),
    )

    logger.info(
        "Notificación enviada: %s",
        resultado.get("notificacion_enviada"),
    )

    logger.info("=" * 60)

    return resultado


def main() -> int:
    """Punto de entrada para ejecutar un caso desde terminal."""

    parser = argparse.ArgumentParser(
        description="Ejecuta un caso de despacho",
    )

    parser.add_argument(
        "--caso",
        default="AV-2026-0001",
        help="Código del aviso",
    )

    parser.add_argument(
        "--zona",
        default="Porvenir Norte",
        help="Zona del caso",
    )

    parser.add_argument(
        "--tipo",
        default="baja_tension",
        help="Tipo de falla",
    )

    parser.add_argument(
        "--prioridad",
        default="normal",
        help="Prioridad del caso",
    )

    args = parser.parse_args()

    ejecutar_caso(
        codigo_aviso=args.caso,
        zona=args.zona,
        tipo_falla=args.tipo,
        prioridad=args.prioridad,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())