# Contribuindo

## Ambiente

O projeto não possui dependências Python de runtime. Para desenvolvimento:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip pytest
```

## Testes

Execute:

```bash
python -m pytest -q
```

Antes de abrir um Pull Request, também execute:

```bash
bash scripts/verify-linux.sh
python -m compileall -q .
```

## Regras

- Não inclua banco de dados real no repositório.
- Não inclua backups, dados pessoais ou credenciais.
- Preserve a compatibilidade da execução direta por `gerenciador_ferias.py`.
- Alterações nas regras de férias devem incluir testes.
- Não altere a localização do banco para um diretório externo sem discussão prévia.

## Pull Requests

Descreva:

1. o problema;
2. a solução;
3. os testes realizados;
4. qualquer alteração de comportamento.
