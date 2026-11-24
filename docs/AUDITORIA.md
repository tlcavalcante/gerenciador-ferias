# Trilha de auditoria

## Finalidade
Registrar operações para identificar o usuário, o momento e o registro afetado. A consulta está no menu Administração e exige perfil administrador.

## Campos
Conforme a operação, cada evento contém data/hora local com fuso, identificador/login/nome do usuário, ação, entidade ou tabela, identificador do registro, detalhes e resultado.

## Cobertura
A tabela trilha_auditoria é criada durante _init_banco(). Gatilhos SQLite AFTER INSERT, AFTER UPDATE e AFTER DELETE registram operações nas tabelas existentes, exceto na própria trilha. Alterações incluem estados anterior e posterior.

Eventos de aplicação incluem autenticação bem-sucedida, falhas de autenticação, acesso administrativo, navegação nos módulos principais e encerramento normal da sessão.

## Edição de cadastro de colaboradores
A opção **Alterar cadastro de colaborador** fica disponível no menu de funcionários somente para o perfil administrador. A rotina repete a verificação de autorização antes de iniciar a gravação; a restrição não depende apenas da visibilidade da opção na interface.

A edição permite alterar nome, setor, subsetor, vínculo e data de admissão. ENTER mantém o valor atual. O motivo é obrigatório, com 5 a 1.000 caracteres, e a operação exige confirmação. Nome, setor e subsetor são obrigatórios. Não é permitido repetir nome dentro do mesmo setor/subsetor; a comparação não diferencia maiúsculas e minúsculas.

A gravação utiliza BEGIN IMMEDIATE e atualiza diretamente a linha correspondente em funcionarios. A rotina não chama o salvamento geral dos cadastros, evitando regravar férias, Banco de Horas ou outros registros sem relação com a edição. A transação contém dois eventos complementares:

1. O gatilho AFTER UPDATE registra a ação UPDATE e o JSON com os estados anterior e posterior dos campos da tabela funcionarios.
2. O evento ATUALIZACAO_CADASTRO registra a justificativa, o colaborador, os campos alterados e a indicação de que os históricos de férias e Banco de Horas foram preservados.

Os dois eventos e a atualização cadastral são confirmados em um único commit. Se ocorrer erro, a transação é revertida e nenhum dos eventos é confirmado. O evento explícito contém registro_id, login e nome do responsável, data/hora local com fuso e resultado da operação.

A edição preserva os identificadores e os registros existentes em ferias e banco_horas. Alterar setor ou subsetor não reclassifica retroativamente os dados: relatórios organizacionais passam a agrupar o colaborador pela lotação cadastral atual. Essa consequência é apresentada antes da confirmação.

## Credenciais
Colunas com nomes associados a senha, hash de senha, password, token ou secret são excluídas da captura. A senha digitada não é registrada. Falhas de autenticação registram o login informado e o resultado, nunca a senha.

Os detalhes podem conter dados pessoais e informações funcionais. Restrinja o acesso ao banco e à consulta.

## Limitações
A trilha reside no mesmo arquivo SQLite. Não é inviolável: alguém com permissão de escrita no arquivo poderá alterar ou apagar eventos. Também não substitui serviço central de logs, armazenamento imutável ou segregação formal de funções.

Para requisitos institucionais mais rigorosos, encaminhe eventos a serviço externo com autenticação independente, retenção definida, controle de acesso e proteção contra alteração.

## Retenção
A consulta apresenta os 100 eventos mais recentes. Não há expurgo automático implementado nesta versão. Defina retenção conforme política institucional e mantenha backups protegidos.
