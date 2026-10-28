# Segurança, dados e backup

## Proteção dos dados

O aplicativo armazena informações de funcionários localmente em SQLite; trate-as como informações pessoais.

- Use senha administrativa forte e exclusiva. Não há senha padrão.
- Não compartilhe contas e não guarde credenciais no repositório.
- Restrinja as permissões do diretório de dados e dos backups.
- Não versione banco de dados, backups, relatórios com nomes reais ou logs sensíveis.
- Armazene cópias de segurança em local separado e protegido, conforme a política institucional.
- Teste periodicamente a restauração.

## Diretório de dados

A aplicação prioriza `GERENCIADOR_FERIAS_DATA_DIR`, depois `$XDG_DATA_HOME/gerenciador-ferias` e, por padrão, `~/.local/share/gerenciador-ferias`. Confirme o caminho real antes de iniciar o backup.

## Rotina recomendada

1. Feche o aplicativo antes de uma cópia simples do banco.
2. Copie `dados_ferias.db` e o diretório `backups/` para local protegido.
3. Mantenha cópias fora do diretório do código e fora do Git.
4. Defina retenção compatível com a política institucional.
5. Teste a restauração em ambiente isolado.
6. Remova cópias temporárias conforme a política institucional.

## Atualização

Valide novas versões em homologação. Preserve o script anterior e um backup restaurável do banco para permitir reversão. Não publique informações pessoais em issues, logs de CI, screenshots ou exemplos.

Este documento complementa, mas não substitui, as políticas institucionais de segurança, privacidade, retenção e continuidade.
