# ATH39: removing the mandatory momentum top20 gate

Fixed ATH and two-year highs, original gain stages SMA150 ->100 at+50% ->50 at+100%, next-opening execution, 20-company capacity,5% initial target,10bps per side and zero cash yield. Clean2008-01-02 through2026-06-30. Only the market6-1/top20 requirement is removed. The MV ranking algorithm remains and is recomputed within each expanded candidate set. Complete12-1 feature support, volume/contraction availability, monthly PIT liquidity membership and conservative high-history quality are unchanged. This is not a pure unfiltered breakout strategy or removal of momentum from the priority score.

## Full-period net results

| Definition | Drift CAGR | Monthly CAGR | Drift max drawdown | Monthly max drawdown |
|---|---:|---:|---:|---:|
| ath_top20 | 9.29% | 9.07% | -44.51% | -43.15% |
| ath_all | 7.54% | 7.26% | -49.24% | -48.18% |
| high2y_top20 | 6.48% | 6.20% | -42.29% | -42.03% |
| high2y_all | 7.10% | 6.55% | -45.09% | -44.58% |
| SPY | 11.24% | 11.24% | -52.45% | -52.45% |

## Contemporary calendar slices

| Definition | Since2018 drift CAGR | Since2018 monthly CAGR | Since2023 drift CAGR | Since2023 monthly CAGR |
|---|---:|---:|---:|---:|
| ath_top20 | 8.20% | 6.58% | 13.03% | 8.46% |
| ath_all | 5.96% | 4.76% | 12.83% | 8.61% |
| high2y_top20 | 7.21% | 6.87% | 21.33% | 15.69% |
| high2y_all | 8.51% | 7.09% | 23.69% | 19.68% |
| SPY | 14.67% | 14.67% | 22.83% | 22.83% |

Calendar slices inherit positions from the clean2008 simulation. No fresh2018/2023 starts or unseen validation are claimed. All individual years remain saved.

## Difference from removing the gate

| Breakout | Period | Drift CAGR change | Monthly CAGR change |
|---|---|---:|---:|
| ath | all | -1.75 pp | -1.81 pp |
| ath | 2018_end | -2.24 pp | -1.82 pp |
| ath | 2023_end | -0.20 pp | +0.15 pp |
| high2y | all | +0.62 pp | +0.35 pp |
| high2y | 2018_end | +1.31 pp | +0.22 pp |
| high2y | 2023_end | +2.36 pp | +3.98 pp |

## Candidates and actual selection

| Definition | Signals | Below-top20 candidates | Executed drift entries | Below-top20 drift entries |
|---|---:|---:|---:|---:|
| ath_top20 | 17285 | 0 | 878 | 0 |
| ath_all | 47480 | 30195 | 898 | 346 |
| high2y_top20 | 23418 | 0 | 945 | 0 |
| high2y_all | 64763 | 41345 | 938 | 335 |

Counts include final signals without a next session. Recomputed MV scores can change priorities even among candidates that were previously eligible. Changed capacity, later entries, exposure and fees affect the full portfolio path. Cashflow episode PnL including open marks, large-winner counts, top contributors and company attribution are saved in tail_trading_diagnostics.csv and episode_attribution.parquet. Monthly episode profit ratios are not fixed-unit price returns.

## Findings

Removing the gate lowers full-period ATH CAGR9.29/9.07% to7.54/7.26%, with larger full drawdowns. The same removal raises two-year-high CAGR6.48/6.20% to7.10/6.55%, but also increases full drawdowns. Since2018 ATH remains weaker without the gate; two-year highs improve to8.51/7.09% but remain belowSPY14.67%. Since2023 the ungated two-year drift portfolio returns23.69% versus21.33% gated and22.83% SPY; monthly19.68% still trailsSPY. No uniform top20 benefit or universal improvement from removing it is established. All full-period variants remain belowSPY11.24%.

## Scope and interpretation

The saved difference table answers the fixed gate ablation within this MV-prioritized US portfolio. It does not establish the best ranking, pure ATH efficacy, GPW account replication, causal economic mechanism or an optimal rule. No new confidence interval or risk-adjusted alpha is claimed. Known2008-present history remains development evidence. Do not combine favorable results automatically with previous best exits, gap caps or consolidation.

## Verification

All 100 top20 control period rows exactly match ATH38 CAGR, NAV, drawdown and exposure. Candidate keys/features/MV priorities also reproduce both prior controls. All eight independent daily cash/share/required-exit/stage replays passed. Independently audited152,946 raw candidate windows,3,607,887 market-pool rank rows,29,349,468 raw SMA cells,200 portfolio summaries and eight SPY curves. Receipts and final counts/status are in manifest.json. Twelve focused window/rank/stage tests pass. Inputs, protocol and code are SHA256 recorded.

Run: `outputs\backtests\ath_39_momentum_gate_v001\20261017T194125816621Z`. Protocol: `ATH_MOMENTUM_GATE_PLAN.md`.
