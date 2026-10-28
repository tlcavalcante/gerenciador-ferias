# Compatibilidade Linux

A aplicação 4.3.0 é compatível com Python 3.9 ou superior e utiliza somente bibliotecas da distribuição padrão do Python, incluindo `sqlite3`.

## Execução

```bash
python3 gerenciador_ferias.py
```

A aplicação pode ser iniciada de qualquer diretório. Os dados são armazenados no diretório definido por `GERENCIADOR_FERIAS_DATA_DIR`, por `XDG_DATA_HOME/gerenciador-ferias` ou, por padrão, em `~/.local/share/gerenciador-ferias`.

## Verificação

```bash
bash scripts/verify-linux.sh
python3 -m pytest -q
```

A verificação compila o código, inicializa um banco temporário e executa os testes automatizados.
