#!/usr/bin/env bash
# Hook de verificación: ruff + mypy sobre el archivo tocado.
# Se ejecuta automáticamente después de que Claude Code modifica un .py.

set -e

ARCHIVO="${1:-}"

if [[ -z "$ARCHIVO" ]]; then
  echo "Uso: $0 <archivo.py>"
  exit 1
fi

if [[ ! "$ARCHIVO" == *.py ]]; then
  exit 0
fi

echo "verificar_python.sh: ruff sobre $ARCHIVO"
.venv/bin/ruff check "$ARCHIVO"

echo "verificar_python.sh: mypy sobre $ARCHIVO"
.venv/bin/mypy "$ARCHIVO" || true  # mypy en modo permisivo al inicio

echo "verificar_python.sh: OK"
exit 0
