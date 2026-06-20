# Brief para o Claude Code — Backtester de Estratégias

> **Objetivo:** construir, em Python, um backtester que pega o preço histórico
> de um ativo (via Yahoo Finance), roda uma estratégia de regras definidas e
> produz a "ficha matemática" completa de um sistema de trading: **win rate,
> expectância, R, curva de capital, drawdown máximo, variância e risco de ruína**.
>
> Estes são os quatro pilares que o sistema deve medir: **expectância**,
> **variância**, **tradeoff risco/recompensa** e **gestão de risco/sobrevivência**.

---

## 0. Princípio que não pode ser violado

Os números (win rate, expectância, etc.) **não são dados que se baixam** — são
*resultados* de simular uma estratégia sobre o preço. O Yahoo Finance fornece
apenas a matéria-prima: **OHLCV** (Open, High, Low, Close, Volume). Todo o resto
é calculado pelo backtester. Mantenha essa separação clara no código: uma camada
de **dados**, uma camada de **estratégia**, uma camada de **simulação** e uma
camada de **métricas/relatório**.

---

## 1. Stack e dependências

- Python 3.11+
- `yfinance` — download de OHLCV (gratuito; raspa endpoints não-oficiais do
  Yahoo, então pode quebrar sem aviso — trate falhas de rede com retry/erro claro)
- `pandas`, `numpy` — manipulação e cálculo
- `matplotlib` — gráficos (curva de capital, drawdown, distribuição de resultados)
- `pyyaml` ou `argparse` — configuração via arquivo/CLI

Instalar com `pip`. Fixar versões num `requirements.txt`.

---

## 2. Estrutura de projeto sugerida

```
backtester/
├── data.py          # download e limpeza do OHLCV
├── strategy.py      # classe base Strategy + estratégias concretas
├── engine.py        # simulação trade a trade (o coração)
├── metrics.py       # cálculo de todas as métricas
├── montecarlo.py    # variância e risco de ruína
├── report.py        # impressão do relatório + gráficos
├── config.yaml      # parâmetros do teste
├── main.py          # orquestra tudo
└── requirements.txt
```

---

## 3. Camada de dados (`data.py`)

- Função `load_ohlcv(ticker, start, end, interval="1d")` que baixa via
  `yfinance.download(...)`.
- **Ações brasileiras (B3) usam o sufixo `.SA`** — ex.: `PETR4.SA`, `VALE3.SA`,
  `ITUB4.SA`. Validar/avisar se o usuário esquecer.
- Remover linhas com `NaN`, ordenar por data, garantir índice de datas único.
- Avisar se o período retornar poucos candles (amostra insuficiente).
- Retornar um `DataFrame` com colunas: `Open, High, Low, Close, Volume`.

---

## 4. Camada de estratégia (`strategy.py`)

Projetar de forma **plugável**, para o usuário trocar a estratégia sem mexer no
motor:

```python
class Strategy:
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe OHLCV e devolve o MESMO df com colunas extras:
          - signal: 1 (comprar), -1 (vender/short), 0 (nada)
          - stop:   preço de stop loss para a entrada
          - target: preço de alvo (take profit)
        REGRA DE OURO: cada linha só pode usar dados ATÉ aquela linha.
        Nada de usar o futuro.
        """
        raise NotImplementedError
```

Entregar pelo menos **uma estratégia concreta de exemplo** — cruzamento de médias
móveis (ex.: MA20 cruza MA50), com stop a N×ATR e alvo a M×ATR — para que o
sistema rode "de fábrica". Deixar parâmetros (períodos das médias, múltiplos de
ATR) configuráveis no `config.yaml`.

---

## 5. Motor de simulação (`engine.py`) — a parte mais delicada

Aqui moram os erros que invalidam um backtest. Implementar com rigor:

### 5.1 Sem viés de lookahead (CRÍTICO)
- O sinal é gerado no fechamento da barra `t`, mas a **execução acontece na
  abertura da barra `t+1`**. Nunca entrar/sair no mesmo candle que gerou o sinal
  usando o preço de fechamento dele. Esse é o erro nº 1 de backtest e infla
  resultados de forma irreal.

