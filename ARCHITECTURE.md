# Arquitetura — Gerenciador de Férias v3.9.1

## Princípio arquitetural

A aplicação é modular internamente, mas distribuída como uma pasta autocontida. Não existe dependência de um diretório de instalação, `cwd`, XDG ou variável de ambiente para localizar os dados.

## Módulos

- `gerenciador_ferias.py`: launcher executável.
- `app.py`: composição e inicialização.
- `core.py`: estado, configuração, interface comum e localização do diretório da aplicação.
- `runtime.py`: fachada do núcleo para os demais módulos.
- `database.py`: persistência SQLite e migrações.
- `business.py`: regras de férias e cálculos.
- `menus.py`: interface interativa.
- `dashboard.py`: painel e gráficos.

## Localização dos dados

`core.py` determina:

```python
APP_DIR = Path(__file__).resolve().parent
BANCO_DADOS = APP_DIR / "dados_ferias.db"
BACKUP_DIR = APP_DIR
```

Assim, se a pasta estiver em `/opt/gerenciador-ferias`, o banco será `/opt/gerenciador-ferias/dados_ferias.db`, independentemente de onde o comando for executado.

## Distribuição

A forma operacional recomendada é copiar a pasta inteira para o destino desejado e executar:

```bash
python3 gerenciador_ferias.py
```

O `pyproject.toml` continua disponível para build e testes de empacotamento, mas não é requisito para executar a aplicação de forma portátil.
