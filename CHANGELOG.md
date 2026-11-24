# Histórico de versões

## 4.9.0 — Edição auditada de cadastro de colaboradores
- Inclui opção de edição de cadastro de colaboradores, disponível somente para administradores.
- Permite alterar nome, setor, subsetor, vínculo e data de admissão, com validação dos campos obrigatórios e da data.
- Impede nomes duplicados dentro do mesmo setor/subsetor, sem diferenciar maiúsculas e minúsculas.
- Exige justificativa e confirmação antes da gravação.
- Atualiza somente o registro do colaborador em transação SQLite, sem recriar períodos de férias ou lançamentos do Banco de Horas.
- Registra os estados anterior e posterior pelo gatilho UPDATE e grava evento ATUALIZACAO_CADASTRO com a justificativa.
- Mantém a atualização e os dois registros de auditoria na mesma transação, com rollback em caso de falha.
- Documenta o fluxo, os controles, as consequências para relatórios e os testes de homologação.

## 4.8.5 — Modernização dos gráficos e indicadores
- Atualiza a apresentação dos gráficos de evolução mensal de férias, com indicadores consolidados, barras proporcionais e sinalização do mês corrente.
- Mantém escala comum nas comparações por setor e por subsetor dentro do setor selecionado.
- Organiza a visão individual com comparação entre dias do mês e acumulado no período.
- Inclui detalhamento mensal da participação por funcionário.
- Atualiza o gráfico completo do Banco de Horas para visão divergente, com saldos negativos à esquerda, positivos à direita e escala pelo maior saldo absoluto.
- Padroniza visualmente as barras de progresso dos indicadores de férias.
- Acrescenta testes automatizados para proporção, limites, valores inválidos, eixo central e quebra dos indicadores conforme a largura do terminal.

## 4.8.3 — Padronização das telas de seleção de funcionários
- Unifica a identificação dos funcionários nas seleções individuais e múltiplas.
- Exibe nome, setor, subsetor e vínculo na mesma linha.
- Aplica o mesmo formato nas etapas de adicionar, revisar e remover funcionários da seleção múltipla.
- Centraliza a formatação em uma única função para evitar divergências entre telas.

## 4.8.2 — Consolidação visual dos relatórios do Banco de Horas
- Apresenta posição, funcionário, unidade organizacional e saldo em formato compacto nos rankings.
- Remove linhas horizontais entre os registros.
- Exibe resumo geral e indicadores na tela inicial dos relatórios do Banco de Horas.
- Preserva cálculos, filtros e critérios de ordenação.

## 4.8.1 — Ajustes de leitura dos relatórios
- Amplia o espaçamento entre os indicadores consolidados e os registros seguintes.

## 4.8.0 — Trilha de auditoria
- Registra inclusões, alterações e exclusões por gatilhos SQLite.
- Identifica usuário, nome, data/hora, ação, entidade e identificador do registro.
- Registra autenticação, falhas de autenticação, navegação e acesso administrativo.
- Armazena estados anterior e posterior nas alterações.
- Exclui campos de senha, hash, token e segredo.
- Restringe a consulta ao perfil administrador.

## 4.7.0 — Padronização dos relatórios
- Unifica a apresentação em blocos compactos, com agrupamento de informações e destaques de situação.

## 4.6.0 — Tema visual
- Atualiza paleta de cores, hierarquia visual e aproveitamento da largura do terminal.

## 4.5.0 — Escalas especiais
- Inclui escalas de feriados prolongados, recessos e outras ocasiões, com controle de situação e cobertura.

## 4.4.0 — Férias coincidentes
- Inclui relatório de sobreposição entre períodos de férias de funcionários diferentes.

## 4.3.9 — Organização do Banco de Horas
- Organiza menus, configurações, rankings e conciliação de saldo final.
