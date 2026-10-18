"""Subagente AnalistaDeFalla.

Responsabilidad única: consultar los avisos abiertos en la zona del caso,
agruparlos por similitud e identificar el tipo de falla predominante.

Usa un LLM para analizar el contexto de los avisos, pero mantiene una
estrategia determinística segura como fallback.
"""

from __future__ import annotations

import logging

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from graph.llm import get_llm
from graph.state import EstadoDespacho
from models.dominio import Aviso, TipoFalla
from tools.consultar_avisos import consultar_avisos

logger = logging.getLogger(__name__)


class AnalisisFallaLLM(BaseModel):
    """Contrato estructurado de salida del LLM."""

    tipo_falla_predominante: TipoFalla
    avisos_relacionados: list[str]
    justificacion: str


def _tipo_predominante_deterministico(
    avisos: list[Aviso],
    tipo_inicial: str,
) -> str:
    """Fallback seguro cuando el LLM no está disponible o falla."""

    if not avisos:
        return tipo_inicial

    conteo_tipos: dict[str, int] = {}

    for aviso in avisos:
        tipo = aviso.tipo_falla.value
        conteo_tipos[tipo] = conteo_tipos.get(tipo, 0) + 1

    return max(
    conteo_tipos,
    key=lambda tipo: conteo_tipos[tipo],
)


def _analizar_con_llm(
    avisos: list[Aviso],
    zona: str,
    codigo_actual: str,
) -> AnalisisFallaLLM | None:
    """Analiza los avisos mediante el LLM con salida estructurada."""

    if not avisos:
        return None

    parser = PydanticOutputParser(pydantic_object=AnalisisFallaLLM)

    detalle_avisos = "\n".join(
        (
            f"- codigo={aviso.codigo_aviso}; "
            f"direccion={aviso.direccion}; "
            f"tipo_falla={aviso.tipo_falla.value}; "
            f"descripcion={aviso.descripcion}"
        )
        for aviso in avisos
    )

    prompt = f"""
Eres el AnalistaDeFalla de un sistema de despacho de incidencias eléctricas.

Analiza los avisos abiertos de la zona "{zona}" y determina cuáles podrían
corresponder a una misma falla que el caso disparador "{codigo_actual}".

Reglas:
- Usa únicamente los avisos proporcionados.
- No inventes códigos de aviso.
- No inventes tipos de falla.
- El tipo de falla solo puede ser:
  baja_tension, media_tension o transformador.
- Considera dirección, descripción y tipo de falla.
- Devuelve solamente la estructura solicitada.

Avisos disponibles:
{detalle_avisos}

{parser.get_format_instructions()}
"""

    try:
        respuesta = get_llm().invoke(prompt)

        contenido = respuesta.content
        if not isinstance(contenido, str):
            contenido = str(contenido)

        resultado = parser.parse(contenido)

        codigos_validos = {aviso.codigo_aviso for aviso in avisos}

        if any(
            codigo not in codigos_validos
            for codigo in resultado.avisos_relacionados
        ):
            raise ValueError(
                "El LLM devolvió códigos de aviso que no estaban "
                "entre las opciones consultadas."
            )

        logger.info(
            "AnalistaDeFalla LLM -> tipo=%s relacionados=%s",
            resultado.tipo_falla_predominante.value,
            resultado.avisos_relacionados,
        )

        return resultado

    except Exception as exc:  # noqa: BLE001 - fallback ante cualquier fallo del LLM
        logger.warning(
            "AnalistaDeFalla: fallo del análisis LLM; "
            "se utilizará fallback determinístico. Motivo: %s",
            exc,
        )
        return None


def ejecutar(estado: EstadoDespacho) -> EstadoDespacho:
    """Nodo LangGraph del AnalistaDeFalla."""

    zona = estado["zona"]
    codigo_actual = estado["codigo_aviso"]

    avisos = consultar_avisos(zona=zona, estado="en_cola")

    tipo_fallback = _tipo_predominante_deterministico(
        avisos,
        estado.get("tipo_falla", "baja_tension"),
    )

    analisis_llm = _analizar_con_llm(
        avisos=avisos,
        zona=zona,
        codigo_actual=codigo_actual,
    )

    if analisis_llm is not None:
        tipo_predominante = analisis_llm.tipo_falla_predominante.value

        codigos_relacionados = set(analisis_llm.avisos_relacionados)

        avisos_agrupados = [
            aviso
            for aviso in avisos
            if aviso.codigo_aviso in codigos_relacionados
        ]

        # Si el modelo no agrupó ninguno, conservamos los consultados
        # como fallback seguro.
        if not avisos_agrupados:
            avisos_agrupados = avisos

        resumen = (
            f"Zona {zona}: {len(avisos_agrupados)} avisos relacionados. "
            f"Tipo predominante: {tipo_predominante}. "
            f"Análisis LLM: {analisis_llm.justificacion}"
        )

    else:
        tipo_predominante = tipo_fallback
        avisos_agrupados = avisos

        resumen = (
            f"Zona {zona}: {len(avisos)} avisos en cola. "
            f"Tipo predominante: {tipo_predominante}. "
            f"Caso disparador: {codigo_actual}. "
            "Resultado obtenido mediante fallback determinístico."
        )

    logger.info("AnalistaDeFalla -> %s", resumen)

    return {
        **estado,
        "avisos_agrupados": avisos_agrupados,
        "tipo_falla_predominante": tipo_predominante,
        "resumen_analisis": resumen,
    }