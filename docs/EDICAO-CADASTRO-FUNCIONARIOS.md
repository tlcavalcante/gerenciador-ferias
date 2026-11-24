# Edição auditada do cadastro de colaboradores

## 1. Objetivo

Disponibilizar uma rotina controlada para corrigir e atualizar informações cadastrais de colaboradores sem excluir e recriar registros. A operação preserva os históricos vinculados ao identificador do colaborador e permite identificar quem realizou a alteração, quando ela ocorreu, quais dados foram modificados e por qual motivo.

A funcionalidade integra o módulo de cadastros e utiliza a trilha de auditoria mantida pelo banco SQLite.

## 2. Acesso e autorização

A funcionalidade é exclusiva do perfil administrador.

No menu Cadastros, opção Funcionários, o perfil administrador visualiza a opção 6 — Alterar cadastro de colaborador. Para os demais perfis, essa opção não é apresentada.

A autorização também é verificada na função de gravação. Chamar a rotina de persistência diretamente com uma sessão que não possua nível admin não permite alterar o banco.

## 3. Campos que podem ser alterados

| Campo | Regra |
|---|---|
| Nome | Obrigatório; não pode ficar vazio. |
| Setor | Obrigatório; deve corresponder a um setor cadastrado. |
| Subsetor | Obrigatório; deve pertencer ao setor selecionado. |
| Vínculo | Pode ser escolhido entre os vínculos cadastrados ou ficar sem vínculo. |
| Data de admissão | Opcional; deve ser uma data válida no formato DD/MM/AAAA. |

A tecla ENTER mantém o valor atual do campo. No campo de data de admissão, o hífen remove a informação. Para o vínculo, a opção 0 representa ausência de vínculo.

O sistema não permite concluir a edição quando o setor escolhido não possui subsetores cadastrados.

## 4. Validações

Antes de gravar, a rotina aplica as seguintes validações:

- a sessão deve pertencer ao perfil administrador;
- o colaborador selecionado deve possuir identificador persistido;
- nome, setor e subsetor não podem ficar vazios;
- setor e subsetor devem ser selecionados a partir dos cadastros disponíveis;
- a data de admissão, quando informada, deve ser válida;
- não pode existir outro colaborador com o mesmo nome no mesmo setor/subsetor;
- a comparação de nomes não diferencia letras maiúsculas e minúsculas;
- o motivo da alteração é obrigatório e deve conter entre 5 e 1.000 caracteres;
- a alteração exige confirmação explícita.

A verificação de duplicidade é realizada na interface e repetida durante a transação no banco. A rotina também compara os dados carregados em memória com os dados atuais do banco. Se outro processo tiver alterado o cadastro desde a seleção, a operação é cancelada e o administrador deve reabrir a edição, evitando sobrescrever silenciosamente uma alteração mais recente.

## 5. Fluxo operacional

1. O administrador acessa Cadastros e seleciona Funcionários.
2. Escolhe a opção Alterar cadastro de colaborador.
3. Seleciona o colaborador que será atualizado.
4. Informa os novos valores. ENTER mantém os valores atuais.
5. O sistema valida os campos, a data, a lotação e a eventual duplicidade.
6. Uma tela apresenta somente os campos modificados, com valor anterior e valor novo.
7. O sistema informa que os históricos de férias e Banco de Horas serão preservados.
8. Se houver mudança de setor ou subsetor, é exibido um alerta sobre os relatórios por unidade organizacional.
9. O administrador informa o motivo da alteração.
10. Após a confirmação, o sistema atualiza o cadastro e registra os eventos de auditoria.

Cancelar na etapa de confirmação não realiza gravação.

## 6. Persistência e integridade

A rotina executa BEGIN IMMEDIATE para iniciar uma transação de escrita no SQLite. Em seguida, consulta novamente o registro pelo seu identificador e valida se os dados armazenados permanecem iguais aos dados originalmente carregados.

A atualização é feita diretamente na linha correspondente da tabela funcionarios. A rotina não utiliza a função geral de salvamento dos cadastros, pois esse mecanismo poderia regravar registros de férias ou outras entidades sem relação com a edição.

