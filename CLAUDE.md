# CLAUDE.md — Reglas invariantes del proyecto

**Proyecto:** Sistema multiagéntico para asignación y despacho de cuadrillas técnicas de Hidrandina S.A. (Zonal Trujillo, Unidad de Negocios Trujillo).

**Contexto:** Implementación en código del subproceso `Asignación y despacho de cuadrilla` del BPMN TO-BE. El subproceso previo (`Recepción y clasificación del aviso`, planteado como automatización/RPA en n8n) entrega la incidencia validada y clasificada como avería de red, con prioridad asignada.

El BPMN ubicado en `bpmn/to_be_asignacion_despacho.bpmn` es la fuente de verdad funcional del subproceso.

Este archivo es el contrato de desarrollo que Claude Code debe respetar en cada sesión. Las reglas aquí definidas no se reinterpretan durante la ejecución: se cumplen o, si existe un caso no contemplado, se propone primero una actualización explícita del contrato.

---

## Arquitectura

La implementación debe mantenerse alineada con `bpmn/to_be_asignacion_despacho.bpmn`.

- **Un orquestador determinista**, implementado con LangGraph, coordina el flujo completo del caso y las decisiones de enrutamiento.
- **Tres subagentes especializados**:
  - `AnalistaDeFalla`
  - `CoordinadorDeCuadrillas`
  - `EmisorDeOrden`
- **Un carril humano**, correspondiente al Supervisor CCO, atiende situaciones excepcionales que el sistema no puede resolver automáticamente, principalmente cuando no existe una cuadrilla disponible.

El flujo principal implementado es:

```text
START
  ↓
AnalistaDeFalla
  ↓
CoordinadorDeCuadrillas
  ↓
¿Hay cuadrilla disponible?
  ├── No → Contingencia manual → SIN_CUADRILLA → END
  │
  └── Sí
       ↓
   Verificar vigencia del aviso
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
        Notificar orden a cuadrilla
            ↓
        CUADRILLA_DESPACHADA
            ↓
           END
```

`ORDEN_EMITIDA` es un estado intermedio.

`CUADRILLA_DESPACHADA` es la terminación exitosa del subproceso después de que la orden haya sido notificada a la cuadrilla asignada.

La confirmación de recepción de la cuadrilla y la ejecución física del trabajo en campo están fuera del alcance actual.

---

## Invariantes del dominio

1. **Nunca emitir una orden sin verificar que el aviso sigue vigente.**

   El orquestador debe consultar el estado actual del aviso antes de invocar al `EmisorDeOrden`.

   Si el aviso está `cancelado`, el flujo termina como `CASO_CANCELADO` sin registrar ninguna orden.

2. **Nunca asignar una cuadrilla con especialidad distinta al tipo de falla.**

   El `CoordinadorDeCuadrillas` solo puede considerar cuadrillas cuya:

   ```text
   especialidad = tipo_falla
   ```

3. **Nunca asignar una cuadrilla cuyo estado sea distinto de `libre`.**

   Las cuadrillas con estado:

   ```text
   ocupada
   fuera_servicio
   ```

   quedan excluidas.

4. **Nunca permitir que el LLM seleccione una cuadrilla fuera del conjunto válido.**

   Toda recomendación del LLM debe validarse contra las cuadrillas obtenidas después de aplicar las restricciones deterministas.

5. **Nunca reutilizar un `codigo_orden`.**

   Cada orden utiliza un identificador único con formato:

   ```text
   OT-YYYY-NNNN
   ```

   Si existe una colisión, se genera un nuevo identificador y se reintenta.

6. **Nunca registrar una orden cuyo aviso no exista.**

   Debe mantenerse la relación:

   ```text
   ordenes.codigo_aviso → avisos.codigo_aviso
   ```

7. **Nunca cambiar directamente una cuadrilla a estado `ocupada`.**

   Este sistema solo consulta disponibilidad.

   El cambio de disponibilidad real corresponde a una confirmación posterior de la cuadrilla en campo y está fuera del alcance actual.

8. **Nunca considerar `ORDEN_EMITIDA` como el resultado final exitoso.**

   `ORDEN_EMITIDA` es un estado intermedio.

   El flujo exitoso termina como:

   ```text
   CUADRILLA_DESPACHADA
   ```

   después de ejecutar satisfactoriamente la notificación.

