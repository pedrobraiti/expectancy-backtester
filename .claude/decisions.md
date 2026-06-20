# Decisões arquiteturais/técnicas

Registro de decisões com o "porquê". Append-only — não edita entradas antigas.

<!-- Formato:
## YYYY-MM-DD — Título curto da decisão
**Motivo:** por que foi decidido assim.
**Alternativas consideradas:** o que ficou de fora e por quê.
-->

## 2026-06-20 — Layout `src/expectancy/` em vez do `backtester/` plano do brief
**Motivo:** o usuário pediu o mesmo padrão profissional dos outros dois repos
(`volume-profile-trading`, `capital-asset-pricing-model`), que usam src-layout com pacote
instalável (`pip install -e .`), submódulos por domínio e `pyproject.toml`. Mantém o código
testável e importável sem hacks de `sys.path`.
**Alternativas consideradas:** estrutura plana `backtester/*.py` do brief — rejeitada por não
casar com o bar de qualidade dos repos de referência.

## 2026-06-20 — Escopo: cesta US + Brasil
**Motivo:** rodar a mesma estratégia em SPY, QQQ, PETR4.SA, VALE3.SA, ITUB4.SA dá um relatório
comparativo muito mais rico (mostra onde a expectância aparece/some) e replica a abordagem dos
repos anteriores. Decisão do usuário.
**Alternativas consideradas:** só PETR4.SA (default do brief) — fiel ao critério de aceite
literal, mas relatório pobre.

## 2026-06-20 — Entregáveis: README rico + PDF técnico (reportlab)
**Motivo:** igualar o bar dos repos públicos do usuário. Terminal report e PNGs são o mínimo do
brief; README com figuras embutidas + PDF técnico é o padrão profissional esperado.

## 2026-06-20 — Execução em t+1 na abertura (sem lookahead)
**Motivo:** §5.1 do brief — o erro nº 1 de backtest. Sinal gerado no fechamento da barra t,
execução na abertura de t+1. Stops/alvos checados barra a barra com prioridade conservadora
(se o candle toca stop e alvo no mesmo dia, assume o pior caso = stop primeiro).
**Alternativas consideradas:** execução no mesmo close (infla resultado, proibido pelo brief).
