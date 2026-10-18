# Skill: /agente-nuevo

Protocolo para agregar un subagente nuevo al sistema. Antes de escribir código, LEE el BPMN TO-BE y verifica que el agente propuesto tenga una responsabilidad única no cubierta por los agentes existentes.

## Pasos obligatorios

1. **Verificar necesidad real.** ¿Qué tarea del BPMN TO-BE no está cubierta por los agentes actuales? Si no hay respuesta clara, probablemente no se necesita un agente nuevo — basta con una tool.

2. **Definir responsabilidad única.** Una frase que empieza con "Este agente SOLO hace X". Si la frase lleva "y también", el agente debería ser dos.

3. **Definir contrato de entrada y salida.** Qué campos del `EstadoDespacho` lee, qué campos escribe. Documentar en el docstring del módulo.

4. **Listar herramientas que necesita.** Si alguna no existe en `tools/`, proponerla PRIMERO (no la implementes sin discutir).

5. **Crear el archivo `agents/<nombre>.py`** siguiendo la estructura de los agentes existentes.

6. **Crear test en `tests/test_<nombre>.py`** con al menos un caso feliz y un caso de borde.

7. **Agregar el nodo al grafo** en `graph/workflow.py` y verificar que las conditional edges no se rompan.

8. **Actualizar `CLAUDE.md`** si el agente introduce una invariante nueva.

## Qué NO hacer

- NO crear un agente para "coordinar" cosas que ya coordina el orquestador.
- NO crear un agente que acceda a tablas directamente sin pasar por `tools/`.
- NO crear un agente con menos de 3 líneas de lógica propia (eso es una tool, no un agente).
