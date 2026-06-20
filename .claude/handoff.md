# Handoff — de onde parei

> **Propósito:** este arquivo serve para que um chat NOVO saiba com precisão "de onde eu parei",
> de forma relativamente detalhada. É o PRIMEIRO arquivo que a próxima sessão lê.
> Mantenha-o vivo e específico — detalhado o bastante para retomar sem reconstruir o raciocínio.

**Última atualização:** 2026-06-20 — núcleo + reporting + estudo rodado. Falta README e push.

## Onde parei
Núcleo, testes (30 passando), reporting (terminal + 32 figuras + PDF de 19 páginas) e pipeline
estão prontos e commitados. O estudo da cesta US+BR rodou de verdade (dados reais do Yahoo,
cacheados em `data/cache`), gerou `output/study.pkl`, todas as figuras em `output/figures/` e
`output/expectancy_study.pdf`. Próximo passo é escrever o README profissional em inglês com os
números reais e depois publicar o repo público no GitHub.

## Contexto mental
Resultados reais (2010–2026, 0,5% risco/trade, MA20×MA50, ATR 1,5/3,0): amostras pequenas
(37–43 trades cada, TODAS < 100 → aviso de ruído dispara, que é exatamente a lição do brief).
Expectância troca de sinal entre ativos: QQQ +0,42R (PF 1,83), ITUB4 +0,22R (PF 1,40),
VALE3 +0,04R (marginal), SPY −0,09R e PETR4 −0,11R (negativos). Narrativa honesta: a estratégia
de exemplo NÃO tem edge robusto; o valor do projeto é a metodologia (medir expectância sem
lookahead, com custos, e mostrar variância + risco de ruína). Sanity check da expectância passa
em todos. Risco de ruína só explode a 5%/trade (SPY 37%, PETR4 38%).

## Próximo passo concreto
Escrever `README.md` em inglês: badges, TL;DR honesto, tabela comparativa (extrair do
`output/study.pkl`), figuras embutidas (`output/figures/*.png`), seção de método (sem lookahead,
custos, sizing), como reproduzir, estrutura, disclaimer. Espelhar o tom dos outros 2 repos.

## Em aberto / armadilhas
- `yfinance` tem que ser 1.4.1 (0.2.x falha). Já corrigido no requirements.
- Output no terminal precisa de UTF-8 (`print_report` faz `sys.stdout.reconfigure`).
- `output/*` é ignorado no git EXCETO `output/figures/` e `output/expectancy_study.pdf`
  (commitados). `study.pkl`, `data/cache`, `*.parquet` ignorados.
- Datas: `build_report.py` usa `date.today()` (ok em script normal).

## Como retomar rápido
- `& ".venv\Scripts\Activate.ps1"`; `pytest -q` (30 testes).
- Reproduzir: `python scripts/run_study.py` → `python scripts/build_report.py`.
- Números para o README: `python -c "import pickle; b=pickle.load(open('output/study.pkl','rb'))"`.
- Publicar: `gh repo create expectancy-backtester --public --source=. --remote=origin --push`.
