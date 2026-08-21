# Checklist de publicação

## Antes do primeiro push

- [ ] Remover qualquer `dados_ferias.db` local.
- [ ] Remover todos os `backup_*.db` locais.
- [ ] Executar `python -m pytest -q`.
- [ ] Executar `bash scripts/verify-linux.sh`.
- [ ] Executar `python -m compileall -q .`.
- [ ] Conferir `git status`.
- [ ] Conferir que não há credenciais, dados pessoais ou dados institucionais.

## GitHub

- [ ] Criar repositório público.
- [ ] Configurar branch `main`.
- [ ] Habilitar Issues.
- [ ] Habilitar Pull Requests.
- [ ] Configurar proteção da branch `main`.
- [ ] Tornar o workflow de testes obrigatório antes do merge.
- [ ] Criar o primeiro Release somente após CI verde.

## Release

- [ ] Definir versão final.
- [ ] Atualizar `pyproject.toml`.
- [ ] Atualizar `CHANGELOG.md`.
- [ ] Conferir README.
- [ ] Criar tag Git.
- [ ] Publicar Release.
