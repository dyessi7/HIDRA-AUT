# Sistema multiagéntico de despacho de cuadrillas — Hidrandina

Proyecto académico que implementa el subproceso TO-BE `Asignación y despacho de cuadrilla` para la atención de incidencias eléctricas de Hidrandina S.A. — Zonal Trujillo.

La solución utiliza:

- Python
- LangGraph
- LangChain
- Anthropic Claude
- Supabase
- pytest
- Ruff
- mypy

El BPMN ubicado en `bpmn/to_be_asignacion_despacho.bpmn` es la fuente de verdad funcional del proceso.

---

## Flujo implementado

```text
START
  ↓
AnalistaDeFalla
  ↓
CoordinadorDeCuadrillas
  ↓
¿Hay cuadrilla disponible?
  ├── No → SIN_CUADRILLA → END
  │
  └── Sí
       ↓
   Verificar vigencia
       ↓
   ¿Sigue vigente?
       ├── No → CASO_CANCELADO → END
       │
       └── Sí
            ↓
        EmisorDeOrden
            ↓
        ORDEN_EMITIDA
            ↓
        Notificar cuadrilla
            ↓
        CUADRILLA_DESPACHADA
            ↓
           END
```

`ORDEN_EMITIDA` es un estado intermedio.

El resultado exitoso final del subproceso es:

`CUADRILLA_DESPACHADA`

---

## Agentes

### AnalistaDeFalla

Consulta los avisos relacionados con la zona e identifica el tipo de falla predominante.

Puede utilizar un LLM con salida estructurada y dispone de un fallback determinista en caso de error.

### CoordinadorDeCuadrillas

Consulta las cuadrillas disponibles y aplica obligatoriamente:

```text
especialidad = tipo_falla
estado = libre
```

El LLM puede recomendar una cuadrilla únicamente dentro del conjunto previamente válido.

También dispone de fallback determinista.

### EmisorDeOrden

Agente determinista encargado de registrar la orden de trabajo después de verificar que el aviso continúa vigente.

### Orquestador

Implementado con LangGraph.

Controla la secuencia del proceso, los gateways, la verificación de vigencia, las rutas excepcionales y la notificación final.

---

## Requisitos

- Python 3.11 o superior.
- Proyecto de Supabase.
- API key de Anthropic opcional para utilizar el LLM real.

En Windows se recomienda utilizar PowerShell.

---

## Instalación

Desde la carpeta raíz del proyecto:

```powershell
python -m venv .venv
```

Activar el entorno:

```powershell
.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

---

## Variables de entorno

Copiar:

```text
.env.example
```

como:

```text
.env
```

y configurar:

```env
SUPABASE_URL=
SUPABASE_KEY=
ANTHROPIC_API_KEY=
```

No subir credenciales reales al repositorio.

`ANTHROPIC_API_KEY` es opcional para pruebas y desarrollo.

Si no está configurada, el proyecto puede utilizar `FakeListChatModel` y los agentes cuentan con lógica determinista de respaldo.

Una ejecución con el modelo fake no representa una inferencia real de Anthropic.

---

## Base de datos

Los archivos de base de datos se encuentran en:

```text
db/schema.sql
db/seed.sql
```

Si se utiliza un proyecto Supabase nuevo, ejecutar primero `schema.sql` y luego `seed.sql` desde el SQL Editor de Supabase.

El sistema trabaja con información de:

- avisos;
- cuadrillas;
- órdenes.

El sistema no modifica directamente una cuadrilla a estado `ocupada`.

---

## Ejecutar un caso

Ejemplo:

```powershell
python -m graph.workflow --caso AV-2026-0001 --zona "Porvenir Norte" --tipo baja_tension --prioridad normal
```

Parámetros disponibles:

```text
--caso
--zona
--tipo
--prioridad
```

Ejemplo para una falla de transformador:

```powershell
python -m graph.workflow --caso AV-2026-0002 --zona "Trujillo Centro" --tipo transformador --prioridad alta
```

---

## Pruebas

Ejecutar toda la suite:

```powershell
python -m pytest tests -v
```

Estado actual de referencia:

```text
14 passed
```

La suite incluye:

```text
tests/test_analista.py
tests/test_coordinador.py
tests/test_integracion.py
tests/test_golden_cases.py
tests/golden_cases.json
```

Los 5 golden cases verifican:

1. Caso normal con cuadrilla disponible.
2. Incidente prioritario de transformador.
3. Ausencia de cuadrilla.
4. Aviso cancelado antes de emitir la orden.
5. Selección entre varias cuadrillas válidas.

---

## Calidad de código

Ruff:

```powershell
python -m ruff check .
```

Resultado de referencia:

```text
All checks passed!
```

mypy:

```powershell
python -m mypy agents tools graph models
```

Resultado de referencia:

```text
Success: no issues found in 17 source files
```

---

## Estructura principal

```text
hidrandina_despacho_multiagente/
├── CLAUDE.md
├── README.md
├── Makefile
├── requirements.txt
├── .env.example
├── bpmn/
├── db/
├── agents/
├── tools/
├── graph/
├── models/
├── tests/
└── docs/
```

Los componentes principales son:

- `bpmn/` — BPMN TO-BE y fuente de verdad funcional.
- `agents/` — agentes especializados y orquestador.
- `tools/` — consultas, persistencia y notificación.
- `graph/` — estado, LLM y workflow LangGraph.
- `models/` — modelos del dominio.
- `db/` — esquema y datos iniciales de Supabase.
- `tests/` — pruebas unitarias, integración y golden cases.
- `docs/` — documentación de arquitectura.
- `CLAUDE.md` — invariantes y reglas técnicas del proyecto.

---

## Notificación

Después de emitir una orden se ejecuta:

`notificar_orden`

En el prototipo actual esta herramienta representa el envío digital mediante logging.

No existe todavía integración real con WhatsApp, SMS, correo electrónico u otro proveedor externo.

---

## Fuera del alcance

Actualmente no se implementa:

- ejecución física de la atención en campo;
- confirmación de recepción por parte de la cuadrilla;
- cambio automático de la cuadrilla a `ocupada`;
- cierre técnico posterior de la incidencia;
- mensajería externa real;
- Human-in-the-Loop interactivo mediante `interrupt()` / `resume()`.

---

## Documentación adicional

Arquitectura detallada:

`docs/arquitectura.md`

Reglas e invariantes del proyecto:

`CLAUDE.md`

---

## Contexto académico

Proyecto académico desarrollado para el curso **Automatización Inteligente de Procesos — UPAO**.

Los datos utilizados son simulados y el proyecto no representa una integración oficial con los sistemas productivos de Hidrandina S.A.