# Guia de operação — versão 4.8.2

## Módulos
- Cadastros: funcionários, setores, subsetores e vínculos.
- Férias: agendamento, cancelamento, calendário e consultas.
- Banco de Horas: movimentações, ajustes, saldos e extratos.
- Relatórios: consultas de férias e Banco de Horas.
- Regras de férias: parâmetros por nível de abrangência.
- Validação, configurações e administração: validações, preferências, usuários, backup e auditoria.
- Escalas especiais: planejamento de cobertura em feriados prolongados, recessos e outras ocasiões.

## Férias coincidentes
O relatório compara períodos de funcionários diferentes no escopo selecionado. Cada ocorrência apresenta os funcionários, suas unidades, períodos originais, intervalo comum e quantidade de dias coincidentes. As datas inicial e final são consideradas no cálculo.

## Banco de Horas
Os valores são informados em HH:MM. Confira funcionário, data, sinal e justificativa antes de confirmar crédito, débito ou ajuste.

Na conciliação com relatório mensal, o sistema calcula e registra somente a diferença entre o saldo atual e o saldo informado. Exemplo: saldo atual +12:30, saldo informado +08:00, ajuste -04:30 e saldo resultante +08:00.

Os rankings apresentam posição, funcionário, unidade organizacional e saldo em formato compacto. O resumo e os indicadores ficam na tela inicial dos relatórios. A preferência para ocultar ou exibir saldos zerados é persistente.

## Escalas especiais
Cadastre a ocasião, intervalo e escopo. A situação pode ser trabalhou, não trabalhou ou pendente. Se a situação variar durante o intervalo, registre períodos distintos. Escalas não alteram automaticamente férias ou Banco de Horas.

## Trilha de auditoria
A consulta fica no menu Administração e exige perfil administrador. Exibe os eventos mais recentes, data/hora, usuário, ação, entidade, identificador e detalhes. Consulte AUDITORIA.md para cobertura e limitações.
