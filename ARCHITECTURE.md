# Arquitetura

## Visão geral
Aplicação CLI em Python, distribuída em script autônomo gerenciador_ferias.py e sem dependências externas de execução. O script concentra interface, regras de férias, autenticação, persistência, relatórios, Banco de Horas, escalas especiais e auditoria. O ponto de entrada é main().

## Persistência
O SQLite é acessado por _conn() e inicializado/migrado por _init_banco(). Entre as entidades estão funcionarios, setores, subsetores, vinculos, ferias, regras, banco_horas, escalas_especiais, escalas_especiais_funcionarios, usuarios, configuracoes e trilha_auditoria.

As conexões habilitam integridade referencial. A inicialização cria tabelas e índices ausentes, preservando os dados existentes.

## Edição de cadastro
A edição de colaboradores altera diretamente a linha correspondente em funcionarios, usando o identificador persistido e uma transação BEGIN IMMEDIATE. O gatilho AFTER UPDATE registra os estados anterior e posterior. Um evento adicional ATUALIZACAO_CADASTRO registra a justificativa e os campos efetivamente alterados na mesma transação. Os históricos de ferias e banco_horas permanecem vinculados ao mesmo funcionario_id; a edição não utiliza o salvamento geral dos cadastros.

## Apresentação dos gráficos
Os gráficos são renderizados no terminal pelas funções auxiliares `_barra_grafico()`, `_linha_grafico_mensal()`, `_grafico_indicadores()` e `_barra_saldo_bh()`. As barras mensais são proporcionais à escala definida para cada visão; comparações organizacionais calculam escala comum entre os setores ou subsetores da seleção. O gráfico do Banco de Horas usa eixo divergente central, com valores negativos e positivos em lados opostos. Os indicadores se reorganizam conforme a largura disponível e as cores respeitam o modo sem ANSI.

Os cálculos de evolução são separados da renderização: `_evolucao_empresa()` agrega dias, funcionários com férias e pico simultâneo por mês; `_evolucao_func()` calcula dias mensais e acumulados por funcionário. A interface oferece janelas de 3, 6, 12 ou 24 meses.

## Diretório de dados
A localização é resolvida por GERENCIADOR_FERIAS_DATA_DIR, depois XDG_DATA_HOME/gerenciador-ferias e, por padrão, ~/.local/share/gerenciador-ferias. Backups ficam no subdiretório backups/. O diretório de dados deve permanecer separado do código-fonte.

## Auditoria
A tabela trilha_auditoria recebe eventos por gatilhos AFTER INSERT, AFTER UPDATE e AFTER DELETE nas tabelas existentes, exceto a própria trilha. Eventos de autenticação e navegação são registrados por _auditar_evento(). As alterações incluem estado anterior e posterior. Campos de senha, hash, token e segredo são excluídos.

A consulta é restrita a administradores. Como os registros residem no mesmo SQLite da aplicação, a trilha não é inviolável: quem puder escrever no arquivo poderá alterar ou remover eventos. Requisitos de auditoria forte exigem armazenamento externo com controle de acesso independente.

## Segurança e compatibilidade
Senhas são derivadas por PBKDF2-HMAC-SHA256 com salt aleatório. Não há credencial administrativa padrão. Consultas com dados externos devem usar parâmetros SQL. O script requer Python 3.9 ou superior e utiliza a biblioteca padrão.
