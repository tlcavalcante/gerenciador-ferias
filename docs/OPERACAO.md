# Guia de operação — versão 4.9.0

## Módulos
- Cadastros: funcionários, setores, subsetores e vínculos.
- Férias: agendamento, cancelamento, calendário e consultas.
- Banco de Horas: movimentações, ajustes, saldos e extratos.
- Relatórios: consultas de férias e Banco de Horas.
- Gráficos: evolução mensal de férias, comparações organizacionais, detalhamento individual e distribuição divergente dos saldos do Banco de Horas.
- Regras de férias: parâmetros por nível de abrangência.
- Validação, configurações e administração: validações, preferências, usuários, backup e auditoria.
- Escalas especiais: planejamento de cobertura em feriados prolongados, recessos e outras ocasiões.

## Alterar cadastro de colaborador

A alteração cadastral é restrita ao perfil administrador. Acesse **Cadastros > Funcionários > Alterar cadastro de colaborador** (opção 6). Selecione o colaborador e informe os novos valores para nome, setor, subsetor, vínculo e data de admissão.

- Pressione ENTER para manter o valor atual.
- No campo data de admissão, informe a data em DD/MM/AAAA; ENTER mantém a data existente e hífen remove a informação.
- Para vínculo, selecione uma opção cadastrada ou a opção 0 para deixar o colaborador sem vínculo.
- Nome, setor e subsetor são obrigatórios. O sistema impede nomes duplicados no mesmo setor/subsetor.
- Confira a comparação dos valores antes/depois, informe um motivo entre 5 e 1.000 caracteres e confirme a operação.

O sistema atualiza apenas o cadastro do colaborador. Os períodos de férias e os lançamentos de Banco de Horas são preservados. A alteração e os registros de auditoria são gravados na mesma transação SQLite. Ao alterar setor ou subsetor, os relatórios organizacionais passam a considerar a lotação atual também nas consultas históricas.

Consulte [EDICAO-CADASTRO-FUNCIONARIOS.md](EDICAO-CADASTRO-FUNCIONARIOS.md) para detalhes das regras e da trilha de auditoria.

## Seleção de funcionários
Todas as telas de seleção individual e múltipla utilizam a mesma identificação, na ordem: **Nome | Setor | Subsetor | Vínculo**. A seleção múltipla mantém esse padrão ao exibir os funcionários escolhidos, listar candidatos para inclusão e apresentar os registros disponíveis para remoção. Campos não preenchidos são indicados como “Sem setor”, “Sem subsetor” ou “Sem vínculo”.

## Gráficos de férias
No menu Gráficos, selecione uma das visões: empresa completa, por setor, por subsetor ou por funcionário. Em seguida, escolha a janela de 3, 6, 12 ou 24 meses. A opção vazia adota 12 meses e a opção 0 retorna.

- **Empresa completa:** mostra o total de dias de férias agendados por mês, quantidade de funcionários com férias no mês e pico diário de funcionários simultaneamente em férias. O resumo apresenta dias no período, meses ativos e média mensal.
- **Detalhamento por funcionário:** na visão da empresa, pressione `P` após o gráfico para abrir os meses com registros e consultar a participação de cada funcionário, ordenada por dias no mês.
- **Por setor:** apresenta os meses com registros de cada setor e usa a mesma escala máxima em todos os setores exibidos, permitindo comparação direta.
- **Por subsetor:** após selecionar o setor, apresenta os subsetores correspondentes usando uma escala comum dentro daquele setor.
- **Por funcionário:** compara dias de férias por mês e acumulado na janela. Quando aplicável, o resumo também exibe data de admissão e progresso do período aquisitivo.

A barra horizontal representa uma proporção do maior valor da escala da visão. O marcador `mês atual` identifica o mês corrente; meses sem registros podem ser omitidos em comparações organizacionais. As cores são auxiliares: consulte sempre valores e legendas. A largura das barras se ajusta à largura disponível do terminal.

## Gráfico do Banco de Horas
Em Relatórios do Banco de Horas, a opção **Gráfico completo de saldos** apresenta os funcionários em visão divergente: saldos negativos crescem para a esquerda do eixo central e saldos positivos para a direita. A extensão da barra é proporcional ao maior saldo absoluto da listagem. A ordenação segue o saldo, do maior para o menor, e a listagem respeita a preferência configurada para ocultar ou exibir saldos zerados. A legenda identifica as duas direções; a coluna de saldo mantém o valor em HH:MM.

## Férias coincidentes
O relatório compara períodos de funcionários diferentes no escopo selecionado. Cada ocorrência apresenta os funcionários, suas unidades, períodos originais, intervalo comum e quantidade de dias coincidentes. As datas inicial e final são consideradas no cálculo.

## Banco de Horas
Os valores são informados em HH:MM. Confira funcionário, data, sinal e justificativa antes de confirmar crédito, débito ou ajuste.

Na conciliação com relatório mensal, o sistema calcula e registra somente a diferença entre o saldo atual e o saldo informado. Exemplo: saldo atual +12:30, saldo informado +08:00, ajuste -04:30 e saldo resultante +08:00.

Os rankings apresentam posição, funcionário, unidade organizacional e saldo em formato compacto. O resumo e os indicadores ficam na tela inicial dos relatórios. A preferência para ocultar ou exibir saldos zerados é persistente.

## Escalas especiais
Cadastre a ocasião, intervalo e escopo. A situação pode ser trabalhou, não trabalhou ou pendente. Se a situação variar durante o intervalo, registre períodos distintos. Escalas não alteram automaticamente férias ou Banco de Horas.

## Trilha de auditoria
A consulta fica no menu Administração e exige perfil administrador. Exibe os eventos mais recentes, data/hora, usuário, ação, entidade, identificador e detalhes. Consulte [AUDITORIA.md](AUDITORIA.md) para cobertura e limitações.
