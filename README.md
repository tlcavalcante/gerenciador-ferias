# Gerenciador de Férias

Aplicação CLI em Python para gerenciamento de férias de equipes, com SQLite, autenticação, regras configuráveis, relatórios, painel e backup.

## Modelo de execução portátil

O projeto foi desenhado para funcionar como uma aplicação autocontida. O banco de dados e os arquivos de runtime ficam no **mesmo diretório dos arquivos do programa**.

O diretório de trabalho atual (`cwd`) não é utilizado para localizar os dados. Portanto, o programa pode ser executado de qualquer ponto do sistema:

```bash
cd /tmp
python3 /opt/gerenciador-ferias/gerenciador_ferias.py
```

O banco será criado em:

```text
/opt/gerenciador-ferias/dados_ferias.db
```

e os backups em arquivos `backup_*.db` no mesmo diretório.

Não há dependência de `XDG_DATA_HOME`, `GERENCIADOR_FERIAS_DATA_DIR` ou de um diretório de dados externo.

## Estrutura para uso

Para uma instalação simples, copie a pasta inteira para o local desejado:

```text
gerenciador-ferias/
├── gerenciador_ferias.py
├── app.py
├── business.py
├── core.py
├── dashboard.py
├── database.py
├── menus.py
├── runtime.py
├── dados_ferias.db          # criado na primeira execução
├── backup_YYYYMMDD_*.db     # criados pelo sistema
└── ...
```

O banco não deve ser versionado no Git.

## Requisitos

- Linux/Unix POSIX
- Python 3.10 ou superior
- SQLite disponível na biblioteca padrão do Python
- Terminal UTF-8 recomendado

Não existem dependências Python de execução além da biblioteca padrão.

## Execução direta

A forma recomendada é executar o launcher:

```bash
python3 gerenciador_ferias.py
```

Também é possível executar a partir de outro diretório usando o caminho absoluto:

```bash
python3 /opt/gerenciador-ferias/gerenciador_ferias.py
```

O aplicativo continua usando a própria pasta para localizar o banco e os demais dados.

## Instalação opcional como pacote

O projeto possui `pyproject.toml` para empacotamento e CI. Essa modalidade é voltada a desenvolvimento/distribuição Python. Para uma instalação operacional simples e autocontida, prefira a execução direta da pasta descrita acima.

## Primeira execução

Na primeira execução, o sistema solicita a criação do administrador inicial. Não existe senha administrativa padrão.

As senhas novas são armazenadas usando PBKDF2-HMAC-SHA256 com salt. Hashes SHA-256 legados são aceitos somente para migração e convertidos após autenticação bem-sucedida.

## Backup

Os backups são bancos SQLite independentes e ficam no mesmo diretório da aplicação:

```text
backup_YYYYMMDD_HHMMSS_ffffff.db
```

O sistema utiliza a API de backup do SQLite para criar cópias consistentes.

## Testes

```bash
python3 -m pytest
```

Para verificar a execução portátil:

```bash
bash scripts/verify-linux.sh
```

## Repositório Git

O repositório contém somente código, testes e documentação. O arquivo `dados_ferias.db` é criado pela aplicação e está explicitamente excluído do Git. Nunca publique bancos de dados, backups ou dados reais de funcionários.

## CI

O repositório possui GitHub Actions para testar múltiplas versões do Python, executar testes, verificar compilação e construir o pacote. A configuração segue o modelo atual de `pyproject.toml` e `project.scripts` recomendado pela documentação oficial de empacotamento Python.

## Segurança

Consulte [SECURITY.md](SECURITY.md).

## Arquitetura

Consulte [ARCHITECTURE.md](ARCHITECTURE.md).

## Compatibilidade Linux

Consulte [LINUX-COMPATIBILITY.md](LINUX-COMPATIBILITY.md).

## Licença

MIT.
