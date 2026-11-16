# Checklist de release — versão 4.8.5

## Código e documentação
- [x] Script autônomo atualizado para 4.8.5.
- [x] Cabeçalho, constante `APP_VERSION` e metadados do pacote alinhados.
- [x] Gráficos de evolução mensal e gráfico divergente do Banco de Horas documentados.
- [x] Guia operacional, checklist de validação e histórico de versões atualizados.
- [x] Testes automatizados de layout dos gráficos adicionados.
- [ ] Revisão final do diff e CI concluída.

## Validação local registrada
- [x] Compilação sintática do script.
- [x] Testes pontuais de barras horizontais e divergentes.
- [x] Teste de quebra dos indicadores conforme a largura configurada.
- [x] Testes automatizados locais executados (8 testes).
- [ ] Suíte executada em todas as versões Python declaradas.
- [ ] Instalação do pacote testada em ambiente virtual limpo.

## Homologação funcional
- [ ] Conferir gráficos em terminal real, com diferentes larguras e configurações de cor.
- [ ] Conferir evolução da empresa, detalhe mensal, setores, subsetores e funcionários.
- [ ] Conferir gráfico divergente com saldos positivos, negativos e zerados.
- [ ] Conferir cálculos, filtros, paginação e ordenação do Banco de Horas.
- [ ] Revalidar seletores de funcionários, cadastros e férias.
- [ ] Login, logout, perfis, backup e restauração.
- [ ] Escalas especiais e trilha de auditoria.

## Publicação
- [ ] CI concluída com sucesso.
- [ ] Revisão final do diff.
- [ ] PR aprovado e integrado.
- [ ] Tag/release criada após aprovação.

Compilação sintática e testes pontuais não comprovam o funcionamento integral. Não marque itens pendentes sem evidência.
