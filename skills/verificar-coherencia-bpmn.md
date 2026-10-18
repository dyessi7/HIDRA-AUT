# Skill: /verificar-coherencia-bpmn

Chequeo de que el código del grafo (`graph/workflow.py`) corresponde a la topología del BPMN TO-BE (`bpmn/to_be_asignacion_despacho.bpmn`). Esta verificación mantiene el diseño y la implementación en el mismo paso.

## Qué verificar

1. **Un nodo del grafo por cada serviceTask / sendTask / receiveTask del BPMN** que esté dentro de los carriles de los agentes (Orquestador, AnalistaDeFalla, CoordinadorDeCuadrillas, EmisorDeOrden).

2. **Las compuertas exclusivas del BPMN** se corresponden con `add_conditional_edges` en el grafo con el mismo nombre y las mismas ramas.

3. **Los endEvents del BPMN** se corresponden con nodos terminales del grafo (`add_edge(nodo, END)`).

4. **Los boundary events del BPMN** se corresponden con rutas condicionales desde el nodo correspondiente.

## Qué hacer si hay drift

- Si el BPMN cambió y el código no: actualizar el código y los tests, en el mismo PR.
- Si el código cambió y el BPMN no: actualizar el BPMN primero (en bpmn.io), exportar, commitear junto al cambio de código.
- Nunca mergear un cambio donde los dos difieren sin justificación en el commit message.
