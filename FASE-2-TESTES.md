# Fase 2 — Testes do núcleo de regras de negócio

## Objetivo

A Fase 2 cria uma camada inicial de testes automatizados para congelar o comportamento atual das principais regras de negócio antes da refatoração arquitetural.

## Cobertura criada

Os testes cobrem:

- cálculo inclusivo de dias de férias;
- validação de datas inválidas;
- detecção de sobreposição de períodos;
- adição/subtração de meses, incluindo fim de mês e ano bissexto;
- cálculo do período aquisitivo atual;
- cálculo de dias dentro de um período aquisitivo;
- cálculo de dias dentro de um ano civil;
- geração de períodos aquisitivos;
- precedência de regras: subsetor → setor → vínculo → global;
- período mínimo de férias;
- limite máximo de dias;
- limite máximo de períodos;
- férias simultâneas no mesmo subsetor;
- limite de funcionários simultâneos;
- antecedência mínima;
- auditoria de venda de férias;
- auditoria de excesso de períodos e dias.

## Resultado

Execução realizada com Python 3.13.5:

```text
22 passed in 0.76s
```

Também foi executada análise de cobertura:

```text
TOTAL  2025 statements  1701 missed  16%
```

A cobertura de 16% é esperada nesta etapa. O objetivo agora não é obter alta cobertura da aplicação inteira, mas criar uma suíte confiável para o núcleo de regras antes da separação dos módulos.

## Observação importante

Durante a primeira execução, um teste assumia que uma admissão em 01/01/2025 ainda estaria no primeiro período aquisitivo. A execução revelou que, na data atual do ambiente, o sistema corretamente considera o período iniciado em 01/01/2026 como o período atual. O teste foi corrigido para refletir o comportamento real da função.

Esse resultado é precisamente o motivo de criar os testes antes da refatoração: o teste deve documentar o comportamento efetivamente implementado, e não uma expectativa criada fora do código.

## Próxima etapa

Com os 22 testes passando, a próxima fase pode extrair o motor de regras para módulos independentes, preservando os testes como rede de segurança.
