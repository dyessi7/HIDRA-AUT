"""Dataclasses de dominio.

Representan las entidades del proceso de despacho tal como viven en la base
de datos. Los agentes y herramientas trabajan con estas estructuras, no con
dicts sueltos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TipoFalla(str, Enum):
    BAJA_TENSION = "baja_tension"
    MEDIA_TENSION = "media_tension"
    TRANSFORMADOR = "transformador"


class Prioridad(str, Enum):
    ALTA = "alta"
    NORMAL = "normal"


class EstadoAviso(str, Enum):
    EN_COLA = "en_cola"
    EN_PROCESO = "en_proceso"
    ASIGNADO = "asignado"
    CANCELADO = "cancelado"


class EstadoCuadrilla(str, Enum):
    LIBRE = "libre"
    OCUPADA = "ocupada"
    FUERA_SERVICIO = "fuera_servicio"


@dataclass
class Aviso:
    codigo_aviso: str
    zona: str
    direccion: str
    tipo_falla: TipoFalla
    prioridad: Prioridad
    descripcion: str
    estado: EstadoAviso
    fecha_registro: datetime | None = None

    @classmethod
    def desde_dict(cls, data: dict) -> Aviso:
        """Construye desde la fila cruda que devuelve Supabase."""
        return cls(
            codigo_aviso=data["codigo_aviso"],
            zona=data["zona"],
            direccion=data["direccion"],
            tipo_falla=TipoFalla(data["tipo_falla"]),
            prioridad=Prioridad(data["prioridad"]),
            descripcion=data.get("descripcion", ""),
            estado=EstadoAviso(data["estado"]),
            fecha_registro=(
                datetime.fromisoformat(data["fecha_registro"])
                if data.get("fecha_registro")
                else None
            ),
        )


@dataclass
class Cuadrilla:
    codigo_cuadrilla: str
    nombre: str
    zona_base: str
    especialidad: TipoFalla
    estado: EstadoCuadrilla

    @classmethod
    def desde_dict(cls, data: dict) -> Cuadrilla:
        """Construye desde la fila cruda que devuelve Supabase."""
        return cls(
            codigo_cuadrilla=data["codigo_cuadrilla"],
            nombre=data["nombre"],
            zona_base=data["zona_base"],
            especialidad=TipoFalla(data["especialidad"]),
            estado=EstadoCuadrilla(data["estado"]),
        )


@dataclass
class Orden:
    codigo_orden: str
    codigo_aviso: str
    codigo_cuadrilla: str
    prioridad: Prioridad
    fecha_emision: datetime | None = None

    @classmethod
    def desde_dict(cls, data: dict) -> Orden:
        """Construye desde la fila cruda que devuelve Supabase."""
        return cls(
            codigo_orden=data["codigo_orden"],
            codigo_aviso=data["codigo_aviso"],
            codigo_cuadrilla=data["codigo_cuadrilla"],
            prioridad=Prioridad(data["prioridad"]),
            fecha_emision=(
                datetime.fromisoformat(data["fecha_emision"])
                if data.get("fecha_emision")
                else None
            ),
        )


class ResultadoDespacho(str, Enum):
    """Estados relevantes del ciclo de despacho."""

    # Estado intermedio: la orden ya fue creada y persistida.
    ORDEN_EMITIDA = "orden_emitida"

    # Terminaciones del flujo.
    CUADRILLA_DESPACHADA = "cuadrilla_despachada"
    SIN_CUADRILLA = "sin_cuadrilla"
    CASO_CANCELADO = "caso_cancelado"