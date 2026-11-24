# Checklist de release — versão 4.9.0

## Código e documentação
- [x] Script principal atualizado para 4.9.0.
- [x] Edição de cadastro de colaboradores documentada.
- [x] Auditoria, operação, arquitetura, checklist de validação e histórico atualizados.
- [x] Testes automatizados específicos para a edição cadastrados.
- [ ] Revisão final do diff e CI concluída.

## Validação local registrada
- [ ] Compilação sintática do script.
- [ ] Suíte automatizada integral executada.
- [ ] Suíte executada em todas as versões Python declaradas.
- [ ] Instalação do pacote testada em ambiente virtual limpo.

## Homologação funcional
- [ ] Edição com administrador e tentativa com usuário comum.
- [ ] Conferência dos campos, validações, motivo e confirmação.
- [ ] Conferência dos eventos UPDATE e ATUALIZACAO_CADASTRO.
- [ ] Preservação dos registros de férias e Banco de Horas.
- [ ] Conferência do comportamento dos relatórios após mudança de lotação.
- [ ] Login, logout, perfis, backup e restauração.
- [ ] Escalas especiais e demais rotinas.

## Publicação
- [ ] CI concluída com sucesso.
- [ ] Revisão final do diff.
- [ ] Tag/release criada após aprovação.

Compilação sintática e testes pontuais não comprovam o funcionamento integral. Não marque itens pendentes sem evidência.
