# Changelog

## [3.9.1] — Preparação para publicação

### Fases 1–6
- Hardening de autenticação e armazenamento de senhas.
- Migração compatível de hashes SHA-256 legados para PBKDF2-HMAC-SHA256.
- Bloqueio temporário após tentativas de autenticação malsucedidas.
- Backup e restauração utilizando a API nativa do SQLite.
- Correções no cálculo de datas e períodos aquisitivos.
- Criação de testes automatizados para segurança e regras de negócio.
- Refatoração do aplicativo monolítico em módulos.
- Execução independente do diretório de trabalho atual.
- Dados persistentes armazenados no mesmo diretório do aplicativo.
- Compatibilidade documentada para Linux/Python 3.10+.
- CI com testes, compilação, verificação de portabilidade e build.
- Documentação para arquitetura, segurança, contribuição e publicação.
- Auditoria final pré-GitHub e remoção de artefatos locais/dados de execução.

## Histórico

A versão original 3.8.1 foi utilizada como base funcional para as fases de modernização. As regras de negócio foram preservadas e protegidas por testes antes da refatoração arquitetural.
