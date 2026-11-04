
"""Prueba de ejecución del grafo para evidenciar el monitoreo en LangSmith."""

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


def test_ejecucion_grafo_para_monitoreo_langsmith():
    """Comprueba el flujo exitoso del grafo con servicios simulados."""

    aviso_mock = Aviso(
        codigo_aviso="AV-LS-001",
        zona="Porvenir Norte",
        direccion="Dirección de prueba",
        tipo_falla=TipoFalla.BAJA_TENSION,
        prioridad=Prioridad.NORMAL,
        descripcion="Prueba de monitoreo LangSmith",
        estado=EstadoAviso.EN_COLA,
    )

    cuadrilla_mock = Cuadrilla(
        codigo_cuadrilla="CU-LS-001",
        nombre="Cuadrilla de prueba LangSmith",
        zona_base="Porvenir Norte",
        especialidad=TipoFalla.BAJA_TENSION,
        estado=EstadoCuadrilla.LIBRE,
    )

    orden_mock = Orden(
        codigo_orden="OT-2026-9998",
        codigo_aviso="AV-LS-001",
        codigo_cuadrilla="CU-LS-001",
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
                "codigo_aviso": "AV-LS-001",
                "zona": "Porvenir Norte",
                "tipo_falla": "baja_tension",
                "prioridad": "normal",
            }
        )

    assert (
        resultado["resultado"]
        == ResultadoDespacho.CUADRILLA_DESPACHADA
    )
    assert resultado["orden_emitida"].codigo_orden == "OT-2026-9998"
    assert resultado["notificacion_enviada"] is True

    print("Caso de prueba: AV-LS-001")
    print(f"Resultado: {resultado['resultado']}")
    print(f"Orden: {resultado['orden_emitida'].codigo_orden}")
    print(f"Notificación enviada: {resultado['notificacion_enviada']}")
    print("Prueba de monitoreo completada correctamente.")
