"""Orquestador del ciclo de despacho.

No es un agente con razonamiento propio: es la lógica de coordinación que
decide a quién llamar cuando, verifica vigencia del caso antes de emitir,
notifica la orden a la cuadrilla y rutea el resultado a cuadrilla despachada,
caso cerrado o alerta al supervisor.

El razonamiento vive en los subagentes. El orquestador asegura que las
invariantes del CLAUDE.md se cumplan (vigencia, disponibilidad, no emisión
sin verificación).
"""

from __future__ import annotations

import logging

from graph.state import EstadoDespacho
from models.dominio import ResultadoDespacho
from tools.consultar_avisos import verificar_estado_aviso
from tools.notificar_orden import notificar_orden

logger = logging.getLogger(__name__)


def verificar_vigencia(estado: EstadoDespacho) -> EstadoDespacho:
    """Consulta el estado actual del aviso antes de emitir orden.

    Si fue cancelado entre la entrada a la cola y este momento,
    se aborta la emisión.
    """

    codigo = estado["codigo_aviso"]
    estado_actual = verificar_estado_aviso(codigo)

    vigente = estado_actual not in ("cancelado", None)

    if not vigente:
        logger.warning(
            "Caso %s no vigente (estado=%s), se abortará emisión",
            codigo,
            estado_actual,
        )

    return {
        **estado,
        "caso_sigue_vigente": vigente,
    }


def notificar_cuadrilla(estado: EstadoDespacho) -> EstadoDespacho:
    """Notifica digitalmente la orden a la cuadrilla asignada.

    Esta actividad representa el envío digital de la orden.
    No representa la confirmación de recepción de la cuadrilla,
    ya que esa actividad queda fuera del alcance actual.
    """

    orden = estado.get("orden_emitida")

    if orden is None:
        raise RuntimeError(
            "No se puede notificar a la cuadrilla sin una orden emitida."
        )

    enviado = notificar_orden(
        codigo_orden=orden.codigo_orden,
        codigo_cuadrilla=orden.codigo_cuadrilla,
    )

    if not enviado:
        raise RuntimeError(
            f"No se pudo notificar la orden {orden.codigo_orden} "
            f"a la cuadrilla {orden.codigo_cuadrilla}."
        )

    mensaje = (
        f"Orden {orden.codigo_orden} notificada correctamente "
        f"a la cuadrilla {orden.codigo_cuadrilla}."
    )

    logger.info(
        "Orquestador -> %s",
        mensaje,
    )

    return {
        **estado,
        "notificacion_enviada": True,
        "resultado": ResultadoDespacho.CUADRILLA_DESPACHADA,
        "mensaje_final": mensaje,
    }

def resolver_sin_cuadrilla(
    estado: EstadoDespacho,
) -> EstadoDespacho:
    """Resultado terminal cuando no hay cuadrilla disponible."""

    mensaje = (
        f"Caso {estado['codigo_aviso']} pendiente por contingencia manual. "
        f"Motivo: "
        f"{estado.get('razon_recomendacion', 'sin disponibilidad')}. "
        "Supervisor CCO debe activar plan de contingencia."
    )

    logger.warning(
        "Orquestador -> %s",
        mensaje,
    )

    return {
        **estado,
        "resultado": ResultadoDespacho.SIN_CUADRILLA,
        "mensaje_final": mensaje,
    }


def resolver_caso_cancelado(
    estado: EstadoDespacho,
) -> EstadoDespacho:
    """Resultado terminal cuando el caso fue cancelado antes de emitir."""

    mensaje = (
        f"Caso {estado['codigo_aviso']} cerrado por cancelación del cliente. "
        "No se emitió orden. No se consumió recurso de cuadrilla."
    )

    logger.info(
        "Orquestador -> %s",
        mensaje,
    )

    return {
        **estado,
        "resultado": ResultadoDespacho.CASO_CANCELADO,
        "mensaje_final": mensaje,
    }


def ruta_tras_coordinacion(
    estado: EstadoDespacho,
) -> str:
    """Routing condicional: ¿hay cuadrilla recomendada?"""

    if estado.get("cuadrilla_recomendada") is None:
        return "sin_cuadrilla"

    return "verificar_vigencia"


def ruta_tras_verificacion(
    estado: EstadoDespacho,
) -> str:
    """Routing condicional: ¿el caso sigue vigente?"""

    if estado.get("caso_sigue_vigente"):
        return "emitir"

    return "cancelado"
