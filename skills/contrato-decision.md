# Skill: /contrato-decision

Cuando un agente debe tomar una decisión que no es un simple cálculo (elegir entre varias opciones, clasificar, puntuar), el output del LLM se mapea a un enum predefinido. Nunca se ejecuta ni se interpreta texto libre como instrucción.

## Patrón obligatorio

1. **Definir el enum de decisiones posibles** en `models/dominio.py`. Cada opción tiene nombre descriptivo.

2. **Prompt estructurado** que fuerza al modelo a devolver una de las opciones del enum, exactamente, sin texto adicional. Usar `langchain_core.output_parsers.PydanticOutputParser` o equivalente.

3. **Validación estricta** del output. Si el modelo devuelve algo fuera del enum, se descarta y se escala al humano o se usa el default seguro.

4. **Logging de la decisión** incluyendo las opciones consideradas y la elegida. Para auditabilidad.

## Qué NO hacer

- NO usar `eval()`, `exec()`, ni llamadas dinámicas basadas en texto del LLM.
- NO permitir que el modelo invente opciones nuevas en runtime.
- NO dejar que un output ambiguo del modelo detenga el flujo sin logging.
