-- Esquema de base de datos para el sistema multiagéntico
-- de asignación y despacho de cuadrillas.
-- Hidrandina S.A. - Zonal Trujillo, Unidad de Negocios Trujillo.
-- Diseñado para Supabase / PostgreSQL.

-- =====================================================
-- Tabla 1: avisos de falta de suministro
-- =====================================================

CREATE TABLE IF NOT EXISTS avisos (
    id SERIAL PRIMARY KEY,
    codigo_aviso TEXT UNIQUE NOT NULL,
    zona TEXT NOT NULL,
    direccion TEXT NOT NULL,

    tipo_falla TEXT NOT NULL
        CHECK (
            tipo_falla IN (
                'baja_tension',
                'media_tension',
                'transformador'
            )
        ),

    prioridad TEXT NOT NULL
        CHECK (
            prioridad IN (
                'alta',
                'normal'
            )
        ),

    descripcion TEXT NOT NULL DEFAULT '',

    estado TEXT NOT NULL DEFAULT 'en_cola'
        CHECK (
            estado IN (
                'en_cola',
                'en_proceso',
                'asignado',
                'cancelado'
            )
        ),

    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_avisos_zona_estado
    ON avisos (zona, estado);


-- =====================================================
-- Tabla 2: cuadrillas técnicas con disponibilidad
-- =====================================================

CREATE TABLE IF NOT EXISTS cuadrillas (
    id SERIAL PRIMARY KEY,
    codigo_cuadrilla TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    zona_base TEXT NOT NULL,

    especialidad TEXT NOT NULL
        CHECK (
            especialidad IN (
                'baja_tension',
                'media_tension',
                'transformador'
            )
        ),

    estado TEXT NOT NULL DEFAULT 'libre'
        CHECK (
            estado IN (
                'libre',
                'ocupada',
                'fuera_servicio'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_cuadrillas_esp_estado
    ON cuadrillas (especialidad, estado);


-- =====================================================
-- Tabla 3: órdenes de trabajo emitidas
-- =====================================================

CREATE TABLE IF NOT EXISTS ordenes (
    id SERIAL PRIMARY KEY,
    codigo_orden TEXT UNIQUE NOT NULL,

    codigo_aviso TEXT NOT NULL
        REFERENCES avisos(codigo_aviso),

    codigo_cuadrilla TEXT NOT NULL
        REFERENCES cuadrillas(codigo_cuadrilla),

    prioridad TEXT NOT NULL
        CHECK (
            prioridad IN (
                'alta',
                'normal'
            )
        ),

    fecha_emision TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ordenes_aviso
    ON ordenes (codigo_aviso);