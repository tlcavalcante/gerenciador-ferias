# Arquitetura

## Visão geral
Aplicação CLI em Python, distribuída em script autônomo gerenciador_ferias.py e sem dependências externas de execução. O script concentra interface, regras de férias, autenticação, persistência, relatórios, Banco de Horas, escalas especiais e auditoria. O ponto de entrada é main().

## Persistência
O SQLite é acessado por _conn() e inicializado/migrado por _init_banco(). Entre as entidades estão funcionarios, setores, subsetores, vinculos, ferias, regras, banco_horas, escalas_especiais, escalas_especiais_funcionarios, usuarios, configuracoes e trilha_auditoria.

As conexões habilitam integridade referencial. A inicialização cria tabelas e índices ausentes, preservando os dados existentes.

## Diretório de dados
A localização é resolvida por GERENCIADOR_FERIAS_DATA_DIR, depois XDG_DATA_HOME/gerenciador-ferias e, por padrão, ~/.local/share/gerenciador-ferias. Backups ficam no subdiretório backups/. O diretório de dados deve permanecer separado do código-fonte.

## Auditoria
A tabela trilha_auditoria recebe eventos por gatilhos AFTER INSERT, AFTER UPDATE e AFTER DELETE nas tabelas existentes, exceto a própria trilha. Eventos de autenticação e navegação são registrados por _auditar_evento(). As alterações incluem estado anterior e posterior. Campos de senha, hash, token e segredo são excluídos.

A consulta é restrita a administradores. Como os registros residem no mesmo SQLite da aplicação, a trilha não é inviolável: quem puder escrever no arquivo poderá alterar ou remover eventos. Requisitos de auditoria forte exigem armazenamento externo com controle de acesso independente.

## Segurança e compatibilidade
Senhas são derivadas por PBKDF2-HMAC-SHA256 com salt aleatório. Não há credencial administrativa padrão. Consultas com dados externos devem usar parâmetros SQL. O script requer Python 3.9 ou superior e utiliza a biblioteca padrão.