9. **Nunca simular una confirmación de recepción de la cuadrilla.**

   `notificar_orden` representa únicamente el envío digital de la orden.

10. **Nunca almacenar datos personales innecesarios del cliente en logs ni en el estado del grafo.**

    No registrar información como:

    ```text
    nombre completo
    DNI
    teléfono
    ```

11. **Nunca ejecutar código generado por el LLM.**

    Está prohibido utilizar:

    ```python
    eval()
    exec()
    ```

    o ejecutar dinámicamente instrucciones obtenidas directamente desde texto libre generado por el modelo.

---

## Responsabilidad de los agentes

### AnalistaDeFalla

El `AnalistaDeFalla` puede utilizar un LLM para:

- analizar avisos relacionados;
- identificar el tipo de falla predominante;
- seleccionar avisos relacionados;
- generar una justificación.

La salida del LLM debe ser estructurada y validada.

Los avisos relacionados propuestos por el modelo deben existir dentro del conjunto de avisos realmente consultados.

Si el LLM no está disponible, devuelve una respuesta inválida o produce una excepción, el agente utiliza una estrategia determinista de respaldo.

---

### CoordinadorDeCuadrillas

El `CoordinadorDeCuadrillas` consulta y filtra primero las cuadrillas utilizando restricciones deterministas:

```text
especialidad = tipo_falla
estado = libre
```

Solo después de aplicar estas restricciones el LLM puede recomendar una cuadrilla.

El LLM únicamente puede elegir entre las candidatas válidas.

Si el modelo:

- falla;
- devuelve una salida inválida;
- selecciona una cuadrilla inexistente;
- selecciona una cuadrilla fuera del conjunto permitido;

se utiliza la estrategia determinista de respaldo.

La estrategia determinista prioriza, cuando existe, una cuadrilla válida cuya zona base coincide con la zona del incidente.

---

### EmisorDeOrden

El `EmisorDeOrden` es determinista.

No utiliza LLM.

Solo puede ejecutarse después de:

1. seleccionar una cuadrilla válida;
2. verificar nuevamente que el aviso continúa vigente.

Su responsabilidad es registrar la orden de trabajo.

Después de registrar correctamente la orden establece:

```text
ORDEN_EMITIDA
```

como estado intermedio.

---

### Orquestador

El orquestador es determinista.

Controla:

- la secuencia del grafo;
- los gateways;
- la verificación de vigencia;
- las rutas alternativas;
- la notificación;
- el resultado final.

Las decisiones críticas del flujo no se delegan al LLM.

---

## Resultados del despacho

### `ORDEN_EMITIDA`

Estado intermedio.

La orden fue creada y persistida correctamente, pero todavía falta notificarla a la cuadrilla.

### `CUADRILLA_DESPACHADA`

Terminación exitosa.

La orden fue registrada y posteriormente notificada a la cuadrilla seleccionada.

### `SIN_CUADRILLA`

Terminación alternativa.

No existe una cuadrilla válida disponible y el caso requiere contingencia manual.

### `CASO_CANCELADO`

Terminación alternativa.

El aviso dejó de estar vigente antes de emitir la orden.

---

## Estructura del proyecto

```text
hidrandina_despacho_multiagente/
├── CLAUDE.md
├── README.md
├── Makefile
├── requirements.txt
├── .env.example
│
├── bpmn/
│   └── to_be_asignacion_despacho.bpmn
│
├── db/
│   ├── schema.sql
│   └── seed.sql
│
├── agents/
│   ├── analista_falla.py
│   ├── coordinador_cuadrillas.py
│   ├── emisor_orden.py
│   └── orquestador.py
│
├── tools/
│   ├── consultar_avisos.py
│   ├── consultar_cuadrillas.py
│   ├── verificar_estado_aviso.py
│   ├── registrar_orden.py
│   ├── notificar_orden.py
│   └── supabase_client.py
│
├── graph/
│   ├── llm.py
│   ├── state.py
│   └── workflow.py
│
├── models/
│   └── dominio.py
│
├── data/
├── tests/
├── skills/
├── hooks/
└── docs/
```

No crear nuevas carpetas, agentes, herramientas, microservicios o capas arquitectónicas sin una necesidad funcional o técnica concreta.

---

## Herramientas

Cada herramienta debe ser una función Python con type hints y docstring.

