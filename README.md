# Gerenciador de Férias — versão 4.3.9

Aplicação local de linha de comando (CLI), em Python, para gestão de férias de equipes e Banco de Horas, com persistência SQLite.

## Requisitos

- Python 3.9 ou superior.
- Linux/Unix e terminal UTF-8 recomendados.
- SQLite incluído na biblioteca padrão.
- Nenhuma dependência Python externa para executar a aplicação autônoma.

## Execução

```bash
python3 gerenciador_ferias.py
```

Na primeira execução, crie o usuário administrador quando solicitado. Não há senha administrativa padrão.

## Dados e backup

A localização dos dados é determinada nesta ordem: `GERENCIADOR_FERIAS_DATA_DIR`, `$XDG_DATA_HOME/gerenciador-ferias` ou `~/.local/share/gerenciador-ferias`. O banco é `dados_ferias.db` e os backups ficam em `backups/`.

**Não publique o banco de dados, backups, exportações com dados reais de funcionários nem credenciais no Git.** Antes de atualizar, faça backup e siga [docs/ATUALIZACAO.md](docs/ATUALIZACAO.md).

## Funcionalidades da versão 4.3.9

- Gestão de funcionários, setores, subsetores e períodos de férias.
- Regras de férias, validações, calendário e relatórios.
- Banco de Horas com movimentações, extrato, ajustes e saldos positivos/negativos.
- Conciliação do saldo final com relatório mensal, registrando a diferença como ajuste e preservando o histórico.
- Relatórios tabulares com cabeçalhos e paginação; tabelas limitadas aos relatórios.
- Rankings completos, sem limitação automática a Top 25.
- Preferência persistente para ocultar ou exibir colaboradores com saldo zerado.
- Destaque em vermelho para saldos negativos e saldos que atingem ou ultrapassam o limite crítico configurado.
- Menus reorganizados, com numeração sequencial, e funções de validação, configurações e administração agrupadas.

## Documentação

- [Guia de operação](docs/OPERACAO.md)
- [Procedimento de atualização e reversão](docs/ATUALIZACAO.md)
- [Testes e validação](docs/TESTES-E-VALIDACAO.md)
- [Segurança e backup](docs/SEGURANCA-E-BACKUP.md)
- [Histórico de versões](CHANGELOG.md)
- [Checklist de release](RELEASE-CHECKLIST.md)

## Testes

A compilação sintática foi verificada na preparação da versão. Isso não substitui os testes funcionais completos em homologação. Execute o checklist em [docs/TESTES-E-VALIDACAO.md](docs/TESTES-E-VALIDACAO.md) antes do uso operacional.

## Licença

MIT. Consulte [LICENSE](LICENSE).
