# TODO

Plano vivo do projeto. Tarefas e subtarefas, marcadas conforme concluídas.

## Em progresso
<vazio — v1.2 entregue>

## Próximas
<vazio> (mudança de jogo real seria de DADOS: estratégia com mais sinais / timeframe menor / cesta
maior tratada como portfólio — gerar centenas/milhares de trades. O motor já está pronto pra isso.)

## Concluído
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
