#!/usr/bin/env bash
# Hook de protección: bloquea edición directa de archivos sensibles.
# Claude Code debe proponer el diff en vez de aplicarlo automáticamente.
#
# Rutas protegidas:
# - CLAUDE.md               (contrato invariante)
# - db/schema.sql           (esquema de la base)
# - .env                    (credenciales reales)
# - bpmn/*.bpmn             (fuente de verdad del modelo)

set -e

ARCHIVO_EDITADO="${1:-}"

RUTAS_PROTEGIDAS=(
  "CLAUDE.md"
  "db/schema.sql"
  ".env"
  "bpmn/"
)

for ruta in "${RUTAS_PROTEGIDAS[@]}"; do
  if [[ "$ARCHIVO_EDITADO" == *"$ruta"* ]]; then
    echo "ERROR: Archivo protegido: $ARCHIVO_EDITADO"
    echo "Claude Code debe proponer un diff para que el humano apruebe."
    echo "No se aplica la edición directa."
    exit 1
  fi
done

exit 0
