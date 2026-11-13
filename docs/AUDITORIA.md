# Trilha de auditoria

## Finalidade
Registrar operações para identificar o usuário, o momento e o registro afetado. A consulta está no menu Administração e exige perfil administrador.

## Campos
Conforme a operação, cada evento contém data/hora local com fuso, identificador/login/nome do usuário, ação, entidade ou tabela, identificador do registro, detalhes e resultado.

## Cobertura
A tabela trilha_auditoria é criada durante _init_banco(). Gatilhos SQLite AFTER INSERT, AFTER UPDATE e AFTER DELETE registram operações nas tabelas existentes, exceto na própria trilha. Alterações incluem estados anterior e posterior.

Eventos de aplicação incluem autenticação bem-sucedida, falhas de autenticação, acesso administrativo, navegação nos módulos principais e encerramento normal da sessão.

## Credenciais
Colunas com nomes associados a senha, hash de senha, password, token ou secret são excluídas da captura. A senha digitada não é registrada. Falhas de autenticação registram o login informado e o resultado, nunca a senha.

Os detalhes podem conter dados pessoais e informações funcionais. Restrinja o acesso ao banco e à consulta.

## Limitações
A trilha reside no mesmo arquivo SQLite. Não é inviolável: alguém com permissão de escrita no arquivo poderá alterar ou apagar eventos. Também não substitui serviço central de logs, armazenamento imutável ou segregação formal de funções.

Para requisitos institucionais mais rigorosos, encaminhe eventos a serviço externo com autenticação independente, retenção definida, controle de acesso e proteção contra alteração.

## Retenção
A consulta apresenta os 100 eventos mais recentes. Não há expurgo automático implementado nesta versão. Defina retenção conforme política institucional e mantenha backups protegidos.
