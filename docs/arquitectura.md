# Arquitectura

## Visión general

El proyecto implementa el subproceso TO-BE `Asignación y despacho de cuadrilla` del proceso de atención de incidencias eléctricas de Hidrandina S.A. (Zonal Trujillo, Unidad de Negocios Trujillo).

El subproceso previo, `Recepción y clasificación del aviso`, se plantea como una automatización determinista mediante n8n. Su responsabilidad es recibir el aviso, validarlo, clasificarlo como avería de red y asignarle una prioridad antes de entregarlo al subproceso de asignación y despacho.

Este repositorio implementa específicamente la lógica multiagéntica del segundo subproceso.

El BPMN ubicado en:

`bpmn/to_be_asignacion_despacho.bpmn`

es la fuente de verdad funcional para la secuencia y las terminaciones del flujo.

La integración mediante webhook pertenece a la arquitectura global del proceso. El prototipo Python actual se concentra en la ejecución del grafo de despacho y puede ser invocado directamente desde código o terminal.

---

## Diagrama lógico

```text
                Subproceso previo
          Recepción y clasificación
                  RPA / n8n
                      |
                      v
             Incidencia clasificada
                      |
                      v
+----------------------------------------------------------------+
|       Hidrandina S.A. - Zonal Trujillo                         |
|                                                                |
|  +----------------------------------------------------------+  |
|  |              ORQUESTADOR LANGGRAPH                      |  |
|  |                                                          |  |
|  |  START                                                   |  |
|  |    |                                                     |  |
|  |    v                                                     |  |
|  |  analizar_falla                                         |  |
|  |    |                                                     |  |
|  |    v                                                     |  |
|  |  coordinar_cuadrilla                                    |  |
|  |    |                                                     |  |
|  |    v                                                     |  |
|  |  [¿hay cuadrilla?]                                      |  |
|  |    |                                                     |  |
|  |    +-- no --> sin_cuadrilla ----------------------> END  |  |
|  |    |                                                     |  |
|  |    +-- sí --> verificar_vigencia                         |  |
|  |                    |                                     |  |
|  |                    v                                     |  |
|  |              [¿sigue vigente?]                           |  |
|  |                    |                                     |  |
|  |                    +-- no --> caso_cancelado ------> END |  |
|  |                    |                                     |  |
|  |                    +-- sí --> emitir_orden               |  |
|  |                                  |                       |  |
|  |                                  v                       |  |
|  |                           ORDEN_EMITIDA                  |  |
|  |                                  |                       |  |
|  |                                  v                       |  |
|  |                         notificar_cuadrilla              |  |
|  |                                  |                       |  |
|  |                                  v                       |  |
|  |                    CUADRILLA_DESPACHADA ----------> END  |  |
|  +----------------------------------------------------------+  |
|                                                                |
|       |                     |                    |              |
|       v                     v                    v              |
|  AnalistaDeFalla     CoordinadorDeCuadrillas  EmisorDeOrden   |
|       |                     |                    |              |
|       v                     v                    v              |
|   DS_Avisos            DS_Cuadrillas        DS_Ordenes        |
+----------------------------------------------------------------+
```

---

## Componentes

### Orquestador

El orquestador está implementado mediante un grafo LangGraph y controla el flujo del caso de principio a fin.

No utiliza un LLM para decidir las transiciones del proceso.

Sus responsabilidades son:

- Secuenciar las llamadas a los subagentes.
- Evaluar si existe una cuadrilla válida disponible.
- Verificar nuevamente la vigencia del aviso antes de emitir una orden.
- Dirigir el flujo hacia las rutas alternativas.
- Ejecutar la notificación de la orden después de su emisión.
- Establecer el resultado final del proceso.

Las decisiones de flujo son deterministas.

Por ejemplo:

```text
¿hay cuadrilla?
→ sí / no

¿el aviso sigue vigente?
→ sí / no
```

Estas decisiones corresponden a reglas de negocio y no requieren razonamiento generativo.

---

### AnalistaDeFalla

