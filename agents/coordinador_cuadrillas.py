"""Subagente CoordinadorDeCuadrillas.

Responsabilidad única: consultar las cuadrillas disponibles que cumplen
la especialidad requerida y recomendar la mejor candidata.

La herramienta aplica los filtros obligatorios de especialidad y estado.
El LLM razona únicamente entre candidatas válidas. Si el modelo falla,
se utiliza un ranking determinístico seguro.
"""

from __future__ import annotations

import logging

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from graph.llm import get_llm
from graph.state import EstadoDespacho
from models.dominio import Cuadrilla
from tools.consultar_cuadrillas import consultar_cuadrillas

logger = logging.getLogger(__name__)


class RecomendacionCuadrillaLLM(BaseModel):
    """Contrato estructurado de salida del LLM."""

    codigo_cuadrilla: str
    justificacion: str


def _rankear(
    candidatas: list[Cuadrilla],
    zona_caso: str,
) -> list[Cuadrilla]:
    """Fallback determinístico: prioriza la misma zona base."""

    misma_zona = [
        cuadrilla
        for cuadrilla in candidatas
        if cuadrilla.zona_base == zona_caso
    ]

    otras = [
        cuadrilla
        for cuadrilla in candidatas
        if cuadrilla.zona_base != zona_caso
    ]

    return misma_zona + otras



def _recomendar_con_llm(
    candidatas: list[Cuadrilla],
    zona: str,
    especialidad: str,
    prioridad: str,
) -> RecomendacionCuadrillaLLM | None:
    """Recomienda una cuadrilla mediante LCEL con salida estructurada."""

    if not candidatas:
        return None

    parser = PydanticOutputParser(
        pydantic_object=RecomendacionCuadrillaLLM
    )

    detalle_candidatas = "\n".join(
        (
            f"- codigo={cuadrilla.codigo_cuadrilla}; "
            f"nombre={cuadrilla.nombre}; "
            f"zona_base={cuadrilla.zona_base}; "
            f"especialidad={cuadrilla.especialidad.value}; "
            f"estado={cuadrilla.estado.value}"
        )
        for cuadrilla in candidatas
    )

    prompt = ChatPromptTemplate.from_template(
        """
Eres el CoordinadorDeCuadrillas de un sistema de despacho de
incidencias eléctricas.

Debes recomendar UNA cuadrilla entre las candidatas proporcionadas.

Contexto del caso:
- zona: {zona}
- especialidad requerida: {especialidad}
- prioridad: {prioridad}

Reglas obligatorias:
- Solo puedes elegir una cuadrilla de la lista proporcionada.
- No inventes códigos de cuadrilla.
- Todas las candidatas ya cumplen especialidad y disponibilidad.
- Prioriza una cuadrilla cuya zona base coincida con la zona del caso.
- Si no existe una de la misma zona, selecciona una de las candidatas
  disponibles y justifica brevemente la elección.
- Devuelve solamente la estructura solicitada.

Candidatas válidas:
{detalle_candidatas}

{formato}
"""
    )

    chain = prompt | get_llm() | parser

    try:
        resultado = chain.invoke(
            {
                "zona": zona,
                "especialidad": especialidad,
                "prioridad": prioridad,
                "detalle_candidatas": detalle_candidatas,
                "formato": parser.get_format_instructions(),
            }
        )

        codigos_validos = {
            cuadrilla.codigo_cuadrilla
            for cuadrilla in candidatas
        }

        if resultado.codigo_cuadrilla not in codigos_validos:
            raise ValueError(
                "El LLM recomendó una cuadrilla que no estaba "
                "entre las candidatas válidas."
            )

        logger.info(
            "CoordinadorDeCuadrillas LLM -> cuadrilla=%s",
            resultado.codigo_cuadrilla,
        )

        return resultado

    except Exception as exc:  # noqa: BLE001 - fallback ante cualquier fallo del LLM
        logger.warning(
            "CoordinadorDeCuadrillas: fallo del análisis LLM; "
            "se utilizará fallback determinístico. Motivo: %s",
            exc,
        )
        return None


def ejecutar(estado: EstadoDespacho) -> EstadoDespacho:
    """Nodo LangGraph del CoordinadorDeCuadrillas."""

    especialidad = estado.get(
        "tipo_falla_predominante",
        estado["tipo_falla"],
    )

    zona = estado["zona"]
    prioridad = estado["prioridad"]

    candidatas = consultar_cuadrillas(
        especialidad=especialidad,
        estado="libre",
    )

    rankeadas = _rankear(
        candidatas,
        zona_caso=zona,
    )

    if not candidatas:
        elegida = None
        razon = (
            f"Sin cuadrilla disponible con especialidad "
            f"{especialidad} en estado libre."
        )

        logger.warning(
            "CoordinadorDeCuadrillas -> %s",
            razon,
        )

    else:
        recomendacion_llm = _recomendar_con_llm(
            candidatas=candidatas,
            zona=zona,
            especialidad=especialidad,
            prioridad=prioridad,
        )

        if recomendacion_llm is not None:
            elegida = next(
                cuadrilla
                for cuadrilla in candidatas
                if cuadrilla.codigo_cuadrilla
                == recomendacion_llm.codigo_cuadrilla
            )

            razon = (
                f"Cuadrilla {elegida.codigo_cuadrilla} "
                f"({elegida.nombre}). "
                f"Análisis LLM: "
                f"{recomendacion_llm.justificacion}"
            )

        else:
            elegida = rankeadas[0]

            razon = (
                f"Cuadrilla {elegida.codigo_cuadrilla} "
                f"({elegida.nombre}) - especialidad "
                f"{elegida.especialidad.value}, zona base "
                f"{elegida.zona_base}"
                + (
                    " (misma zona del caso)"
                    if elegida.zona_base == zona
                    else " (zona diferente)"
                )
                + ". Resultado obtenido mediante "
                "fallback determinístico."
            )

        logger.info(
            "CoordinadorDeCuadrillas -> %s",
            razon,
        )

    return {
        **estado,
        "cuadrillas_candidatas": rankeadas,
        "cuadrilla_recomendada": elegida,
        "razon_recomendacion": razon,
    }