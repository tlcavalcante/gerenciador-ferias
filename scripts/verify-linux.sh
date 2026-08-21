#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

printf '%s\n' '== Gerenciador de Férias: verificação Linux ==' 
printf 'Diretório da aplicação: %s\n' "$ROOT_DIR"
printf 'Python: '; "$PYTHON_BIN" --version
printf 'Sistema: '; "$PYTHON_BIN" -c 'import platform; print(platform.platform())'
printf 'SQLite: '; "$PYTHON_BIN" -c 'import sqlite3; print(sqlite3.sqlite_version)'

cd "$ROOT_DIR"
"$PYTHON_BIN" -m compileall -q .
"$PYTHON_BIN" -c 'import core; assert core.APP_DIR.resolve() == __import__("pathlib").Path("core.py").resolve().parent; print("Módulos: OK")'

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
mkdir -p "$TMP_DIR/work"

PYTHONPATH="$ROOT_DIR" "$PYTHON_BIN" - <<'PY'
import os
from pathlib import Path
import core

assert core.APP_DIR.resolve() == Path(__file__).resolve().parent
assert core.BANCO_DADOS.parent.resolve() == core.APP_DIR.resolve()
assert core.BACKUP_DIR.resolve() == core.APP_DIR.resolve()
print(f"Diretório de dados: {core.DATA_DIR}")
print("Layout autocontido: OK")
PY

"$PYTHON_BIN" -m pytest -q
printf '%s\n' 'Verificação concluída com sucesso.'
