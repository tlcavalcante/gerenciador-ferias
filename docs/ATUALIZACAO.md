# Procedimento de atualização

## Antes de atualizar

1. Identifique o diretório de dados: `GERENCIADOR_FERIAS_DATA_DIR`, depois `$XDG_DATA_HOME/gerenciador-ferias`, caso definido, ou `~/.local/share/gerenciador-ferias`.
2. Encerre o aplicativo e confirme que não há processo escrevendo no banco.
3. Faça backup de `dados_ferias.db` e do diretório `backups/`.
4. Guarde uma cópia do script anterior para reversão.
5. Registre versão anterior, horário e responsável.

## Validar o código

```bash
python3 --version
python3 -m py_compile gerenciador_ferias.py
```

A compilação verifica a sintaxe, não todas as funções. Execute os testes de [TESTES-E-VALIDACAO.md](TESTES-E-VALIDACAO.md) em homologação, usando uma cópia do banco.

## Instalar

1. Substitua o script da instalação pelo arquivo aprovado `gerenciador_ferias.py`.
2. Preserve o diretório de dados existente; não o apague nem o inclua no Git.
3. Inicie o programa e valide autenticação, cadastros, férias e Banco de Horas.
4. Confira a configuração de ocultação de saldos zerados, os rankings e a conciliação de saldo final.

## Reversão

Se ocorrer erro, encerre o aplicativo e restaure o script anterior. Restaure o banco apenas se houver evidência de corrupção ou alteração incompatível, mantendo uma cópia do estado atual para análise. Não repita a atualização em produção antes de reproduzir o problema em homologação.

## Proteção de dados

Use dados fictícios ou anonimizados nos testes. Não adicione ao Git banco de dados, backups, exportações com nomes reais, logs sensíveis ou credenciais.
