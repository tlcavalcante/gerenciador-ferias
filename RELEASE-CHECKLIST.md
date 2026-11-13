# Checklist de release — versão 4.8.2

## Código e documentação
- [x] Script autônomo atualizado.
- [x] Versão do código e metadados do pacote alinhados.
- [x] Documentação técnica, operacional, segurança e histórico revisados.
- [x] Trilha de auditoria documentada.
- [ ] Suíte automatizada integral executada em ambiente limpo.
- [ ] Compatibilidade validada em todas as versões Python declaradas.
- [ ] Instalação do pacote testada em ambiente virtual limpo.

## Homologação
- [ ] Login, logout, criação inicial de administrador e perfis.
- [ ] Inclusão, alteração e exclusão de cadastros.
- [ ] Agendamento, cancelamento e consulta de férias.
- [ ] Relatório de férias coincidentes e filtros.
- [ ] Lançamentos, ajustes, extratos, rankings e conciliação do Banco de Horas.
- [ ] Criação, alteração, consulta e exclusão de escalas especiais.
- [ ] Auditoria: usuário, data/hora, ação e estados anterior/posterior.
- [ ] Confirmar ausência de senhas, hashes e tokens na trilha.
- [ ] Controle de acesso à consulta de auditoria.
- [ ] Backup, restauração e atualização sobre banco preexistente.

## Publicação
- [ ] CI concluída com sucesso.
- [ ] Revisão final do diff.
- [ ] Tag/release criada após aprovação.

Compilação sintática e testes pontuais não comprovam o funcionamento integral. Não marque itens pendentes sem evidência.
