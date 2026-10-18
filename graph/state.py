"""Estado compartido entre los nodos del grafo LangGraph.

Cada nodo del grafo (orquestador, cada subagente) lee y escribe campos
específicos de este estado. Es la "memoria del caso" durante el ciclo.
"""

from __future__ import annotations

from typing import TypedDict

from models.dominio import Aviso, Cuadrilla, Orden, ResultadoDespacho


class EstadoDespacho(TypedDict, total=False):
    """Estado del caso durante el procesamiento multiagéntico."""

    # Entrada del caso (viene del webhook del RPA)
    codigo_aviso: str
    zona: str
    tipo_falla: str
    prioridad: str

    # Salida del AnalistaDeFalla
    avisos_agrupados: list[Aviso]
    tipo_falla_predominante: str
    resumen_analisis: str

    # Salida del CoordinadorDeCuadrillas
    cuadrillas_candidatas: list[Cuadrilla]
    cuadrilla_recomendada: Cuadrilla | None
    razon_recomendacion: str

    # Resultado de verificar vigencia
    caso_sigue_vigente: bool

    # Salida del EmisorDeOrden
    orden_emitida: Orden | None

    # Resultado de la notificación digital
    notificacion_enviada: bool

    # Resultado final del ciclo
    resultado: ResultadoDespacho
    mensaje_final: str