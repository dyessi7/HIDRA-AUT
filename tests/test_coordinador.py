"""Test unitario del CoordinadorDeCuadrillas."""

from __future__ import annotations

from unittest.mock import patch

from agents.coordinador_cuadrillas import (
    RecomendacionCuadrillaLLM,
    ejecutar,
)
from models.dominio import Cuadrilla, EstadoCuadrilla, TipoFalla


def _hacer_cuadrilla(
    codigo: str,
    zona: str,
    esp: TipoFalla = TipoFalla.BAJA_TENSION,
) -> Cuadrilla:
    return Cuadrilla(
        codigo_cuadrilla=codigo,
        nombre=f"Cuadrilla {codigo}",
        zona_base=zona,
        especialidad=esp,
        estado=EstadoCuadrilla.LIBRE,
    )


def test_coordinador_prioriza_misma_zona():
    """Sin LLM, el fallback prioriza la cuadrilla de la misma zona."""

    candidatas = [
        _hacer_cuadrilla("CU-X", "Trujillo Centro"),
        _hacer_cuadrilla("CU-01", "Porvenir Norte"),
        _hacer_cuadrilla("CU-Y", "Huanchaco"),
    ]

    estado_entrada = {
        "codigo_aviso": "AV-1",
        "zona": "Porvenir Norte",
        "tipo_falla": "baja_tension",
        "tipo_falla_predominante": "baja_tension",
        "prioridad": "normal",
    }

    with (
        patch(
            "agents.coordinador_cuadrillas.consultar_cuadrillas",
            return_value=candidatas,
        ),
        patch(
            "agents.coordinador_cuadrillas._recomendar_con_llm",
            return_value=None,
        ),
    ):
        resultado = ejecutar(estado_entrada)

    assert resultado["cuadrilla_recomendada"] is not None
    assert (
        resultado["cuadrilla_recomendada"].codigo_cuadrilla
        == "CU-01"
    )
    assert "fallback determinístico" in resultado["razon_recomendacion"]


def test_coordinador_sin_cuadrillas_devuelve_none():
    """Si no hay cuadrillas disponibles, devuelve None."""

    estado_entrada = {
        "codigo_aviso": "AV-1",
        "zona": "Porvenir Norte",
        "tipo_falla": "transformador",
        "tipo_falla_predominante": "transformador",
        "prioridad": "alta",
    }

    with patch(
        "agents.coordinador_cuadrillas.consultar_cuadrillas",
        return_value=[],
    ):
        resultado = ejecutar(estado_entrada)

    assert resultado["cuadrilla_recomendada"] is None
    assert "Sin cuadrilla" in resultado["razon_recomendacion"]


def test_coordinador_usa_recomendacion_llm_estructurada():
    """Si el LLM recomienda una candidata válida, se utiliza."""

    candidatas = [
        _hacer_cuadrilla("CU-01", "Porvenir Norte"),
        _hacer_cuadrilla("CU-02", "Porvenir Norte"),
    ]

    recomendacion_llm = RecomendacionCuadrillaLLM(
        codigo_cuadrilla="CU-02",
        justificacion=(
            "La cuadrilla cumple la especialidad requerida "
            "y tiene la misma zona base del caso."
        ),
    )

    estado_entrada = {
        "codigo_aviso": "AV-1",
        "zona": "Porvenir Norte",
        "tipo_falla": "baja_tension",
        "tipo_falla_predominante": "baja_tension",
        "prioridad": "normal",
    }

    with (
        patch(
            "agents.coordinador_cuadrillas.consultar_cuadrillas",
            return_value=candidatas,
        ),
        patch(
            "agents.coordinador_cuadrillas._recomendar_con_llm",
            return_value=recomendacion_llm,
        ),
    ):
        resultado = ejecutar(estado_entrada)

    assert resultado["cuadrilla_recomendada"] is not None
    assert (
        resultado["cuadrilla_recomendada"].codigo_cuadrilla
        == "CU-02"
    )
    assert "Análisis LLM" in resultado["razon_recomendacion"]