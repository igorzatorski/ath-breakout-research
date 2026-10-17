# Annual return distribution and post-entry paths

Study: `ath_17_return_paths_v001`  
Run: `outputs/research/ath/ath_17_return_paths_v001/20261016T215031880762Z`  
Protocol: [ATH_RETURN_PATHS_PLAN.md](ATH_RETURN_PATHS_PLAN.md)

## Finding

The observed ATH + strong-momentum distribution has a substantial positive tail: relatively few large winners account for much of its positive event-weighted mean. However, some eventual winners first suffer sizeable losses from entry, and more events reach large gains during the window than retain them at the annual endpoint. These facts motivate testing an exit hypothesis; they do **not** establish that cutting losses improves performance, that winners are identifiable in advance, or that a profitable portfolio strategy exists.

Primary population: frozen ATH + common 6-1/top20, **23,712 annual stock/SPY pairs**. Context: **71,961 qualified ATH annual pairs**. Source signals without complete annual pairs remain excluded under original rules, not repaired with zeros. Both include repeated companies/events; sensitivity flags were frozen before this experiment. Prices end June 30, 2026 and annual mature signal cohorts end in partial 2025. All inspected history is exploratory.

## Annual endpoint distribution

| Annual stock return | Events | Share of primary events |
|---|---:|---:|
| Below -50% | 2,318 | 9.78% |
| -50% to below -20% | 4,013 | 16.92% |
| -20% to below 0% | 4,244 | 17.90% |
| 0% to below +20% | 4,786 | 20.18% |
| +20% to below +50% | 4,151 | 17.51% |
| +50% to below +100% | 2,602 | 10.97% |
| +100% to below +200% | 1,075 | 4.53% |
| +200% to below +300% | 256 | 1.08% |
| At least +300% | 267 | 1.13% |

Primary mean **+15.47%**, median **+3.66%**, same-window SPY mean **+9.89%**. Negative annual return frequency **44.60%**. Mean losing return **-31.08%**; mean nonnegative return **+52.93%**. These are buy-and-hold event outcomes, not the win rate or payoff of a strategy using stops.

Stock quantiles: 5th **-63.79%**, 25th **-22.44%**, median **+3.66%**, 75th **+35.32%**, 95th **+118.73%**, 99th **+313.53%**. In the broader all-ATH context, mean is +12.64%, median +6.64%, loss frequency 41.12%; only 4.32% finish at least +100%. Strong-momentum conditioning increases both large-winner frequency and loss frequency in these observed samples. It does not prove a causal filter improvement.

## Reaching a large gain versus retaining it

Percentages below overlap cumulatively; do not add rows.

| Gain level | Finished at or above | Reached at a close during year |
|---|---:|---:|
| +50% | 17.71% (4,200) | 30.77% (7,296) |
| +100% | 6.74% (1,598) | 12.08% (2,865) |
| +200% | 2.21% (523) | 3.88% (920) |
| +300% | 1.13% (267) | 1.98% (470) |

A +200% return means wealth tripled, not doubled. These are total-wealth gains from entry, including eligible distributions. Values are observed at closes; intraday highs are not measured here.

Final >=100% events contribute **+13.98 pp** to the overall **+15.47%** stock mean. The other events average +1.59%. Final >=200% events contribute +7.91 pp. These are contributions using all parent events in the denominator; cumulative tails overlap. They describe net event-mean concentration, not shares of all gross profits or portfolio P&L.

Retrospective top5% influence: 1,186 events contribute +12.10 pp to the full mean; the remaining events average +3.55%. Top1% (238 events) contribute +4.94 pp. These outcome-selected omissions are diagnostics only; no investor could remove or select those events in advance from these calculations.

## Adverse paths before eventual success

For events finishing at least +100%, **before first reaching +100% at a close**:

| Closing wealth below initial investment | Winners that crossed it | Share of those 1,598 winners |
|---|---:|---:|
| -10% | 584 | 36.55% |
| -20% | 264 | 16.52% |
| -30% | 125 | 7.82% |