### 5.2 Definição de R (R-múltiplo)
- `risco_por_unidade = |preço_entrada − preço_stop|`
- `R = (preço_saída − preço_entrada) / risco_por_unidade` (sinal ajustado p/ short)
- Cada trade fechado guarda seu resultado **em R** e **em dinheiro**.
- Isso conecta direto com o vídeo: o sistema é descrito por `(win rate, R médio)`.

### 5.3 Custos (não ignorar — o vídeo alerta para isso)
Descontar de **cada trade**:
- **spread** (estimar em pips/centavos),
- **comissão** (por ordem ou por lote),
- **slippage** (estimar como fração do range do candle).

Tudo configurável no `config.yaml`. Sem custos, a expectância "no papel" fica
otimista demais e mente.

### 5.4 Position sizing (gestão de risco)
- O **risco em dinheiro por trade é fixo** (ex.: 0,5% do capital). Faixa
  recomendada: **0,25% a 2% no máximo**.
- `tamanho_posição = risco_em_dinheiro / risco_por_unidade`.
- Stop maior ⇒ posição menor; stop menor ⇒ posição maior. O risco em % é o que
  permanece constante.
- Para forex, converter em **lotes** (1 lote padrão = 100.000 unidades) e expor
  uma função tipo calculadora de lote (currency, balance, risk%, stop em pips).

### 5.5 Saída do motor
Uma lista/`DataFrame` de **trades**, cada um com: data entrada/saída, lado,
preço entrada/saída/stop/alvo, resultado em R, resultado em $, custos aplicados,
e o capital acumulado após o trade (curva de capital).

---

## 6. Métricas (`metrics.py`) — a "ficha" do vídeo

Calcular e retornar:

| Métrica | Fórmula / definição |
|---|---|
| Nº de trades | contagem total (avisar se < 100 — ver §8) |
| Win rate | `wins / total` |
| Loss rate | `1 − win_rate` |
| Ganho médio | média dos trades vencedores (em $ e em R) |
| Perda média | média dos trades perdedores (em $ e em R) |
| **Expectância** | `EV = win_rate × ganho_médio − loss_rate × perda_médio` (em $ **e** em R) |
| Profit factor | `lucro_bruto / perda_bruta` |
| Win rate de breakeven | `1 / (R + 1)` — para comparar com o win rate real |
| Curva de capital | capital acumulado trade a trade |
| Drawdown máximo | maior queda do pico anterior (em % e em $) |
| CAGR / retorno total | opcional, mas útil |
| Sharpe / Sortino | opcional |

**Validação de sanidade:** a expectância calculada a partir dos trades deve bater
com a fórmula `win_rate × ganho − loss_rate × perda`. Se não bater, há bug.
Loggar essa checagem.

A fórmula de breakeven é só sanity check do tradeoff: alvo de 4R precisa de só
~20% de acerto para empatar; 1R precisa de 50%. Mostrar o win rate real ao lado
do breakeven deixa óbvio se o sistema tem margem.

---

## 7. Variância e risco de ruína (`montecarlo.py`)

Esta é a parte que o vídeo trata como o que mais derruba trader emocionalmente —
e que um backtest ingênuo (uma única curva) esconde.

### 7.1 Distribuição de resultados (variância)
- Pegar a sequência de resultados em R dos trades reais e **reembaralhar a ordem
  (bootstrap)** N vezes (ex.: N = 5.000), reconstruindo a curva de capital a cada
  vez.
- Reportar a **distribuição**: curva mediana, percentis 5% e 95%, melhor e pior
  caso. Isso reproduz o slide "Variance Changes Everything" — mesmo sistema,
  mesma expectância, experiências completamente diferentes.
- **Fixar a seed** do gerador aleatório para reprodutibilidade.

### 7.2 Risco de ruína / probabilidade de drawdown
- Via Monte Carlo, estimar a **probabilidade de atingir um drawdown de X%**
  (ex.: 50%) para diferentes níveis de risco por trade (0,5% / 1% / 2% / 5%).
- Mostrar como essa probabilidade **explode de forma não-linear** conforme o
  risco por trade aumenta (replica a tabela de "probability of ruin" do vídeo).

