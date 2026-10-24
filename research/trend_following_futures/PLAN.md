# Futures trend following: research plan

Current status: one predeclared market-level prototype is implemented and run;
see BASELINE_V001_PLAN.md, DATA_AUDIT.md and BASELINE_V001_RESULTS.md.
The stages below describe the full research roadmap. The executable-chain and
production accounting milestones remain incomplete; v001 uses documented proxies.

## Stage 0: scope established

The user requested a new research track, starting with the choice of markets.
The primary hypothesis is diversified time-series momentum with volatility-based
sizing. Cross-sectional ranking, price-level Z-scores and SHA are separate
future comparisons. No signal is presumed profitable.

Start with 20 market families, not 20 individual expiring positions or one lot
of each product. The candidate list is pre-performance and not selected from
historical backtest winners. It is a convenience universe concentrated in
US-listed, USD-settled products, not a globally representative or historically
point-in-time complete universe. Retain an exclusion/change log.

## Stage 1: data feasibility (next milestone)

Audit available legal data access and coverage for a few representative markets
(ES, ZN, 6E, CL), then all candidates. Use known exchange sources for contract
definitions; confirm vendor root mapping, historical changes and units separately.
Document data products, costs, roll metadata, raw-contract availability and
reproducibility. Reading public documentation does not establish data access.

Do not purchase data, upload local research or use credentialed data services
without the corresponding user authorization. Research can proceed with public
documentation and an inventory of local files. Preserve raw sources.

Complete DATA_REQUIREMENTS.md before reporting a futures strategy result.
If only a continuous-price prototype is feasible, label its assumptions and
limitations explicitly and do not present it as verified contract-level P&L.

## Stage 2: freeze one baseline before inspecting performance

Proposed design (not yet a fully frozen execution specification):

- Daily observations; signal/sizing refresh once per month using only information
  available at that decision time. Calendar timing and execution latency must
  be specified per market before the run.
- Own-market momentum over 12 completed months, positive -> long and negative
  -> short, zero -> flat. Do not force dollar-neutral long/short rankings.
- Derive momentum from a documented tradable futures excess-return or properly
  normalized P&L history. Do not use percentage changes of an arbitrary additive
  back-adjusted price series or assume futures prices are always positive.
- Daily contract dollar-P&L volatility estimated over 60 past valid sessions;
  scale positions inversely with volatility. Confirm normalization and treatment
  of contract multiplier, quote units and historical rolls before freezing.
- Initial risk budget: 25% for each broad class; equal standalone risk allocations
  within a class, adjusted by inverse volatility. These allocations are not an
  assertion of equal marginal contribution once correlations are considered.
- Provisional portfolio volatility target 10% annualized. This is an ex-ante
  scaling objective, not a realized-volatility guarantee or promised return.
- Apply a portfolio covariance estimate and explicit market, sector, gross
  exposure and margin limits. Estimator, floors, caps and emergency actions
  must be fixed before the first backtest, not optimized on its outcomes.
- Research portfolio capital, integer-lot rounding, collateral yield, fees,
  spread/slippage, position limits and roll rules are unresolved inputs. Do not
  copy the SPY 100,000 USD / fractional-share execution model as if tradable.
- Contract rolls can occur between monthly signal dates; risk/margin monitoring
  is required between rebalances. Define permitted risk reductions in advance.

Save all resolved settings and the time split in a separate baseline manifest.
An initial full-history feasibility run is exploratory; reserve any genuinely
untouched validation history before parameter selection where feasible.

## Stage 3: execution and accounting slice

Validate one market on a small explicit contract chain before adding a portfolio.
Hand-check long and short mark-to-market, multiplier/quote conversion, a roll,
execution costs, margin transfers and collateral cash. Then add the other classes.
Test causality, calendar mismatches, missing bars, zero/negative prices,
contract rounding and risk-limit behavior. Account for both legs of rolls;
do not treat the new-vs-old contract price gap as free return or double-count
roll effects already included in a provider's futures-return series.

## Stage 4: first portfolio experiment

Run one shared momentum specification with common risk and execution rules.
Report total vs excess-of-cash returns, drawdowns, turnover, exposure, margin
usage, sector/market contribution and dependence on individual trend episodes.
Compare against matched-risk controls, including always-long futures and a
no-direction/risk-allocation diagnostic where its definition is meaningful.
Traditional equity/60-40 comparisons are portfolio context, not the sole objective.

## Later work

Only after the baseline is audited: bounded horizon sensitivity, comparison with
SHA or moving-average signals, and expansion toward 40-50 markets including
non-US equity and bond futures and further commodity groups. Preserve all trials;
do not tune an independent best horizon for every market at the outset.
