-- Datos de ejemplo para pruebas del sistema multiagéntico.
-- Hidrandina S.A. - Zonal Trujillo.
--
-- Casos principales preparados:
-- AV-2026-0001 -> despacho normal
-- AV-2026-0003 -> incidente prioritario de transformador
-- AV-2026-0004 -> sin cuadrilla disponible
-- AV-2026-0009 -> varias cuadrillas válidas, prioriza misma zona
-- AV-2026-0010 -> aviso cancelado antes de emitir la orden


-- =====================================================
-- Avisos
-- =====================================================

INSERT INTO avisos (
    codigo_aviso,
    zona,
    direccion,
    tipo_falla,
    prioridad,
    descripcion,
    estado
)
VALUES
(
    'AV-2026-0001',
    'Porvenir Norte',
    'Mz A Lt 5, Urb. La Merced',
    'baja_tension',
    'normal',
    'Sin luz en toda la cuadra desde las 20:00',
    'en_cola'
),
(
    'AV-2026-0002',
    'Porvenir Norte',
    'Mz A Lt 12, Urb. La Merced',
    'baja_tension',
    'normal',
    'Vecino reporta la misma falla que AV-2026-0001',
    'en_cola'
),
(
    'AV-2026-0003',
    'Trujillo Centro',
    'Jr. Bolivar 456',
    'transformador',
    'alta',
    'Hospital Regional sin suministro',
    'en_cola'
),
(
    'AV-2026-0004',
    'Laredo',
    'Av. Principal 890',
    'media_tension',
    'normal',
    'Sector completo sin luz',
    'en_cola'
),
(
    'AV-2026-0005',
    'Porvenir Sur',
    'Mz C Lt 3, Alto Trujillo',
    'baja_tension',
    'normal',
    'Falla intermitente en el poste',
    'en_cola'
),
(
    'AV-2026-0006',
    'Trujillo Centro',
    'Av. Espana 1234',
    'baja_tension',
    'alta',
    'Semaforo apagado en cruce con alto trafico',
    'en_cola'
),
(
    'AV-2026-0007',
    'Huanchaco',
    'Malecon Larco 200',
    'transformador',
    'normal',
    'Transformador con ruido y sin salida',
    'en_cola'
),
(
    'AV-2026-0008',
    'Laredo',
    'Av. Principal 895',
    'media_tension',
    'normal',
    'Misma falla que AV-2026-0004',
    'en_cola'
),
(
    'AV-2026-0009',
    'Porvenir Norte',
    'Mz D Lt 8, El Bosque',
    'baja_tension',
    'normal',
    'Sin luz desde la manana',
    'en_cola'
),
(
    'AV-2026-0010',
    'Trujillo Centro',
    'Jr. Pizarro 300',
    'baja_tension',
    'normal',
    'Aviso cancelado antes de emitir la orden',
    'cancelado'
)
ON CONFLICT (codigo_aviso)
DO UPDATE SET
    zona = EXCLUDED.zona,
    direccion = EXCLUDED.direccion,
    tipo_falla = EXCLUDED.tipo_falla,
    prioridad = EXCLUDED.prioridad,
    descripcion = EXCLUDED.descripcion,
    estado = EXCLUDED.estado;


-- =====================================================
-- Cuadrillas
-- =====================================================

INSERT INTO cuadrillas (
    codigo_cuadrilla,
    nombre,
    zona_base,
    especialidad,
    estado
)
VALUES
(
    'CU-01',
    'Cuadrilla Porvenir A',
    'Porvenir Norte',
    'baja_tension',
    'libre'
),
(
    'CU-02',
    'Cuadrilla Porvenir B',
    'Porvenir Sur',
    'baja_tension',
    'ocupada'
),
(
    'CU-03',
    'Cuadrilla Centro',
    'Trujillo Centro',
    'baja_tension',
    'libre'
),
(
    'CU-04',
    'Cuadrilla MT Norte',
    'Porvenir Norte',
    'media_tension',
    'fuera_servicio'
),
(
    'CU-05',
    'Cuadrilla MT Sur',
    'Laredo',
    'media_tension',
    'ocupada'
),
(
    'CU-06',
    'Cuadrilla Trafos',
    'Trujillo Centro',
    'transformador',
    'libre'
)
ON CONFLICT (codigo_cuadrilla)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    zona_base = EXCLUDED.zona_base,
    especialidad = EXCLUDED.especialidad,
    estado = EXCLUDED.estado;