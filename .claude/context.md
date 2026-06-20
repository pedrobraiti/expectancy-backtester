# Contexto do projeto

> Camada **estável** da memória: o que o projeto é e suas características macro. Muda devagar.
> O detalhe volátil de "de onde parei" fica no `handoff.md`; as tarefas, no `todo.md`;
> as decisões com o porquê, no `decisions.md`.

**Nome:** expectancy
**Descrição:** Backtester de estratégias de trading que mede a "ficha matemática" de um sistema — expectância, variância, tradeoff risco/recompensa e risco de ruína — sobre OHLCV histórico do Yahoo Finance.
**Stack:** Python 3.12, pandas, numpy, scipy, yfinance, matplotlib, reportlab, pyyaml, pytest.

## Visão geral
Pega o preço histórico de um ativo (via Yahoo Finance), roda uma estratégia de regras
plugável e simula trade a trade — sem viés de lookahead, com custos e position sizing por
risco fixo em %. A partir dos trades calcula win rate, expectância (em $ e em R), profit
factor, drawdown e, via Monte Carlo (bootstrap), variância, risco de ruína e a matemática
da recuperação. O objetivo é separar claramente **dados** (matéria-prima OHLCV) de
**resultados** (calculados pela simulação), e mostrar honestamente o que a variância
esconde. Para quem quer entender se uma estratégia tem edge real.

## Fase atual
Entregue (v1.0): núcleo, estudo da cesta US+Brasil, figuras, PDF e README publicados.

## Restrições e bloqueios de longo prazo
- Dados gratuitos do `yfinance` (endpoints não-oficiais do Yahoo; podem quebrar sem aviso).
- Estratégia de exemplo (MA-crossover) é didática, não um sistema com edge garantido.
- A matemática só vale se a estratégia tiver expectância positiva real — o backtester mede
  o edge, não o cria.