Las herramientas que acceden a Supabase deben reutilizar el cliente definido en:

`tools/supabase_client.py`

Herramientas existentes:

```python
consultar_avisos(
    zona: str,
    estado: str = "en_cola",
) -> list[Aviso]
```

```python
consultar_cuadrillas(
    especialidad: str,
    estado: str = "libre",
) -> list[Cuadrilla]
```

```python
verificar_estado_aviso(
    codigo_aviso: str,
) -> str
```

```python
registrar_orden(
    codigo_aviso: str,
    codigo_cuadrilla: str,
    prioridad: str,
) -> Orden
```

```python
notificar_orden(
    codigo_orden: str,
    codigo_cuadrilla: str,
) -> bool
```

`notificar_orden` representa actualmente una simulación del envío digital mediante logging.

No existe todavía una integración real con SMS, WhatsApp, correo electrónico u otro proveedor externo.

No agregar herramientas nuevas sin definir previamente:

- qué responsabilidad resuelven;
- qué agente las necesita;
- qué datos reciben;
- qué efecto producen;
- por qué no puede utilizarse una herramienta existente.

---

## Modelo LLM

La creación del modelo está centralizada en:

`graph/llm.py`

mediante:

`get_llm()`

No instanciar modelos independientemente dentro de cada agente.

El modelo configurado por defecto es:

`claude-sonnet-4-5`

mediante la API de Anthropic.

La API key se obtiene únicamente desde:

`ANTHROPIC_API_KEY`

Nunca incluir claves reales en:

- código;
- logs;
- documentación;
- commits.

Actualmente utilizan LLM:

```text
AnalistaDeFalla
CoordinadorDeCuadrillas
```

No utilizan LLM:

```text
Orquestador
EmisorDeOrden
Gateways
Persistencia
Verificación de vigencia
Notificación
```

Si no existe `ANTHROPIC_API_KEY`, `graph/llm.py` puede utilizar `FakeListChatModel`.

Una ejecución mediante `FakeListChatModel` no debe presentarse como una inferencia real de Anthropic.

Si la salida del modelo fake no cumple el esquema estructurado esperado, el agente debe utilizar su fallback determinista.

---

## Estado compartido de LangGraph

El estado compartido está definido en:

`graph/state.py`

Debe contener únicamente información necesaria para coordinar el subproceso.

Entre los campos relevantes se encuentran:

```text
codigo_aviso
zona
tipo_falla
prioridad
avisos_relacionados
cuadrilla_recomendada
aviso_vigente
orden_emitida
notificacion_enviada
resultado
mensaje_final
```

No utilizar el estado del grafo como almacenamiento general de información.

---

## Testing

La suite actual contiene:

```text
tests/test_analista.py
tests/test_coordinador.py
tests/test_integracion.py
tests/test_golden_cases.py
tests/golden_cases.json
```

Los 5 golden cases cubren:

```text
GOLDEN-01 → caso normal con cuadrilla disponible
GOLDEN-02 → incidente prioritario de transformador
GOLDEN-03 → ausencia de cuadrilla
GOLDEN-04 → aviso cancelado antes de emitir
GOLDEN-05 → varias cuadrillas válidas con prioridad por misma zona
```

Los escenarios exitosos deben terminar como:

```text
CUADRILLA_DESPACHADA
```

y verificar:

- registro de la orden;
- notificación de la orden.

Todo cambio funcional debe mantener los golden cases en verde o actualizar explícitamente las expectativas cuando exista una modificación justificada del BPMN o del contrato.

---

## Calidad de código

Antes de considerar terminado un cambio funcional deben ejecutarse:

```powershell
python -m ruff check .
```

```powershell
python -m mypy agents tools graph models
```

```powershell
python -m pytest tests -v
```

Estado de referencia validado en octubre de 2026:

```text
Ruff:
All checks passed!

mypy:
Success: no issues found in 17 source files

pytest:
14 passed
```

No considerar terminado un cambio funcional hasta comprobar nuevamente estas validaciones.

---

## Ejecución en Windows

El entorno principal de desarrollo actual es Windows PowerShell.

Activar el entorno virtual:

```powershell
.venv\Scripts\Activate.ps1
```

Ejecutar pruebas:

```powershell
python -m pytest tests -v
```

Ejecutar Ruff:

