"""Test unitario del AnalistaDeFalla."""

from __future__ import annotations

from unittest.mock import patch

from agents.analista_falla import AnalisisFallaLLM, ejecutar
from models.dominio import Aviso, EstadoAviso, Prioridad, TipoFalla


def _hacer_aviso(
    codigo: str,
    tipo: TipoFalla = TipoFalla.BAJA_TENSION,
) -> Aviso:
    return Aviso(
        codigo_aviso=codigo,
        zona="Porvenir Norte",
        direccion="Mz A Lt 1",
        tipo_falla=tipo,
        prioridad=Prioridad.NORMAL,
        descripcion="",
        estado=EstadoAviso.EN_COLA,
    )


def test_analista_agrupa_avisos_misma_zona():
    """Dado 3 avisos de baja tensión, el analista reporta ese tipo."""

    avisos_mock = [
        _hacer_aviso("AV-1"),
        _hacer_aviso("AV-2"),
        _hacer_aviso("AV-3"),
    ]

    estado_entrada = {
        "codigo_aviso": "AV-1",
        "zona": "Porvenir Norte",
        "tipo_falla": "baja_tension",
        "prioridad": "normal",
    }

    with (
        patch(
            "agents.analista_falla.consultar_avisos",
            return_value=avisos_mock,
        ),
        patch(
            "agents.analista_falla._analizar_con_llm",
            return_value=None,
        ),
    ):
        resultado = ejecutar(estado_entrada)

    assert len(resultado["avisos_agrupados"]) == 3
    assert resultado["tipo_falla_predominante"] == "baja_tension"
    assert "Porvenir Norte" in resultado["resumen_analisis"]


def test_analista_zona_sin_avisos_usa_tipo_inicial():
    """Si la consulta devuelve vacío, se mantiene el tipo inicial."""

    estado_entrada = {
        "codigo_aviso": "AV-X",
        "zona": "Zona Fantasma",
        "tipo_falla": "transformador",
        "prioridad": "alta",
    }

    with (
        patch(
            "agents.analista_falla.consultar_avisos",
            return_value=[],
        ),
        patch(
            "agents.analista_falla._analizar_con_llm",
            return_value=None,
        ),
    ):
        resultado = ejecutar(estado_entrada)

    assert resultado["avisos_agrupados"] == []
    assert resultado["tipo_falla_predominante"] == "transformador"


def test_analista_usa_resultado_llm_estructurado():
    """Si el LLM devuelve una respuesta válida, el analista la utiliza."""

    avisos_mock = [
        _hacer_aviso("AV-1"),
        _hacer_aviso("AV-2"),
        _hacer_aviso("AV-3"),
    ]

    respuesta_llm = AnalisisFallaLLM(
        tipo_falla_predominante=TipoFalla.BAJA_TENSION,
        avisos_relacionados=["AV-1", "AV-2"],
        justificacion=(
            "Los dos avisos presentan características compatibles "
            "y corresponden a ubicaciones relacionadas."
        ),
    )

    estado_entrada = {
        "codigo_aviso": "AV-1",
        "zona": "Porvenir Norte",
        "tipo_falla": "baja_tension",
        "prioridad": "normal",
    }

    with (
        patch(
            "agents.analista_falla.consultar_avisos",
            return_value=avisos_mock,
        ),
        patch(
            "agents.analista_falla._analizar_con_llm",
            return_value=respuesta_llm,
        ),
    ):
        resultado = ejecutar(estado_entrada)

    assert resultado["tipo_falla_predominante"] == "baja_tension"
    assert len(resultado["avisos_agrupados"]) == 2
    assert "Análisis LLM" in resultado["resumen_analisis"]