# Futures data requirements and current audit status

Status on 2026-10-24: public pysystemtrade market-level data acquired and audited
for an explicitly limited research prototype. See DATA_AUDIT.md and
BASELINE_V001_RESULTS.md. Full executable-chain and historical margin/delivery
verification is still incomplete. The requirements below remain the production
and fully audited research target, not a claim that all items are satisfied.

## Required source records

For every dated contract retain market root, vendor symbol, contract identifier,
expiry/delivery month, session date/timezone, raw open/high/low/close/settlement,
volume and open interest when supplied. Keep actual observations distinct from
forward-filled marks. Record exchange holidays, session boundaries and the time
at which settlement, volume and OI become available.

Retain point value/multiplier, price quotation and scale, tick size/value,
P&L currency, listing/start history, last trade date and first notice/delivery
constraints where relevant. Exchange/vendor mappings need dated evidence.
Raw futures prices may be zero or negative; a positive-only ETF validator and
log-return assumptions are not universally applicable.

## Roll and return contract

Define active-contract eligibility and a causal roll rule using information
available at the time. Complete rolls before delivery/notice constraints, with
market-specific exchange calendars. Volume/OI-based rules must lag publication
appropriately. Prohibit accidental expiry settlement or delivery in the model.

Distinguish raw dated-contract execution prices, continuous signal histories
and investable P&L/return histories. A continuous close alone does not establish
an executable historical strategy. Vendor adjustment type and roll calendar are
required. Check that future roll adjustments cannot change past trading choices.

## Portfolio cash and execution

Futures positions generate daily mark-to-market P&L; margin posted is not the
notional purchase price. Track USD cash/collateral, initial/maintenance margin,
available liquidity, stress funding and exposure limits. State whether cash yield
is earned on collateral and avoid counting it twice in futures excess returns.
Specify commissions per contract, exchange/clearing fees, ticks/spread/slippage,
both roll legs, market execution times and integer sizing.

## First audit deliverable

Create a coverage table for all 20 candidates with source, available date range,
contract count, raw-chain and roll-metadata availability, licensing/access status,
missing/duplicate bars, quote/multiplier checks, price anomalies and whether the
market is eligible. Begin with ES/ZN/6E/CL as representative accounting cases.
Retain source hashes and an explicit list of unresolved data limitations.

This checklist does not authorize a subscription, data purchase or credentialed
connection. Public-source research and local inspection are within this stage.
