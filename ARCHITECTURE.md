# Arquitetura

A versão 4.3.0 é uma aplicação CLI autônoma em `gerenciador_ferias.py`. A lógica de interface, regras de férias, autenticação, persistência SQLite, relatórios, banco de horas e backups está no arquivo principal para permitir distribuição simples sem dependências externas.

## Persistência

O SQLite mantém tabelas de setores, subsetores, vínculos, funcionários, férias, regras, configurações, usuários e lançamentos de banco de horas. O banco é inicializado por `_init_banco()`.

O diretório de dados é resolvido nesta ordem:
1. `GERENCIADOR_FERIAS_DATA_DIR`, quando definido;
2. `$XDG_DATA_HOME/gerenciador-ferias`, quando `XDG_DATA_HOME` estiver definido;
3. `~/.local/share/gerenciador-ferias`.

Os backups são cópias consistentes criadas pela API de backup do SQLite e ficam no subdiretório `backups/`.

## Segurança

As senhas novas são derivadas com PBKDF2-HMAC-SHA256 e salt aleatório. Não há credencial administrativa padrão; o administrador é criado na primeira execução. A validação de entradas e as consultas SQL parametrizadas devem ser mantidas nos novos recursos.

## Compatibilidade

Os módulos históricos permanecem disponíveis para testes de regressão. O comando instalado pelo pacote aponta para `gerenciador_ferias:main`.
