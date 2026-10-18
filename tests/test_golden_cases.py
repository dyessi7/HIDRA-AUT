"""Pruebas golden del flujo completo de despacho.

Carga los 5 casos canónicos definidos en golden_cases.json y verifica
que el comportamiento del grafo permanezca estable.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from graph.workflow import construir_grafo
from models.dominio import (
    Aviso,
    Cuadrilla,
    EstadoAviso,
    EstadoCuadrilla,
    Orden,
    Prioridad,
    ResultadoDespacho,
    TipoFalla,
)

GOLDEN_FILE = Path(__file__).parent / "golden_cases.json"


def _cargar_casos() -> list[dict]:
    """Carga los casos dorados desde el archivo JSON."""

    with GOLDEN_FILE.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        return json.load(archivo)


def _crear_aviso(data: dict) -> Aviso:
    """Convierte un aviso del JSON en objeto de dominio."""

    return Aviso(
        codigo_aviso=data["codigo_aviso"],
        zona=data["zona"],
        direccion=data["direccion"],
        tipo_falla=TipoFalla(data["tipo_falla"]),
        prioridad=Prioridad(data["prioridad"]),
        descripcion=data["descripcion"],
        estado=EstadoAviso(data["estado"]),
    )


def _crear_cuadrilla(data: dict) -> Cuadrilla:
    """Convierte una cuadrilla del JSON en objeto de dominio."""

    return Cuadrilla(
        codigo_cuadrilla=data["codigo_cuadrilla"],
        nombre=data["nombre"],
        zona_base=data["zona_base"],
        especialidad=TipoFalla(data["especialidad"]),
        estado=EstadoCuadrilla(data["estado"]),
    )


@pytest.mark.parametrize(
    "caso",
    _cargar_casos(),
    ids=lambda caso: caso["id"],
)
def test_golden_case(caso: dict):
    """Ejecuta y valida cada escenario canónico."""

    avisos = [
        _crear_aviso(data)
        for data in caso["avisos_mock"]
    ]

    cuadrillas = [
        _crear_cuadrilla(data)
        for data in caso["cuadrillas_mock"]
    ]

    entrada = caso["entrada"]
    esperado = caso["esperado"]

    def registrar_orden_mock(
        codigo_aviso: str,
        codigo_cuadrilla: str,
        prioridad: str,
    ) -> Orden:
        return Orden(
            codigo_orden=f"OT-{caso['id']}",
            codigo_aviso=codigo_aviso,
            codigo_cuadrilla=codigo_cuadrilla,
            prioridad=Prioridad(prioridad),
        )

    with (
        patch(
            "agents.analista_falla.consultar_avisos",
            return_value=avisos,
        ),
        patch(
            "agents.analista_falla._analizar_con_llm",
            return_value=None,
        ),
        patch(
            "agents.coordinador_cuadrillas.consultar_cuadrillas",
            return_value=cuadrillas,
        ),
        patch(
            "agents.coordinador_cuadrillas._recomendar_con_llm",
            return_value=None,
        ),
        patch(
            "agents.orquestador.verificar_estado_aviso",
            return_value=caso["estado_actual_aviso"],
        ),
        patch(
            "agents.emisor_orden.registrar_orden",
            side_effect=registrar_orden_mock,
        ) as mock_registrar,
        patch(
            "agents.orquestador.notificar_orden",
            return_value=True,
        ) as mock_notificar,
    ):
        workflow = construir_grafo()

        resultado = workflow.invoke(entrada)

    assert (
        resultado["resultado"].value
        == esperado["resultado"]
    )

    cuadrilla_esperada = esperado["cuadrilla"]

    if cuadrilla_esperada is not None:
        assert resultado["cuadrilla_recomendada"] is not None

        assert (
            resultado["cuadrilla_recomendada"].codigo_cuadrilla
            == cuadrilla_esperada
        )
    else:
        if esperado["resultado"] == ResultadoDespacho.SIN_CUADRILLA.value:
            assert resultado.get("cuadrilla_recomendada") is None

    assert (
        resultado.get("notificacion_enviada", False)
        == esperado["notificacion_enviada"]
    )

    if (
        esperado["resultado"]
        == ResultadoDespacho.CUADRILLA_DESPACHADA.value
    ):
        mock_registrar.assert_called_once()
        mock_notificar.assert_called_once()

    else:
        mock_registrar.assert_not_called()
        mock_notificar.assert_not_called()
