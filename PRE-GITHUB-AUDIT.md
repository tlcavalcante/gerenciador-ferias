# Revisão final pré-GitHub — Gerenciador de Férias 3.9.1

## Resultado

**Aprovado para criação do repositório, condicionado à execução do checklist de publicação e à revisão humana final.**

## Verificações realizadas

| Verificação | Resultado |
|---|---|
| Testes automatizados | 26 passaram |
| Compilação Python | OK |
| Banco local removido do pacote | OK |
| `__pycache__` removido | OK |
| `.pytest_cache` removido | OK |
| Credencial administrativa padrão no código de produção | Não encontrada |
| Chaves privadas/tokens conhecidos | Não encontrados |
| Caminhos absolutos de ambiente institucional | Não encontrados |
| Dependências Python de execução | Nenhuma |
| Dados pessoais/institucionais no código | Não identificados |
| Licença | MIT |
| Documentação de segurança | Presente |
| Contribuição | Presente |
| CI | Presente |

## Observações importantes

### Banco de dados

O projeto anterior continha `dados_ferias.db` apenas como artefato local de execução. Ele foi removido do pacote final. O banco deve ser criado na primeira execução e permanece ao lado do programa.

### Senhas

A implementação atual utiliza PBKDF2-HMAC-SHA256 para novas senhas. O suporte a SHA-256 simples permanece exclusivamente para migração de bancos legados e deve ser removido em uma futura versão após a migração de todos os ambientes conhecidos.

### Tratamento de exceções

Ainda existem alguns `except:` genéricos em módulos legados. Eles não representam uma credencial ou exposição direta de dados, mas constituem dívida técnica e devem ser eliminados em uma futura fase de qualidade de código.

### Empacotamento

A execução operacional recomendada é a pasta autocontida. O `pyproject.toml` permanece para CI e distribuição Python. A validação final do wheel deve ser realizada pelo GitHub Actions, inclusive nas versões de Python não disponíveis no ambiente local.

## Itens que o mantenedor deve confirmar manualmente antes do primeiro push

- [ ] O nome e a descrição do repositório estão corretos.
- [ ] O e-mail público do perfil GitHub está conforme a preferência do mantenedor.
- [ ] A licença MIT é a desejada.
- [ ] Não há outros arquivos fora desta pasta que devam entrar no repositório.
- [ ] O repositório será criado como público somente após conferência do primeiro commit.
- [ ] Branch `main` e proteção de branch serão configuradas.
- [ ] GitHub Actions ficará obrigatório antes de merge.
- [ ] Issues/Discussions serão habilitadas somente se desejado.
- [ ] O primeiro Release será criado após CI verde.
