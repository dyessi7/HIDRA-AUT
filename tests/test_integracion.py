"""Test de integración: grafo completo con mocks de las herramientas.

Verifica que el flujo end-to-end funciona sin tocar Supabase real.
"""

from __future__ import annotations

from unittest.mock import patch

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


def test_flujo_completo_orden_emitida_y_notificada():
    """Un caso feliz debería emitir y notificar correctamente la orden."""

    aviso_mock = Aviso(
        codigo_aviso="AV-TEST-001",
        zona="Porvenir Norte",
        direccion="Mz A Lt 1",
        tipo_falla=TipoFalla.BAJA_TENSION,
        prioridad=Prioridad.NORMAL,
        descripcion="",
        estado=EstadoAviso.EN_COLA,
    )

    cuadrilla_mock = Cuadrilla(
        codigo_cuadrilla="CU-TEST",
        nombre="Cuadrilla Test",
        zona_base="Porvenir Norte",
        especialidad=TipoFalla.BAJA_TENSION,
        estado=EstadoCuadrilla.LIBRE,
    )

    orden_mock = Orden(
        codigo_orden="OT-2026-9999",
        codigo_aviso="AV-TEST-001",
        codigo_cuadrilla="CU-TEST",
        prioridad=Prioridad.NORMAL,
    )

    with (
        patch(
            "agents.analista_falla.consultar_avisos",
            return_value=[aviso_mock],
        ),
        patch(
            "agents.analista_falla._analizar_con_llm",
            return_value=None,
        ),
        patch(
            "agents.coordinador_cuadrillas.consultar_cuadrillas",
            return_value=[cuadrilla_mock],
        ),
        patch(
            "agents.coordinador_cuadrillas._recomendar_con_llm",
            return_value=None,
        ),
        patch(
            "agents.orquestador.verificar_estado_aviso",
            return_value="en_cola",
        ),
        patch(
            "agents.emisor_orden.registrar_orden",
            return_value=orden_mock,
        ),
        patch(
            "agents.orquestador.notificar_orden",
            return_value=True,
        ),
    ):
        workflow = construir_grafo()

        resultado = workflow.invoke(
            {
                "codigo_aviso": "AV-TEST-001",
                "zona": "Porvenir Norte",
                "tipo_falla": "baja_tension",
                "prioridad": "normal",
            }
        )

    assert (
        resultado["resultado"]
        == ResultadoDespacho.CUADRILLA_DESPACHADA
    )
    assert resultado["orden_emitida"].codigo_orden == "OT-2026-9999"
    assert resultado["notificacion_enviada"] is True
    assert "notificada correctamente" in resultado["mensaje_final"].lower()


def test_flujo_sin_cuadrilla_termina_en_alerta():
    """Si no hay cuadrilla disponible, el flujo termina con alerta al supervisor."""

    with (
        patch(
            "agents.analista_falla.consultar_avisos",
            return_value=[],
        ),
        patch(
            "agents.analista_falla._analizar_con_llm",
            return_value=None,
        ),
        patch(
            "agents.coordinador_cuadrillas.consultar_cuadrillas",
            return_value=[],
        ),
    ):
        workflow = construir_grafo()

        resultado = workflow.invoke(
            {
                "codigo_aviso": "AV-TEST-002",
                "zona": "Zona X",
                "tipo_falla": "transformador",
                "prioridad": "alta",
            }
        )

    assert resultado["resultado"] == ResultadoDespacho.SIN_CUADRILLA
    assert "contingencia" in resultado["mensaje_final"].lower()


def test_flujo_caso_cancelado_no_emite_orden():
    """Si el aviso fue cancelado, no se emite ni notifica ninguna orden."""

    aviso_mock = Aviso(
        codigo_aviso="AV-TEST-003",
        zona="Porvenir Norte",
        direccion="Mz B Lt 10",
        tipo_falla=TipoFalla.BAJA_TENSION,
        prioridad=Prioridad.NORMAL,
        descripcion="Aviso posteriormente cancelado",
        estado=EstadoAviso.EN_COLA,
    )

    cuadrilla_mock = Cuadrilla(
        codigo_cuadrilla="CU-TEST",
        nombre="Cuadrilla Test",
        zona_base="Porvenir Norte",
        especialidad=TipoFalla.BAJA_TENSION,
        estado=EstadoCuadrilla.LIBRE,
    )

    with (
        patch(
            "agents.analista_falla.consultar_avisos",
            return_value=[aviso_mock],
        ),
        patch(
            "agents.analista_falla._analizar_con_llm",
            return_value=None,
        ),
        patch(
            "agents.coordinador_cuadrillas.consultar_cuadrillas",
            return_value=[cuadrilla_mock],
        ),
        patch(
            "agents.coordinador_cuadrillas._recomendar_con_llm",
            return_value=None,
        ),
        patch(
            "agents.orquestador.verificar_estado_aviso",
            return_value="cancelado",
        ),
        patch(
            "agents.emisor_orden.registrar_orden"
        ) as mock_registrar_orden,
        patch(
            "agents.orquestador.notificar_orden"
        ) as mock_notificar_orden,
    ):
        workflow = construir_grafo()

        resultado = workflow.invoke(
            {
                "codigo_aviso": "AV-TEST-003",
                "zona": "Porvenir Norte",
                "tipo_falla": "baja_tension",
                "prioridad": "normal",
            }
        )

    assert resultado["resultado"] == ResultadoDespacho.CASO_CANCELADO
    assert resultado.get("orden_emitida") is None
    assert resultado.get("notificacion_enviada") is not True

    mock_registrar_orden.assert_not_called()
    mock_notificar_orden.assert_not_called()

    assert "cancelación" in resultado["mensaje_final"].lower()