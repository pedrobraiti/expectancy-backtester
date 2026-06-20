# Handoff — de onde parei

> **Propósito:** este arquivo serve para que um chat NOVO saiba com precisão "de onde eu parei",
> de forma relativamente detalhada. É o PRIMEIRO arquivo que a próxima sessão lê.
> Mantenha-o vivo e específico — detalhado o bastante para retomar sem reconstruir o raciocínio.

**Última atualização:** 2026-06-20 — v2.1 ENTREGUE (ajustes finais da 3ª revisão).

## Onde parei
Projeto completo e publicado: https://github.com/pedrobraiti/expectancy-backtester (público).
v1.0 núcleo; v1.1 analysis/; v1.2 block bootstrap; v2.0 estudo powered (RSI, 2313 trades, resolve em
"edge ~0"). **v2.1 (esta sessão) = ajustes finais da 3ª revisão**: cost sweep pooled NO ESTUDO POWERED
→ achado gross-vs-net (gross +0,056R, breakeven slippage ~0,045: sinal real mas pequeno, só baixo custo
extrai); scorecard "Edge?"→"unconfirmed"; reshuffle→resample no PDF; IC pooled da tabela = block; nota
survivorship; Sharpe/ruína marcados instáveis a n<100; numeração de seções e capa corrigidas; glitch do
ruin chart. 48 testes, PDF 26 páginas. Falta commitar/pushar v2.1 (em andamento).
**ATENÇÃO push:** o remoto pode ter commits do usuário (ele já editou o README no GitHub — removeu
emojis decorativos; ver [[readme-no-decorative-emojis]]). Se `git push` falhar, `git fetch` + rebase
preservando a edição dele. NÃO usar emojis decorativos no README.

## Contexto mental
Backtester de expectância fiel ao `BACKTEST_BRIEF.md`. Estudo real (2010–2026, 0,5% risco/trade,
MA20×MA50, ATR 1,5/3,0) sobre SPY, QQQ, PETR4.SA, VALE3.SA, ITUB4.SA. Resultado honesto: a
estratégia de exemplo NÃO tem edge robusto — expectância troca de sinal (QQQ +0,42R, ITUB4 +0,22R,
VALE3 +0,04R, SPY −0,09R, PETR4 −0,11R) e TODA amostra tem < 100 trades (37–43), então o aviso de
ruído dispara em todas. O valor entregue é a metodologia: medir sem lookahead, com custos, sizing
por risco fixo, sanity check da expectância (passa em todos), variância (bootstrap) e risco de ruína
(explode a 5%/trade). README e PDF contam isso sem spin.

## Próximo passo concreto
Nenhum pendente. Possíveis evoluções FUTURAS se o usuário pedir: (a) adicionar estratégias novas em
`strategy/` (registrar em `registry.py`); (b) split in-sample/out-of-sample / walk-forward para
robustez; (c) análise "pooled" juntando trades de todos os ativos para passar de 100 trades; (d)
calculadora de lote forex já existe em `sizing.lot_size` mas não é exposta na CLI.

## Em aberto / armadilhas
- `yfinance` TEM que ser 1.4.1 (série 0.2.x falha com YFTzMissingError/JSON vazio). Fixado.
- Terminal precisa UTF-8 (`print_report` faz `sys.stdout.reconfigure`); rodar com PYTHONIOENCODING=utf-8 ajuda.
- `output/*` ignorado EXCETO `output/figures/` e `output/expectancy_study.pdf`. `study.pkl`,
  `data/cache`, `*.parquet`, `Prompt_Claude_Code.txt` ignorados.

## Como retomar rápido
- `& ".venv\Scripts\Activate.ps1"`; `pytest -q` (30 testes).
- Reproduzir: `python scripts/run_study.py` → `python scripts/build_report.py`.
- Um ativo: `python main.py --ticker QQQ`.