A instrução UPDATE modifica apenas os campos cadastrais permitidos. O identificador do colaborador não é alterado.

Os registros das tabelas ferias e banco_horas continuam associados ao mesmo funcionario_id. Não há exclusão, recriação, transferência ou recálculo dos lançamentos históricos durante a edição.

A atualização e os eventos de auditoria são confirmados em um único commit. Se qualquer etapa falhar, a transação é revertida.

## 7. Registros de auditoria

A operação produz dois registros complementares na tabela trilha_auditoria.

### 7.1 Evento automático UPDATE

O gatilho AFTER UPDATE da tabela funcionarios registra:
- ação UPDATE;
- entidade funcionarios;
- identificador do colaborador em registro_id;
- estado anterior e estado posterior dos campos;
- data/hora local com fuso;
- usuário identificado pela sessão;
- resultado OK.

### 7.2 Evento explícito ATUALIZACAO_CADASTRO

A rotina grava um segundo evento com ação ATUALIZACAO_CADASTRO e entidade funcionarios. O campo detalhes contém:
- motivo informado pelo administrador;
- nome do colaborador após a alteração;
- lista dos campos efetivamente alterados;
- valor anterior e valor posterior de cada campo;
- indicação de preservação dos históricos de ferias e banco_horas.

O evento mantém o registro_id do colaborador, o identificador do usuário quando disponível, login, nome, data/hora e resultado da operação.

Os dois eventos são escritos na mesma transação da atualização cadastral. Assim, a operação não é confirmada sem que os registros de auditoria correspondentes também sejam confirmados.

## 8. Efeito das mudanças de lotação nos relatórios

A alteração de setor ou subsetor muda a lotação cadastral atual do colaborador. Os registros históricos de férias e Banco de Horas permanecem intactos, mas os relatórios organizacionais que consultam a lotação atual passam a apresentar o colaborador no setor/subsetor atual, inclusive em consultas sobre períodos anteriores.

Esse comportamento não representa reclassificação dos lançamentos originais. É uma consequência do relacionamento histórico pelo identificador do colaborador e da utilização dos dados cadastrais atuais para agrupar os relatórios.

Quando for necessário preservar a lotação histórica por período, será necessário um modelo próprio de histórico de movimentações funcionais, fora do escopo desta rotina.

## 9. Tratamento de erros e cancelamentos

A rotina não grava alterações quando:
- o usuário não é administrador;
- o cadastro não existe ou não possui identificador;
- os dados em memória estão desatualizados;
- há duplicidade de nome no setor/subsetor;
- os campos obrigatórios ou a data são inválidos;
- o motivo não atende ao tamanho permitido;
- a confirmação não é positiva;
- ocorre erro durante a transação.

Em falha durante a persistência, o sistema executa rollback, fecha a conexão e informa o erro. O evento automático e o evento explícito também são revertidos, pois pertencem à mesma transação.

## 10. Testes e homologação

Os testes automatizados verificam:
- restrição de acesso para usuário comum;
- atualização dos campos permitidos;
- rejeição de duplicidade, inclusive com diferença de caixa;
- registro dos estados anterior e posterior no evento UPDATE;
- evento ATUALIZACAO_CADASTRO com motivo e identificador;
- preservação dos identificadores e dos registros de férias e Banco de Horas;
- rejeição de justificativa insuficiente.

A homologação operacional deve ser feita com cópia isolada do banco, utilizando um administrador de teste. Antes de atualizar uma instalação em produção, faça backup e verifique se o arquivo de banco pode ser restaurado.

## 11. Considerações de segurança

Os registros de auditoria podem conter dados pessoais e funcionais. O acesso à consulta deve permanecer restrito ao perfil administrador e o arquivo SQLite deve ter permissões adequadas no sistema operacional.

A trilha armazenada no mesmo arquivo do banco não é inviolável. Uma pessoa com permissão de escrita no arquivo poderá alterar ou remover registros. Para requisitos de auditoria mais rigorosos, encaminhe os eventos para serviço externo com controle de acesso independente, retenção definida e proteção contra alteração.