### 7.3 Matemática da recuperação
- Tabela da assimetria perda↔recuperação: `ganho_necessário = 1/(1 − perda) − 1`.
  - 10% de perda ⇒ ~11% para recuperar
  - 30% ⇒ ~43%
  - 50% ⇒ 100%
- Imprimir essa tabela no relatório para deixar explícito por que proteger
  capital importa mais do que maximizar retorno.

---

## 8. Tamanho de amostra (regra "uma trade não significa nada")

- Se o backtest gerar **menos de ~100 trades**, emitir um **aviso destacado** de
  que a expectância ainda está dominada por ruído e não é confiável.
- Opcional: mostrar a curva de "expectância acumulada vs. nº de trades" para
  ilustrar visualmente quando ela estabiliza (replica o slide "One Trade Means
  Nothing").

---

## 9. Relatório e gráficos (`report.py`)

Imprimir no terminal um resumo limpo com todas as métricas da §6, mais:
- a faixa de variância da §7.1,
- a tabela de risco de ruína da §7.2,
- a tabela de recuperação da §7.3,
- o aviso de amostra da §8.

E salvar gráficos em PNG:
1. **Curva de capital** (a real).
2. **Underwater plot** (drawdown ao longo do tempo).
3. **Leque de Monte Carlo** (mediana + banda 5–95%) — a variância visualizada.
4. **Histograma** do resultado final entre as simulações.

---

## 10. Configuração (`config.yaml`)

Tudo que o usuário troca sem editar código:

```yaml
ticker: "PETR4.SA"
start: "2018-01-01"
end:   "2026-01-01"
interval: "1d"

capital_inicial: 10000
risco_por_trade_pct: 0.5      # 0,25 a 2,0

custos:
  spread: 0.02
  comissao: 0.0
  slippage_frac: 0.05         # fração do range do candle

estrategia:
  nome: "ma_crossover"
  ma_rapida: 20
  ma_lenta: 50
  atr_periodo: 14
  stop_atr_mult: 1.5
  alvo_atr_mult: 3.0

montecarlo:
  n_simulacoes: 5000
  seed: 42
  drawdown_alvo_pct: 50
  niveis_risco: [0.5, 1.0, 2.0, 5.0]
```

---

## 11. Armadilhas a evitar (checklist de qualidade)

- [ ] **Lookahead bias** — sinal em `t`, execução em `t+1`. (§5.1)
- [ ] **Custos aplicados** em todo trade — sem isso o resultado é fantasia. (§5.3)
- [ ] **Risco fixo em %**, não tamanho de posição fixo. (§5.4)
- [ ] **Amostra pequena** sinalizada. (§8)
- [ ] **Seed fixa** no Monte Carlo para reprodutibilidade. (§7)
- [ ] **Sanity check** da expectância (fórmula vs. trades reais). (§6)
- [ ] **Sobrevivência de dados** — atenção a splits/dividendos (usar preços
      ajustados do yfinance) e a ativos que saíram de bolsa (survivorship bias).
- [ ] Idealmente, separar **in-sample / out-of-sample** para não otimizar em cima
      do ruído (mencionar mesmo que não implemente já).

---

## 12. Critério de aceite

Considere pronto quando, ao rodar `python main.py` com o `config.yaml` padrão,
o sistema:

1. baixar o OHLCV do ticker,
2. rodar a estratégia de exemplo,
3. imprimir a ficha completa (win rate, expectância em $ e R, profit factor,
   drawdown, breakeven win rate ao lado do real),
4. rodar o Monte Carlo e imprimir variância + risco de ruína + recuperação,
5. salvar os 4 gráficos,
6. e emitir o aviso de amostra quando aplicável —
   **tudo sem erro e com os números batendo no sanity check.**

> **Lembrete final:** toda essa matemática só vale se a estratégia tiver
> expectância positiva *real*. O backtester mede o edge; ele não cria um. E a
> variância corta dos dois lados: pode esconder um bom sistema por 20 trades, e
> pode fazer um sistema ruim parecer bom por um bom tempo. Trate resultados de
> amostra pequena com ceticismo.
