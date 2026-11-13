# Segurança, dados e backup

O aplicativo armazena informações de funcionários e registros funcionais em SQLite. Trate banco, backups e trilha de auditoria como informações de acesso restrito.

- Utilize senha administrativa forte e exclusiva.
- Não compartilhe contas.
- Restrinja permissões do diretório de dados e dos backups.
- Não versione banco, backups, exportações com nomes reais ou logs.
- Armazene cópias em local separado e protegido.
- Teste periodicamente a restauração.
- Aplique política institucional de retenção e descarte.

## Diretório de dados
A aplicação prioriza GERENCIADOR_FERIAS_DATA_DIR, depois XDG_DATA_HOME/gerenciador-ferias e, por padrão, ~/.local/share/gerenciador-ferias. Confirme o caminho antes do backup.

## Rotina recomendada
1. Encerre o aplicativo antes de cópia simples do banco.
2. Copie dados_ferias.db e backups/ para local protegido.
3. Mantenha cópias fora do código e do Git.
4. Defina retenção conforme política institucional.
5. Teste restauração em ambiente isolado.
6. Remova cópias temporárias conforme política aplicável.

## Atualização
Valide novas versões em homologação. Preserve o script anterior e backup restaurável. Não publique informações pessoais em issues, logs de CI ou capturas de tela.

Este documento complementa, mas não substitui, as políticas institucionais de segurança, privacidade, retenção e continuidade.