```powershell
python -m ruff check .
```

Ejecutar mypy:

```powershell
python -m mypy agents tools graph models
```

Ejecutar un caso:

```powershell
python -m graph.workflow --caso AV-2026-0001 --zona "Porvenir Norte" --tipo baja_tension --prioridad normal
```

No asumir que GNU Make está instalado en Windows.

El `Makefile` puede mantenerse como comodidad para entornos que dispongan de `make`, pero la documentación debe incluir también comandos Python/PowerShell equivalentes.

---

## Base de datos

El proyecto utiliza Supabase como capa de persistencia.

Los archivos versionados son:

```text
db/schema.sql
db/seed.sql
```

La aplicación utiliza:

```text
SUPABASE_URL
SUPABASE_KEY
```

desde `.env`.

Nunca incluir credenciales reales en el repositorio.

Mientras no exista una conexión PostgreSQL administrativa configurada específicamente para ejecutar DDL desde Python, no crear módulos ficticios como:

```text
db.apply_schema
db.apply_seed
```

El esquema y los datos iniciales pueden aplicarse utilizando el SQL Editor de Supabase.

El sistema:

- consulta avisos;
- consulta cuadrillas;
- verifica el estado de avisos;
- registra órdenes.

El sistema no cambia directamente una cuadrilla a estado `ocupada`.

---

## Human-in-the-Loop

El Supervisor CCO representa la contingencia humana del proceso.

Actualmente, cuando no existe una cuadrilla disponible, el flujo termina como:

```text
SIN_CUADRILLA
```

y representa el escalamiento hacia la gestión manual.

El proyecto no implementa actualmente una pausa interactiva mediante:

```text
interrupt()
resume()
```

de LangGraph.

Esta funcionalidad solo debe añadirse si el alcance académico requiere explícitamente demostrar Human-in-the-Loop dentro del mismo runtime.

---

## Correspondencia BPMN y código

| BPMN | Código |
|---|---|
| Analizar avisos relacionados | `agents/analista_falla.py` |
| Consultar y seleccionar cuadrilla | `agents/coordinador_cuadrillas.py` |
| ¿Hay cuadrilla disponible? | `agents/orquestador.py` + `graph/workflow.py` |
| Verificar vigencia del aviso | `agents/orquestador.py` + `tools/verificar_estado_aviso.py` |
| Emitir orden de trabajo | `agents/emisor_orden.py` + `tools/registrar_orden.py` |
| Notificar orden a cuadrilla asignada | `agents/orquestador.py` + `tools/notificar_orden.py` |
| Cuadrilla despachada | `ResultadoDespacho.CUADRILLA_DESPACHADA` |

---

## Convenciones de código

- Python 3.11 o superior.
- Type hints en funciones públicas.
- Dataclasses para las entidades principales del dominio.
- Pydantic `BaseModel` para salidas estructuradas del LLM.
- Logging mediante el módulo estándar `logging`.
- No utilizar `print()` como mecanismo de logging de producción.
- Mantener nombres del dominio en español cuando corresponda.
- Mantener responsabilidades delimitadas.
- No duplicar lógica de acceso a Supabase.
- No introducir dependencias nuevas sin una necesidad concreta.
- No modificar reglas del BPMN únicamente para facilitar la implementación.

---

## Fuente de verdad

Si existe una contradicción entre:

- código;
- documentación;
- tests;
- `CLAUDE.md`;

la fuente funcional principal es:

`bpmn/to_be_asignacion_despacho.bpmn`

Las demás piezas deben actualizarse para conservar la coherencia con el BPMN.

Si aparece un caso no contemplado, primero debe definirse cómo tratarlo antes de implementar comportamiento nuevo.

No agregar complejidad arquitectónica sin una necesidad derivada del proceso o de un requisito del curso.

---

## Qué queda fuera del alcance

Quedan fuera del alcance actual:

- ejecución física del trabajo en terreno;
- confirmación de recepción de la orden por parte de la cuadrilla;
- actualización automática de la cuadrilla a estado `ocupada`;
- cierre técnico de la incidencia después de reparar la falla;
- comunicación posterior con el cliente;
- integración real con un proveedor externo de mensajería;
- HITL interactivo mediante `interrupt()` y `resume()`.

---

**Última actualización del contrato:** octubre de 2026.