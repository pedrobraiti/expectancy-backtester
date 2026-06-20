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
