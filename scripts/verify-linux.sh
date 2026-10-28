#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

printf '%s\n' '== Gerenciador de Férias: verificação Linux =='
"$PYTHON_BIN" --version
"$PYTHON_BIN" -m compileall -q "$ROOT_DIR"
GERENCIADOR_FERIAS_DATA_DIR="$TMP_DIR/data" PYTHONPATH="$ROOT_DIR" "$PYTHON_BIN" - <<'PY'
import os
from pathlib import Path
import gerenciador_ferias as app

assert isinstance(app.APP_VERSION, str) and app.APP_VERSION.startswith("4.")
app._init_banco()
assert app.BANCO_DADOS.is_file()
assert app.BANCO_DADOS.parent == Path(os.environ["GERENCIADOR_FERIAS_DATA_DIR"])
print("Inicialização SQLite: OK")
print("Diretório de dados configurável: OK")
PY
cd "$ROOT_DIR"
"$PYTHON_BIN" -m pytest -q
printf '%s\n' 'Verificação concluída com sucesso.'
