# Handoff — de onde parei

> **Propósito:** este arquivo serve para que um chat NOVO saiba com precisão "de onde eu parei",
> de forma relativamente detalhada. É o PRIMEIRO arquivo que a próxima sessão lê.
> Mantenha-o vivo e específico — detalhado o bastante para retomar sem reconstruir o raciocínio.

**Última atualização:** 2026-06-20 — setup concluído, iniciando o núcleo.

## Onde parei
Acabei de concluir o scaffolding `/setup`: `.claude/` (memória), `pyproject.toml`,
`requirements.txt`, `.gitignore/.gitattributes/.editorconfig`, `LICENSE`, venv `.venv`
(Python 3.12.10) com dependências já instaladas. Próximo passo é escrever o pacote
`src/expectancy/`.

## Contexto mental
Projeto = backtester de expectância seguindo o `BACKTEST_BRIEF.md` (que é completo e
detalhado). Decisões travadas com o usuário: cesta US+Brasil (SPY, QQQ, PETR4.SA, VALE3.SA,
ITUB4.SA), README rico + PDF técnico, idioma inglês, publicar repo público no GitHub.
Padrão de qualidade = espelhar os outros dois repos do usuário (src-layout, scripts/, README
profissional honesto, figuras commitadas).

## Próximo passo concreto
Escrever as camadas do pacote na ordem: `data/loader.py` → `strategy/` → `engine/` →
`metrics/` → `montecarlo/` → `reporting/`, depois `tests/`, depois `scripts/` e `main.py`.

## Em aberto / armadilhas
- Lookahead: sinal em t, execução na abertura de t+1 (CRÍTICO, §5.1).
- Custos aplicados em todo trade; risco fixo em % (não tamanho fixo); seed fixa no MC.
- Sanity check da expectância (fórmula vs trades) tem que bater — logar.
- `yfinance` pode falhar/rate-limit; cache em Parquet e retry.

## Como retomar rápido
- Ler `BACKTEST_BRIEF.md` (a especificação completa).
- `& ".venv\Scripts\Activate.ps1"`; `pytest -q`.
- Pipeline: `python scripts/run_study.py` → `python scripts/build_report.py`.
