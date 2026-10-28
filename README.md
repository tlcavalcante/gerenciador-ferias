# Gerenciador de Férias

Aplicação de linha de comando (CLI) em Python para gerenciamento local de férias de equipes, com SQLite, autenticação, regras configuráveis, relatórios, painel, validação, calendário, backup e Banco de Horas.

**Versão publicada: 4.3.0**

## Requisitos

- Linux/Unix com terminal UTF-8 recomendado
- Python 3.9 ou superior
- SQLite incluído na biblioteca padrão do Python
- Nenhuma dependência Python externa para execução

## Execução

Na pasta do projeto:

```bash
python3 gerenciador_ferias.py
```

O programa solicita a criação do primeiro usuário administrador; não há senha administrativa padrão.

## Dados e backups

Por padrão, banco de dados e backups ficam em `~/.local/share/gerenciador-ferias/`. É possível definir um diretório alternativo por `GERENCIADOR_FERIAS_DATA_DIR`; na ausência dele, o programa considera `XDG_DATA_HOME` e usa o subdiretório `gerenciador-ferias`.

- Banco: `dados_ferias.db`
- Backups: subdiretório `backups/`

Para preservar a privacidade e a integridade dos dados, não publique o banco de dados, backups ou registros reais de funcionários no Git.

## Funcionalidades da versão 4.3.0

- Gestão de funcionários, setores, subsetores, vínculos e períodos de férias
- Regras configuráveis, validação, calendário, painel e relatórios
- Autenticação local e armazenamento de senhas com hash PBKDF2-HMAC-SHA256 e salt
- Banco de Horas com lançamentos em formato `HH:MM`, saldos positivos/negativos, extrato, relatórios, ajustes e ranking de alertas
- Backup consistente do SQLite e exportação de cópias
- Interface CLI com opções de acessibilidade visual e saída sem cores ANSI

## Testes

```bash
python3 -m pip install pytest
python3 -m pytest -q
bash scripts/verify-linux.sh
```

## Estrutura

O arquivo `gerenciador_ferias.py` é a aplicação autônoma da versão 4.3.0. Os módulos históricos `app.py`, `business.py`, `core.py`, `dashboard.py`, `database.py`, `menus.py` e `runtime.py` são mantidos no repositório para compatibilidade e testes de regressão.

## Segurança

- Não existe conta ou senha administrativa padrão.
- Defina uma senha exclusiva e forte ao criar o administrador.
- Armazene o banco e os backups em diretório com permissões restritas.
- Não versionar banco de dados, backups, credenciais reais ou dados pessoais.
- Hashes legados são tratados para permitir migração após autenticação válida.

## Licença

MIT.
