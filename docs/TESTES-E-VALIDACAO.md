# Checklist de testes e validação — versão 4.8.5

## Limite da validação
A compilação sintática, os testes automatizados da suíte e a homologação interativa devem ser avaliados separadamente. Marque os itens somente após a respectiva execução. Testes de renderização com funções auxiliares não substituem inspeção no terminal utilizado na instalação.

## Gráficos e indicadores
- [ ] Evolução mensal da empresa: conferir dias agendados, meses ativos, média mensal, funcionários por mês e pico simultâneo.
- [ ] Selecionar janelas de 3, 6, 12 e 24 meses; confirmar mês corrente e navegação/retorno.
- [ ] Detalhamento `P`: conferir lista mensal de funcionários e ordenação por dias utilizados.
- [ ] Visão por setor: validar os totais e a mesma escala em todos os setores.
- [ ] Visão por subsetor: validar seleção do setor, subsetores disponíveis e escala comum dentro do setor.
- [ ] Visão individual: conferir dias por mês, acumulado, data de admissão e período aquisitivo quando aplicável.
- [ ] Indicadores de progresso: verificar zero, valor parcial, 100% e valor acima do limite.
- [ ] Gráfico do Banco de Horas: conferir saldo negativo à esquerda, saldo zero no eixo central e positivo à direita.
- [ ] Gráfico do Banco de Horas: testar escala com valores de magnitudes diferentes, filtro de saldos zerados e paginação.
- [ ] Inspecionar em terminal estreito e largo, com cores ANSI e com `NO_COLOR=1`.

## Testes automatizados do layout
- [x] Barra horizontal: largura fixa, proporção parcial, limite superior e valores negativos.
- [x] Barra horizontal: escala zero e valor inválido.
- [x] Barra divergente: sinal negativo, zero, positivo, eixo central e saturação pela escala.
- [x] Indicadores: quebra de linha conforme a largura do terminal.
- [ ] Executar a suíte integral em cada versão Python declarada no workflow.
- [ ] Construir e instalar o pacote em ambiente virtual limpo.

## Seleção de funcionários
- [ ] Todas as seleções individuais exibem nome, setor, subsetor e vínculo, nessa ordem e na mesma linha.
- [ ] Campos ausentes exibem os indicadores “Sem setor”, “Sem subsetor” e “Sem vínculo”.
- [ ] A seleção múltipla exibe os quatro campos ao mostrar os funcionários já selecionados.
- [ ] A lista de candidatos para inclusão exibe os quatro campos e mantém o marcador dos já selecionados.
- [ ] A lista de funcionários para remoção exibe os quatro campos.
- [ ] Selecionar todos, adicionar e remover funcionários preserva os IDs e a ordem escolhida.
- [ ] A escolha do funcionário continua retornando o registro correto após a mudança de apresentação.

## Preparação e autenticação
- [ ] Usar cópia isolada do banco e confirmar backup restaurável.
- [ ] Aplicativo inicia sem erro.
- [ ] Criação inicial de administrador e autenticação.
- [ ] Usuário sem perfil administrativo não acessa funções restritas.
- [ ] Login inválido é registrado sem armazenar senha.

## Cadastros e férias
- [ ] Inclusão, alteração e exclusão de funcionários, setores, subsetores e vínculos.
- [ ] Agendamento, cancelamento e consulta de férias.
- [ ] Validações de regras e limites.
- [ ] Relatórios por funcionário, setor, subsetor, período e situação.
- [ ] Férias coincidentes: filtros, datas e quantidade de dias.

## Banco de Horas
- [ ] Movimentações positivas e negativas preservam sinal e histórico.
- [ ] Ajuste por diferença calcula saldo final correto.
- [ ] Conciliação de +12:30 para +08:00 registra -04:30.
- [ ] Conciliação entre saldos positivos e negativos.
- [ ] Justificativa e confirmação exigidas.
- [ ] Rankings e indicadores apresentam valores coerentes.
- [ ] Preferência de ocultação de saldos zerados persiste após reiniciar.
- [ ] Alertas de saldo negativo e limite crítico.

## Escalas especiais
- [ ] Criar escala de data única e de intervalo.
- [ ] Selecionar escopo por empresa, setor, subsetor e funcionários.
- [ ] Marcar trabalhou, não trabalhou e pendente.
- [ ] Adicionar funcionários sem sobrescrever situações existentes.
- [ ] Conferir totais e cobertura por unidade.
- [ ] Excluir evento e conferir integridade referencial.

## Trilha de auditoria
- [ ] Inclusões, alterações e exclusões geram eventos.
- [ ] Usuário e data/hora são identificados.
- [ ] Alterações apresentam dados anteriores e posteriores.
- [ ] Login, falha de login, acesso administrativo e logout são registrados.
- [ ] Hashes, senhas e tokens não aparecem nos detalhes.
- [ ] Consulta restrita a administradores.
- [ ] Registros permanecem disponíveis após reiniciar.

## Dados e backup
- [ ] Banco e backups permanecem no diretório configurado.
- [ ] Backup criado e restaurado em base de teste.
- [ ] Atualização preserva dados existentes.
- [ ] Nenhum dado real incluído no repositório.

## Registro da homologação
Data:
Responsável:
Ambiente:
Versão anterior:
Versão testada:
Resultado: [ ] Aprovado [ ] Reprovado
Falhas/evidências:
