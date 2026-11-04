"""Orquestador del ciclo de despacho.

Responsabilidad principal: coordinar la ejecuciÃƒÂ³n del proceso de despacho,
controlar las decisiones del flujo y dirigir el caso segÃƒÂºn su resultado.

Verifica la vigencia del aviso antes de emitir la orden, coordina la notificaciÃƒÂ³n
a la cuadrilla y gestiona las rutas alternativas cuando el caso ha sido cancelado o no existe una cuadrilla disponible.

El razonamiento especializado se encuentra en los subagentes. El orquestador se encarga de mantener el cumplimiento de
las reglas del proceso, como verificar la vigencia del caso antes de emitir una orden.
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
    se aborta la emisiÃƒÂ³n.
    """

    codigo = estado["codigo_aviso"]
    estado_actual = verificar_estado_aviso(codigo)

    vigente = estado_actual not in ("cancelado", None)

    if not vigente:
        logger.warning(
            "Caso %s no vigente (estado=%s), se abortarÃƒÂ¡ emisiÃƒÂ³n",
            codigo,
            estado_actual,
        )

    return {
        **estado,
        "caso_sigue_vigente": vigente,
    }


def notificar_cuadrilla(estado: EstadoDespacho) -> EstadoDespacho:
    """Notifica digitalmente la orden a la cuadrilla asignada.

    Esta actividad representa el envÃƒÂ­o digital de la orden.
    No representa la confirmaciÃƒÂ³n de recepciÃƒÂ³n de la cuadrilla,
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
        f"Caso {estado['codigo_aviso']} cerrado por cancelaciÃƒÂ³n del cliente. "
        "No se emitiÃƒÂ³ orden. No se consumiÃƒÂ³ recurso de cuadrilla."
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
    """Routing condicional: Ã‚Â¿hay cuadrilla recomendada?"""

    if estado.get("cuadrilla_recomendada") is None:
        return "sin_cuadrilla"

    return "verificar_vigencia"


def ruta_tras_verificacion(
    estado: EstadoDespacho,
) -> str:
    """Routing condicional: Ã‚Â¿el caso sigue vigente?"""

    if estado.get("caso_sigue_vigente"):
        return "emitir"

    return "cancelado"
