# TODO

Plano vivo do projeto. Tarefas e subtarefas, marcadas conforme concluídas.

## Em progresso
<vazio — v2.1 entregue (ajustes finais da 3ª revisão)>

## Próximas
<vazio> (refinamentos opcionais: BCa bootstrap; intraday se houver fonte; walk-forward com reotimização)

## Concluído
- [x] v2.1: 3ª revisão — cost sweep pooled no estudo POWERED (gross +0,056R, breakeven slippage ~0,045),
      scorecard "Edge?"→"unconfirmed" (parar de contradizer significância), reshuffle→resample no PDF,
      IC pooled da tabela = block, nota de survivorship, instabilidade Sharpe/ruína a n<100, numeração
      de seções e capa corrigidas, glitch do ruin chart. 48 testes.
- [x] v2.0: estratégia RSI(2) reversão + saída por sinal no motor + estudo powered (20 ativos, 2313
      trades) → IC pooled colapsa pra [−0,04,+0,03], resolve a pergunta (~0 edge após custos). 47 testes
- [x] v1.2: block bootstrap no pooled (correlação) + comparações múltiplas + QQQ fronteira (41 testes)
- [x] v1.1: camada analysis/ (CI bootstrap, pooling+OOS, sensibilidade ao custo) após revisão externa
- [x] Recalibrar conclusão "sem edge" → "underpowered, não distinguível de zero" + corrigir termo bootstrap
- [x] Publicar repo público: https://github.com/pedrobraiti/expectancy-backtester
- [x] README profissional em inglês com resultados reais e figuras embutidas
- [x] Setup inicial do projeto (.claude/, CLAUDE.md, git, pyproject, venv, requirements)
- [x] Núcleo do backtester (data → strategy → engine → metrics → montecarlo)
- [x] Suíte de testes (pytest): lookahead, R, sanity da expectância, engine, métricas (30 testes)
- [x] Reporting: figuras (matplotlib) + relatório no terminal + PDF (reportlab, 19 páginas)
- [x] Pipeline `scripts/`: rodar cesta US+BR, cachear dados, gerar figuras + PDF
- [x] Fix yfinance 0.2.x → 1.4.1 (endpoints antigos rejeitados pelo Yahoo)