Among the 523 final >=200% winners, the analogous shares before first reaching +200% are 34.99%, 16.06%, 7.27%. Among the 267 final >=300% winners, they are 39.33%, 14.98%, 5.62%. These are hindsight-conditional groups, not a trading filter.

Consequently a narrow loss rule could truncate some large winners, but this does not show that the rule is bad: savings on other losing events could offset the missed upside. No stop was executed or repriced here. Closing total wealth is not the exact traded stock-price threshold; intraday crossings, overnight gaps, fills, costs, stop re-entry and dividend effects require explicit execution rules.

## Typical closing excursions

Across primary events:

- Median worst loss relative to entry (closing MAE): **-21.14%**.
- Median best gain relative to entry (closing MFE): **+28.82%**.
- Median peak-to-subsequent-trough closing drawdown: **-35.16%**.

These differ: a stock can rise first, then lose substantially from its peak while remaining above entry. Initial capital 1 is included. The 10th MAE percentile is -61.33%; the median is not a downside bound. Neither MAE nor MFE gives a tradable best exit without hindsight.

Paths use next-session open to the first close, then subsequent CIZ total returns. Terminal return is applied once and proceeds are held as zero-interest cash. Every reconstructed endpoint reconciles to the frozen annual return. Cross-sectional path quantiles at each holding session are not trajectories of a single representative stock and are not prediction bands.

## Repeats and period sensitivity

Fixed nonoverlap primary sample: 1,725 events, stock mean +13.88%, median +3.53%, SPY +10.24%. Final >=100% events are 116 (6.72%) and contribute +12.61 pp of the stock mean. Thus right-tail concentration is also visible under this sensitivity. This does not establish portfolio performance.

Final >=100% frequency by existing period: early 10.66%, middle 3.60%, recent 5.36%. Primary mean stock returns by period are 21.57%, 12.97%, 11.34%; SPY excess is +17.11, +0.90, -2.23 pp. Right tails remain present recently while relative market performance differs. No causal explanation or new significance claim is made from these descriptive cuts.

## Figures and reproducibility

- `return_distribution.png`: visually checked static grouped histogram, including all return tails and same-window SPY; category bars represent probability mass, not density per return interval.
- `return_distribution.html`: standalone Plotly scientific figure with two selectable populations and four panels: distribution, ever/final large gains, cross-sectional paths, and prior losses among large winners. The Plotly data/trace construction was checked, but its browser UI could not be visually verified because the available browser could not reach the local preview server. The PNG was rendered independently with ReportLab charts and PDFium and inspected directly.
- `by_year/paths_YYYY.npz`: exact complete closing-wealth matrices and event IDs.
- `events.parquet`, source coverage, return bins, quantiles, tail contributions, winner prior-loss counts, top-tail influence, path quantiles, manifest and independent verification.

Independent verification passed **506,679 numerical checks**, **315 complete raw scalar path samples**, and reconciliation of **all 71,961 endpoints**. Checks include terminal cash, distribution partitioning, MAE/MFE/drawdown and tail/prior-loss counts. Nine relevant tests passed (path diagnostics, existing wealth paths and annual returns), plus Ruff and whitespace checks. These are scoped checks, not full repository tests, raw-provider audit or calibrated statistical inference. No distribution significance test was needed for this descriptive question.

## Research stage

Only selected filters have been explored: momentum windows, consolidation range and fixed prior-ATH proximity. We have not exhausted possible filters, nor should exhaustive searching be the objective. There is no validated complete ranking, exit, sizing, allocation or portfolio-construction rule for the current research setup. Existing engine code and older pilots are not validation of such a strategy.

A next separately registered experiment could test a small, fixed set of loss/exit rules against unchanged buy-and-hold, with explicit decision time, gaps/fills, terminal treatment, re-entry and costs. It should report both avoided losses and missed large winners. No rule should receive credit for trimming observed losers while preserving the same observed winners automatically. Complete portfolio tests and genuinely uninspected validation remain later stages. No exit or combined-filter experiment was run here.