El `AnalistaDeFalla` consulta los avisos abiertos correspondientes a la zona del incidente y analiza la información disponible.

Sus responsabilidades principales son:

- Consultar avisos relacionados.
- Identificar avisos compatibles con el incidente.
- Determinar el tipo de falla predominante.
- Generar una justificación del análisis.

El agente puede utilizar un LLM para realizar razonamiento contextual.

La respuesta del modelo se procesa mediante una salida estructurada que incluye:

```text
tipo_falla_predominante
avisos_relacionados
justificacion
```

El resultado producido por el LLM nunca se acepta directamente sin validación.

Los códigos de avisos relacionados deben pertenecer al conjunto de avisos realmente consultados.

Si el LLM no está disponible, devuelve una salida inválida, produce una excepción o incumple las restricciones definidas, el agente utiliza una estrategia determinista de respaldo.

De esta forma, la disponibilidad del LLM no determina la continuidad del proceso.

---

### CoordinadorDeCuadrillas

El `CoordinadorDeCuadrillas` consulta el registro de cuadrillas disponibles y determina cuáles pueden atender la incidencia.

Antes de cualquier recomendación se aplican restricciones deterministas obligatorias:

```text
especialidad = tipo_falla
estado = libre
```

Una cuadrilla que no cumpla ambas condiciones queda excluida de la selección.

Una vez obtenido el conjunto válido de candidatas, el LLM puede recomendar una de ellas utilizando el contexto operativo.

La recomendación estructurada contiene:

```text
codigo_cuadrilla
justificacion
```

El código recomendado se valida nuevamente contra el conjunto de candidatas permitido.

El LLM no puede seleccionar:

- Una cuadrilla ocupada.
- Una cuadrilla fuera de servicio.
- Una cuadrilla con especialidad incompatible.
- Una cuadrilla que no haya sido obtenida previamente por la herramienta.

Si el modelo falla o su recomendación no supera la validación, se utiliza el mecanismo determinista de respaldo.

En el comportamiento determinista actual se prioriza, cuando existe, una cuadrilla compatible cuya zona base coincida con la zona del incidente.

---

### EmisorDeOrden

El `EmisorDeOrden` es determinista.

No utiliza un LLM porque la generación y persistencia de una orden de trabajo requiere un comportamiento controlado y predecible.

Sus responsabilidades son:

- Recibir la cuadrilla previamente seleccionada.
- Recibir la información del aviso.
- Solicitar el registro de una nueva orden.
- Almacenar la orden devuelta por la herramienta.
- Establecer el estado intermedio `ORDEN_EMITIDA`.

El agente solo puede ejecutarse después de que el orquestador haya comprobado que el aviso continúa vigente.

La emisión de la orden no representa todavía el final exitoso del subproceso.

---

### Notificación de la orden

Después de obtener:

`ORDEN_EMITIDA`

el orquestador ejecuta la herramienta:

`notificar_orden`

Esta herramienta representa el envío digital de la orden a la cuadrilla seleccionada.

En el prototipo actual, la notificación se simula mediante logging y no existe todavía una integración real con servicios como WhatsApp, SMS, correo electrónico o una aplicación móvil de cuadrillas.

Tampoco se simula una confirmación de recepción.

Si el envío se realiza correctamente, el flujo termina como:

`CUADRILLA_DESPACHADA`

Este es el resultado final exitoso definido para el subproceso.

---

## Terminaciones del flujo

El subproceso puede finalizar de tres formas.

### Cuadrilla despachada

`CUADRILLA_DESPACHADA`

Ocurre cuando se completa correctamente la siguiente secuencia:

```text
Cuadrilla válida seleccionada
        ↓
Aviso sigue vigente
        ↓
Orden registrada
        ↓
ORDEN_EMITIDA
        ↓
Notificación enviada
        ↓
CUADRILLA_DESPACHADA
```

`ORDEN_EMITIDA` es únicamente un estado intermedio del flujo exitoso.

---

### Sin cuadrilla

`SIN_CUADRILLA`

