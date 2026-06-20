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

## 2026-06-20 — v1.1: camada `analysis/` (significância, pooling, custo) após revisão externa
**Motivo:** uma IA revisora apontou (com razão) que (a) a conclusão "não tem edge" não é sustentada
pela amostra — com ~40 trades o spread de expectância é compatível com ruído sobre edge zero; o
honesto é "underpowered, não distinguível de zero"; (b) o termo "reshuffle" no README estava errado —
o código já fazia bootstrap COM REPOSIÇÃO (correto), pois sob sizing fracionário permutar não dispersa
o destino (produto comutativo); (c) edge fino é frágil a custo; (d) faltava OOS. Adicionado:
`analysis/significance.py` (CI bootstrap 95% da expectância em R), `analysis/pooled.py` (agrega ~201
trades de todos os ativos + split temporal in/out-of-sample), `analysis/cost_sensitivity.py` (varre
slippage). Conclusão recalibrada para "não dá para confirmar nem refutar o edge nesta amostra".
**Resultado-chave:** TODOS os CIs (inclusive o pooled, [−0,11R, +0,30R]) cruzam zero. OOS (+0,32R) >
in-sample (−0,14R), então não é overfit clássico — provavelmente exposição de regime pós-2020.
**Alternativas consideradas:** walk-forward completo — rejeitado por inutilidade com ~40 trades/ativo
(folds teriam ~10 trades); o split pooled in/out é o OOS honesto possível nesta amostra.

## 2026-06-20 — v1.2: block bootstrap no pooled (2ª rodada de revisão externa)
**Motivo:** a revisora apontou (corretamente) que o pooling tratava os 201 trades como IID, mas eles
NÃO são independentes — SPY/QQQ ~0,9 correlacionados, e os 3 BR andam juntos. Bootstrap IID destrói
a correlação e SUBESTIMA o erro padrão (N efetivo < 201, IC real mais largo). Não muda a conclusão,
mas o relatório estava sub-reportando a própria incerteza. Adicionado `cluster_bootstrap_mean_ci`
(reamostra clusters = trimestres-calendário, preservando a dependência; mean exato via somas/contagens
de clusters). Pooled agora reporta os DOIS ICs: IID [−0,11, +0,30] (otimista) e block [−0,14, +0,34]
(~20% mais largo, 58 trimestres, honesto). Ambos cruzam zero. Também: nota de comparações múltiplas
(1−0,95⁵≈23% de achar 1 de 5 a 95% por acaso) e QQQ rotulado como caso de fronteira. BCa documentado
como refinamento conhecido (não muda o veredito), não implementado.
**Alternativas consideradas:** block por instrumento (5 clusters) — coarse demais; trimestre-calendário
captura a correlação temporal e cross-sectional e dá N efetivo razoável (~58).

## 2026-06-20 — v2.0: estudo "powered" (RSI reversão + saída por sinal) p/ resolver a pergunta
**Motivo:** o usuário escolheu (após a 2ª revisão) o caminho de DADOS: dar trades suficientes pra
máquina de fato concluir, em vez de só polir estatística. Crossover diário dispara ~2,5x/ano →
estruturalmente sem poder. Solução: estratégia frequente + cesta grande, reusando o motor.
**O que mudou:** (1) Motor estendido para **saída por sinal** (coluna `exit` opcional → fecha na
abertura de t+1, lookahead-safe) + `max_holding_bars` — backward-compatible (default 0/sem exit =
comportamento idêntico ao crossover). (2) Indicador RSI (Wilder). (3) Estratégia `rsi_reversion`
(Connors RSI2: compra dip oversold em uptrend filtrado por SMA200, sai quando RSI recupera; stop ATR
define o R, sem alvo fixo). (4) `scripts/run_powered_study.py` sobre 20 ativos US+BR.
**Resultado-chave:** 2313 trades. Pooled expectância −0,005R, block CI **[−0,04, +0,03]** (vs crossover
[−0,14,+0,34]) — banda ESTREITA colada no zero. A pergunta RESOLVE: não é "não dá pra saber", é "edge
~0 após custos, com precisão". WR 60-68% nos índices US (assinatura real de reversão), mas custos comem
o ganho. IS (−0,001) ≈ OOS (−0,009). PETR4 vira significativamente negativo. Lição final: o gargalo era
o setup, não o motor.
**Alternativas consideradas:** MA mais rápida (mais trades mas ainda trend-following / provável ~0);
intraday (Yahoo só dá ~2 anos de dados intraday, inviável p/ 16 anos).

## 2026-06-20 — v2.1: ajustes finais da 3ª revisão externa
**Motivo:** revisão apontou itens corretos. Implementado: (1) **cost sweep pooled no estudo POWERED**
(o que dependia de custo era a tese do RSI, não o crossover) → achado gross-vs-net: **gross +0,056R**,
breakeven slippage **~0,045**; sinal é REAL mas pequeno, só um trader de baixo custo extrai. (2) Coluna
"Edge? YES/no" do scorecard contradizia a própria conclusão de significância (usava sinal do ponto
estimado) → trocada por "unconfirmed"/veredito do CI (README e PDF). (3) PDF tinha regredido pra
"Reshuffling" nas legendas de variância → "resampling with replacement" + nota didática. (4) IC pooled
da TABELA divergia do forest (tabela IID, forest block) → tabela agora usa block, com nota do IID.
(5) Nota de **survivorship** (cesta = sobreviventes de hoje; viés joga A FAVOR de achar edge, logo nulo
é conservador). (6) Sharpe/Sortino e % de ruína marcados como instáveis a n<100. (7) Numeração de
seções (pulava 9 por double-increment) e capa (só citava crossover) corrigidas; glitch do label do ruin
chart (headroom no ylim).
**Alternativas consideradas:** remover Sharpe/ruína de vez — preferi manter com aviso de instabilidade.
