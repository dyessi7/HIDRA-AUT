# Skill: /preflight-despacho

Verificación previa antes de ejecutar un caso real contra Supabase. No invocar el modelo real durante este chequeo.

```
disable_model_invocation: true
```

## Checklist

1. **Variables de entorno cargadas.** `SUPABASE_URL`, `SUPABASE_KEY` definidos y no vacíos.

2. **Conexión Supabase OK.** Hacer un `SELECT 1` o equivalente para confirmar que la base responde.

3. **Esquema esperado presente.** Verificar que las tablas `avisos`, `cuadrillas`, `ordenes` existen con sus columnas esperadas.

4. **Datos de ejemplo presentes.** Al menos 1 fila en cada tabla. Si está vacío, correr `make db-seed` antes de intentar.

5. **BPMN sincronizado.** El archivo `bpmn/to_be_asignacion_despacho.bpmn` tiene fecha de modificación posterior a la última versión mergeada del código. Si no, hay drift entre modelo y código.

6. **Tests golden en verde.** Al menos los goldens de "caso exitoso" y "sin cuadrilla disponible" pasan.

Si alguno falla, reportar y detener. No proceder con la ejecución real.
