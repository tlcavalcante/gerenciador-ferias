#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

fail=0

if find . -type f \( -name 'dados_ferias.db' -o -name 'backup_*.db' \) -print -quit | grep -q .; then
  echo "FALHA: banco ou backup local encontrado"
  fail=1
else
  echo "OK: banco/backups locais ausentes"
fi

if find . -type d \( -name '__pycache__' -o -name '.pytest_cache' \) -print -quit | grep -q .; then
  echo "AVISO: caches presentes antes da execução; serão removidos no pacote final"
else
  echo "OK: caches ausentes"
fi

python3 - <<'PY'
from pathlib import Path
import re, sys

files = [*Path('.').glob('*.py'), Path('pyproject.toml')]
patterns = {
    'credenciais padrão/segredos conhecidos': re.compile(r'admin/admin123|password\s*=\s*["\']admin123|SECRET_KEY\s*=', re.I),
    'chaves privadas': re.compile(r'BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY'),
    'tokens conhecidos': re.compile(r'(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,})'),
    'caminhos absolutos específicos de ambiente': re.compile(r'/home/[^/]+/|/Users/[^/]+/|/mnt/data/'),
}
failed = False
for desc, pattern in patterns.items():
    hits=[]
    for path in files:
        text=path.read_text(encoding='utf-8', errors='ignore')
        if pattern.search(text):
            hits.append(str(path))
    if hits:
        print(f'FALHA: {desc}')
        for h in hits: print(f'  {h}')
        failed=True
    else:
        print(f'OK: {desc}')
if failed:
    sys.exit(1)
PY

python3 -m compileall -q .
python3 -m pytest -q

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi

echo "Pré-GitHub: OK"
