# Checklist de testes e validação — versão 4.3.9

## Limite da validação

A compilação sintática foi verificada na preparação do pacote. Os testes funcionais completos não foram executados como parte da preparação. Marque os itens somente após executá-los em homologação.

## Preparação e autenticação

- [ ] Usar uma cópia isolada do banco, nunca a única cópia de produção.
- [ ] Confirmar backup restaurável.
- [ ] Aplicativo inicia sem erro.
- [ ] Criação do administrador inicial e autenticação funcionam.
- [ ] Usuário sem perfil administrativo não acessa funções restritas.

## Menus e relatórios

- [ ] Menu principal tem numeração sequencial e não apresenta opção independente “Painel de férias”.
- [ ] Submenu de validação/configurações/administração funciona.
- [ ] Relatórios de férias e Banco de Horas são acessíveis.
- [ ] Tabelas aparecem nos relatórios, não indiscriminadamente nas telas operacionais.
- [ ] Relatórios por funcionário, setor, subsetor, período e situação apresentam dados coerentes.

## Banco de Horas

- [ ] Movimentações positivas e negativas preservam sinal e histórico.
- [ ] Ajuste por diferença calcula saldo final correto.
- [ ] Conciliação de `+12:30` para `+08:00` registra `-04:30` e resulta em `+08:00`.
- [ ] Conciliação de saldo negativo para positivo e vice-versa é testada.
- [ ] Justificativa e confirmação são exigidas.
- [ ] Rankings gerais, positivos e negativos exibem todos os colaboradores elegíveis, sem limite Top 25.
- [ ] Preferência de ocultar saldos zerados persiste após sair e reabrir os relatórios.
- [ ] Com a preferência ativa, saldos zerados são suprimidos de relatórios/rankings aplicáveis; desativada, são exibidos.
- [ ] Saldos negativos e no/acima do limite crítico são destacados em vermelho.
- [ ] Tabela de saldos funciona para todos os funcionários e filtros por setor/subsetor.

## Dados e backup

- [ ] Banco e backups permanecem no diretório configurado.
- [ ] Backup é criado e restaurado em base de teste.
- [ ] Nenhum dado real de produção foi incluído no repositório.

## Registro

- Data:
- Responsável:
- Ambiente:
- Versão anterior:
- Versão testada:
- Resultado: [ ] Aprovado [ ] Reprovado
- Falhas/evidências:
