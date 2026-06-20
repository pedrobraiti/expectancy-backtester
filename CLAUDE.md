# Instruções para o Claude neste projeto

## Memória persistente

Ao iniciar **qualquer** conversa neste projeto, antes de agir:
1. Leia `.claude/handoff.md` **PRIMEIRO** — é o ponteiro mais fresco: responde "de onde parei" com detalhe.
2. Leia `.claude/context.md` para o estado macro/estável do projeto.
3. Leia `.claude/todo.md` para saber o que está em progresso e o que vem a seguir.
4. Rode `git log --oneline -20` para ver atividade recente.
5. Se a tarefa tocar em área sensível/arquitetural, leia `.claude/decisions.md`.

### Manter o handoff vivo

O `.claude/handoff.md` é o que permite a **próxima sessão começar de onde esta parou**. Trate-o como documento vivo:
- Ao concluir qualquer passo significativo (não só no fim da sessão), atualize-o.
- Escreva com detalhe suficiente para um chat novo retomar sem reconstruir seu raciocínio: onde parou, o contexto mental, o próximo passo concreto e o que está em aberto.
- Atualize a data e **sobrescreva** o conteúdo antigo — ele reflete sempre o ESTADO ATUAL de "onde paramos", não é histórico append-only (esse papel é do git e do `decisions.md`).

## Disciplina do TODO

- O `.claude/todo.md` é **mandatório** e deve sempre refletir a realidade do projeto.
- Ao sair do planning mode (ou após planejar qualquer coisa com o usuário), atualize o TODO com tarefas e subtarefas granulares.
- Marque `[x]` a subtarefa **no mesmo commit** em que ela é concluída.
- Subtarefas devem ser pequenas e modulares — se uma não cabe em um commit, quebra em menores.

## Disciplina de commits

- Sempre que uma subtarefa do TODO for **concluída** (não trabalho intermediário), faça um commit.
- Use **Conventional Commits**: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`, `style:`.
- Mensagens claras, no imperativo, descrevendo o **porquê** quando não óbvio.
- **Nunca** inclua `Co-Authored-By: Claude` nas mensagens de commit.
- Antes de cada commit, avalie e atualize **no mesmo commit** se necessário:
  - `.claude/handoff.md` (de onde parei — detalhado, refletindo o estado atual).
  - `.claude/todo.md` (marcar subtarefa concluída).
  - `.claude/context.md` (estado atual mudou?).
  - `.claude/decisions.md` (houve decisão arquitetural nova?).
  - `README.md` (mudou stack, dependências, forma de rodar?).
  - `.env.example` (adicionou/removeu variável em `.env`? espelha aqui sem valores).

## Arquitetura

Camadas separadas e plugáveis, fiéis ao `BACKTEST_BRIEF.md`:
**dados** (`data/`) → **estratégia** (`strategy/`) → **simulação** (`engine/`) →
**métricas** (`metrics/`) → **variância/ruína** (`montecarlo/`) → **relatório** (`reporting/`).
Os números são *resultados* da simulação, nunca dados baixados. Seguir
`~/.claude/rules/BEST_PRACTICES.md` (código profissional, modular, testável).

### Regras de ouro do backtest (não violar)
- **Sem lookahead:** sinal no fechamento de `t`, execução na abertura de `t+1`.
- **Custos** em todo trade (spread + comissão + slippage).
- **Risco fixo em %** do capital, não tamanho de posição fixo.
- **Seed fixa** no Monte Carlo (reprodutibilidade).
- **Sanity check** da expectância: fórmula `WR×ganho − LR×perda` tem que bater com a média real.
- Avisar quando a amostra tiver < ~100 trades.

## Autonomia

Neste projeto você tem autonomia ampliada — use com critério profissional (autonomia controlada, não automática). Delegue buscas amplas a subagentes (`Explore`/`Plan`/`general-purpose`) quando fizer sentido. Instale skills úteis **sempre local** (`npx skills add <owner/repo> --skill <nome> --copy -y`), nunca global.
