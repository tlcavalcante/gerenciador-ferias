# Procedimento de atualização

## Antes de atualizar
1. Identifique o diretório de dados: GERENCIADOR_FERIAS_DATA_DIR, XDG_DATA_HOME/gerenciador-ferias ou ~/.local/share/gerenciador-ferias.
2. Encerre o aplicativo e confirme que não há processo escrevendo no banco.
3. Faça backup de dados_ferias.db e do diretório backups/.
4. Guarde uma cópia do script anterior.
5. Registre versão anterior, horário e responsável.

## Validar
Execute python3 --version e python3 -m py_compile gerenciador_ferias.py. A compilação verifica sintaxe, não todas as funções. Execute o checklist de docs/TESTES-E-VALIDACAO.md em homologação com cópia do banco.

## Instalar
1. Substitua o script da instalação pelo arquivo aprovado gerenciador_ferias.py.
2. Preserve o diretório de dados existente.
3. Inicie o programa e valide autenticação, cadastros, férias, Banco de Horas, escalas e auditoria.
4. Confira se a trilha registra os eventos esperados.

## Reversão
Em caso de erro, encerre o aplicativo e restaure o script anterior. Restaure o banco somente se houver evidência de corrupção ou incompatibilidade, mantendo cópia do estado atual para análise. Reproduza o problema em homologação antes de nova tentativa.

## Proteção de dados
Use dados fictícios ou anonimizados nos testes. Não adicione ao Git banco, backups, exportações com nomes reais, logs sensíveis ou credenciais.
