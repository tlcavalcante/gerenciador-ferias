# Gerenciador de Férias — versão 4.8.2

Aplicação CLI em Python para gestão de férias, escalas especiais e Banco de Horas, com persistência local em SQLite.

## Requisitos e execução
- Python 3.9 ou superior.
- Linux/Unix e terminal UTF-8 recomendados.
- SQLite da biblioteca padrão; nenhuma dependência externa para executar o script autônomo.

Execute com: python3 gerenciador_ferias.py

Na primeira execução, cadastre o administrador quando solicitado. Não existe senha administrativa padrão.

## Funcionalidades
### Férias
- Cadastro de funcionários, setores, subsetores e vínculos.
- Agendamento, cancelamento, regras e validações.
- Calendário e relatórios por funcionário, setor, subsetor e período.
- Relatório de férias coincidentes, com funcionários envolvidos, períodos originais e intervalo de sobreposição.

### Banco de Horas
- Lançamentos de crédito, débito e ajuste em HH:MM.
- Saldos positivos e negativos, extratos, relatórios e rankings.
- Conciliação com saldo final de relatório mensal, registrando somente a diferença e preservando o histórico.
- Indicadores na tela inicial dos relatórios e preferência para ocultar/exibir saldos zerados.
- Limite configurável para alertas de saldo crítico.

### Escalas especiais
- Cadastro de feriados prolongados, recessos e outras ocasiões, em data única ou intervalo.
- Seleção por empresa, setor, subsetor ou funcionários.
- Situações: trabalhou, não trabalhou ou pendente.
- Relatório de cobertura por unidade organizacional.

### Administração
- Gestão de usuários, perfis e backups.
- Trilha de auditoria com data/hora, usuário, ação, entidade, identificador e detalhes das alterações.
- Consulta da trilha restrita a administradores.

## Dados e backup
O diretório de dados é determinado nesta ordem: variável GERENCIADOR_FERIAS_DATA_DIR; diretório XDG_DATA_HOME/gerenciador-ferias; ou ~/.local/share/gerenciador-ferias.

O banco principal é dados_ferias.db e os backups ficam em backups/.

Não publique banco de dados, backups, exportações com dados reais de funcionários, logs ou credenciais no Git. Antes de atualizar, faça backup e siga docs/ATUALIZACAO.md.

## Documentação
- Arquitetura: ARCHITECTURE.md
- Operação: docs/OPERACAO.md
- Atualização e reversão: docs/ATUALIZACAO.md
- Testes e validação: docs/TESTES-E-VALIDACAO.md
- Segurança e backup: docs/SEGURANCA-E-BACKUP.md
- Trilha de auditoria: docs/AUDITORIA.md
- Histórico: CHANGELOG.md
- Checklist de release: RELEASE-CHECKLIST.md

## Testes
A compilação sintática pode ser verificada com python3 -m py_compile gerenciador_ferias.py. Isso não substitui os testes funcionais e a homologação descritos em docs/TESTES-E-VALIDACAO.md.

## Licença
MIT. Consulte LICENSE.