Ocurre cuando no existe ninguna cuadrilla que satisfaga simultáneamente las restricciones de:

```text
especialidad compatible
estado libre
```

El flujo automatizado finaliza y el caso queda destinado conceptualmente a una contingencia manual asociada al Supervisor CCO.

---

### Caso cancelado

`CASO_CANCELADO`

Ocurre cuando, después de seleccionar una cuadrilla pero antes de emitir la orden, el sistema detecta que el aviso ya no se encuentra vigente.

En este escenario:

```text
no se registra una orden
no se envía una notificación
```

---

## Capas transversales

### `tools/`

Contiene las operaciones atómicas utilizadas por los agentes y el orquestador.

Las herramientas actuales son:

```text
consultar_avisos
consultar_cuadrillas
verificar_estado_aviso
registrar_orden
notificar_orden
```

Las operaciones relacionadas con Supabase comparten la configuración centralizada en:

`tools/supabase_client.py`

Las herramientas ejecutan operaciones concretas y no controlan por sí mismas el flujo general del proceso.

---

### `models/`

Contiene las estructuras principales del dominio:

```text
Aviso
Cuadrilla
Orden
```

También contiene enums utilizados para restringir los valores permitidos:

```text
TipoFalla
Prioridad
EstadoAviso
EstadoCuadrilla
ResultadoDespacho
```

El uso de estas estructuras permite evitar el manejo indiscriminado de diccionarios para las principales entidades del dominio.

---

### `graph/`

Contiene los elementos relacionados con la orquestación:

```text
graph/state.py
graph/workflow.py
graph/llm.py
```

`state.py` define el estado compartido durante la ejecución.

`workflow.py` contiene la topología LangGraph y sus transiciones.

`llm.py` centraliza la creación del modelo utilizado por los agentes que requieren razonamiento contextual.

---

## Flujo LangGraph

La topología implementada actualmente es:

```text
START
  |
  v
analizar_falla
  |
  v
coordinar_cuadrilla
  |
  v
¿hay cuadrilla?
  |
  +--- no ---> sin_cuadrilla ---> END
  |
  +--- sí
         |
         v
verificar_vigencia
         |
         v
¿sigue vigente?
         |
         +--- no ---> caso_cancelado ---> END
         |
         +--- sí
                |
                v
          emitir_orden
                |
                v
        notificar_cuadrilla
                |
                v
               END
```

Los siete nodos funcionales del grafo son:

```text
analizar_falla
coordinar_cuadrilla
verificar_vigencia
emitir_orden
notificar_cuadrilla
sin_cuadrilla
caso_cancelado
```

---

## Uso del LLM

El sistema utiliza un enfoque híbrido que combina razonamiento mediante LLM con reglas deterministas.

Actualmente utilizan LLM:

```text
AnalistaDeFalla
CoordinadorDeCuadrillas
```

No utilizan LLM:

```text
Orquestador
EmisorDeOrden
Herramientas de persistencia
Gateways del proceso
Verificación de vigencia
Notificación
```

El objetivo es utilizar el modelo únicamente donde aporta valor contextual y mantener mediante código convencional las restricciones críticas del dominio.

---

## Salidas estructuradas y fallback

Las respuestas de los agentes que utilizan un LLM se validan mediante modelos estructurados.

El modelo no controla directamente el estado del sistema.

La secuencia conceptual es:

```text
Datos válidos
    ↓
Prompt
    ↓
LLM
    ↓
Salida estructurada
    ↓
Validación
    ↓
Decisión aceptada
```

Si alguna de estas etapas falla debido a:

```text
LLM no disponible
respuesta no parseable
valor inexistente
violación de una restricción
```

se activa una lógica determinista de respaldo.

Esto permite mantener el flujo operativo incluso cuando no existe acceso a la API del modelo.

---

## Modelo LLM

La instanciación del modelo se encuentra centralizada en:

`graph/llm.py`

El modelo configurado por defecto es:

`claude-sonnet-4-5`

mediante la API de Anthropic.

La clave se obtiene desde la variable de entorno:

`ANTHROPIC_API_KEY`

y no debe almacenarse directamente en el código ni incluirse en el repositorio.

Cuando no existe una API key configurada, el proyecto puede utilizar un `FakeListChatModel`.

Este mecanismo permite desarrollar y ejecutar el proyecto sin depender permanentemente de una llamada externa.

El modelo fake no representa una inferencia real de Anthropic.

Si su respuesta no satisface el esquema estructurado esperado, los agentes utilizan automáticamente el comportamiento determinista de respaldo.

---

## Decisiones de diseño

### Por qué LangGraph

LangGraph permite representar explícitamente un proceso que contiene:

- Secuencia de agentes.
- Estado compartido.
- Gateways condicionales.
- Rutas alternativas.
- Diferentes terminaciones.

La topología del código se mantiene cercana a la estructura definida en el BPMN.

Además, permite una posible evolución posterior hacia capacidades como checkpoints, observabilidad o mecanismos Human-in-the-Loop sin rediseñar completamente el flujo.

Para este proyecto se utiliza únicamente la complejidad necesaria para representar el subproceso.

---

### Por qué el orquestador es determinista

Las decisiones centrales del flujo representan reglas de negocio claras.

Por ejemplo:

```text
¿existe una cuadrilla válida?
¿el aviso continúa vigente?
```

Estas decisiones no requieren interpretación generativa.

Utilizar un LLM para resolverlas agregaría incertidumbre, latencia y costo sin aportar una mejora funcional.

Por ello, el orquestador controla el proceso mediante reglas deterministas.

---

### Por qué el Analista y el Coordinador pueden usar LLM

Estos agentes contienen actividades donde existe mayor valor contextual.

El Analista puede interpretar relaciones entre avisos y justificar un diagnóstico predominante.

El Coordinador puede razonar sobre cuál de varias cuadrillas previamente válidas resulta preferible.

Sin embargo, el LLM trabaja únicamente dentro de límites previamente establecidos.

Las restricciones críticas siempre se verifican mediante código determinista.

---

### Por qué el EmisorDeOrden es determinista

La creación de una orden de trabajo es una operación transaccional.

No requiere generación de lenguaje ni una decisión abierta.

Por ello:

```text
Selección válida
        +
Aviso vigente
        ↓
Registrar orden
```

se ejecuta mediante código convencional.

---

### Por qué se verifica nuevamente la vigencia

Entre la recepción inicial del aviso y la emisión de la orden, el estado de la incidencia puede cambiar.

Por ejemplo, el aviso podría haber sido cancelado.

Por esta razón, seleccionar previamente una cuadrilla no es suficiente.

El sistema vuelve a consultar el estado actual del aviso inmediatamente antes de registrar la orden.

Esto implementa una de las invariantes principales del dominio.

---

### Por qué existe una notificación después de emitir

El BPMN no termina simplemente cuando la orden queda registrada.

Después de:

`Emitir orden de trabajo`

existe la actividad:

`Notificar orden a cuadrilla asignada`

y posteriormente la terminación:

`Cuadrilla despachada`

Por ello, el código distingue entre:

`ORDEN_EMITIDA`

y:

`CUADRILLA_DESPACHADA`

---

### Por qué un cliente Supabase compartido

La creación del cliente está centralizada para:

- Evitar duplicar configuración.
- Mantener un único punto de acceso a credenciales.
- Reutilizar consistentemente el cliente.
- Simplificar las herramientas.

Las herramientas no deben crear configuraciones independientes de Supabase.

---

### Por qué separar `tools/` de `agents/`

Las herramientas representan operaciones concretas, por ejemplo:

```text
consultar
verificar
registrar
notificar
```

Los agentes representan responsabilidades dentro del proceso.

Esta separación permite diferenciar:

```text
qué operación puede ejecutarse
```

de:

```text
por qué y cuándo debe ejecutarse
```

y evita duplicar la lógica de acceso a datos.

---

## Supervisor CCO y Human-in-the-Loop

El BPMN contempla un carril humano correspondiente al Supervisor CCO para situaciones que requieren contingencia manual.

En la implementación actual, cuando no existe una cuadrilla disponible, el flujo termina como:

`SIN_CUADRILLA`

y representa el escalamiento del caso hacia una gestión manual.

Actualmente no se implementa una pausa interactiva mediante mecanismos de LangGraph como:

```text
interrupt()
resume()
```

Por tanto, el proyecto implementa el punto de escalamiento hacia el humano, pero no una sesión humana interactiva dentro del mismo runtime.

Esta funcionalidad puede incorporarse posteriormente si el alcance académico exige demostrar Human-in-the-Loop de manera interactiva.

---

## Correspondencia BPMN y código

| BPMN | Implementación |
|---|---|
| Analizar avisos relacionados | `agents/analista_falla.py` |
| Consultar y seleccionar cuadrilla | `agents/coordinador_cuadrillas.py` + `tools/consultar_cuadrillas.py` |
| ¿Hay cuadrilla disponible? | `agents/orquestador.py` + `graph/workflow.py` |
| Verificar vigencia del aviso | `agents/orquestador.py` + `tools/verificar_estado_aviso.py` |
| Emitir orden de trabajo | `agents/emisor_orden.py` + `tools/registrar_orden.py` |
| Notificar orden a cuadrilla asignada | `agents/orquestador.py` + `tools/notificar_orden.py` |
| Cuadrilla despachada | `ResultadoDespacho.CUADRILLA_DESPACHADA` |

---

## Persistencia

El prototipo utiliza Supabase como capa de persistencia.

Los principales almacenes conceptuales son:

```text
DS_Avisos
DS_Cuadrillas
DS_Ordenes
```

El esquema versionado se encuentra en:

`db/schema.sql`

y los datos iniciales de prueba en:

`db/seed.sql`

El sistema consulta avisos y cuadrillas y registra órdenes.

Una restricción importante del alcance es que este sistema:

`NO cambia directamente una cuadrilla a ocupada`

El cambio real de disponibilidad requeriría una confirmación posterior relacionada con la operación en campo.

---

## Validación de la arquitectura

La implementación dispone actualmente de pruebas unitarias, de integración y golden cases.

Las rutas principales verificadas incluyen:

- Caso normal con despacho.
- Incidente prioritario.
- Ausencia de cuadrilla.
- Cancelación antes de emitir.
- Selección entre varias cuadrillas válidas.

El estado técnico de referencia actual es:

```text
pytest
14 passed

Ruff
All checks passed!

mypy
Success: no issues found in 17 source files
```

Estas validaciones comprueban el comportamiento automatizado, el lint y el tipado estático del proyecto.

No sustituyen una prueba posterior de integración real con Supabase ni, cuando corresponda, una ejecución utilizando la API real del LLM.

---

## Invariantes del dominio

Las reglas completas se encuentran en:

`CLAUDE.md`

Entre las invariantes principales se encuentran:

- No emitir una orden sin verificar previamente la vigencia del aviso.
- No seleccionar una cuadrilla con especialidad incompatible.
- No seleccionar una cuadrilla cuyo estado sea distinto de `libre`.
- No permitir que el LLM seleccione elementos fuera del conjunto válido.
- No modificar directamente una cuadrilla a estado `ocupada`.
- No ejecutar código generado por el LLM.
- No considerar `ORDEN_EMITIDA` como la terminación exitosa final.
- No simular una confirmación de recepción de la cuadrilla.

---

## Qué queda fuera de este sistema

Quedan fuera del alcance actual:

- Ejecución física del trabajo en terreno.
- Confirmación de recepción de la orden por parte de la cuadrilla.
- Actualización automática de la cuadrilla a estado `ocupada`.
- Cierre técnico de la incidencia después de reparar la falla.
- Comunicación posterior con el cliente.
- Integración real con un proveedor externo de mensajería.
- Operación humana interactiva dentro del grafo mediante `interrupt()` y `resume()`.

Estas actividades pueden formar parte del proceso completo de atención de incidencias, pero no pertenecen al alcance implementado actualmente.