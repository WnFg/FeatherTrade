## Context

The `ATRTrendStrategy` is designed to be a robust trend-following strategy that leverages volatility (via Average True Range) for both entry filtering and precise risk-based position sizing. It builds upon the `StatefulStrategy` framework to manage lifecycle states and risk-driven exits.

## Goals / Non-Goals

**Goals:**
- Implement a 20-period price breakout entry (Donchian Channel high).
- Calculate "1 UNIT" of position size based on a fixed risk percentage (e.g., 1% of equity) and the ATR-based stop distance.
- Enforce a hard cap on position size at 5% of total account value.
- Use ATR-based trailing or initial stop losses.

**Non-Goals:**
- Implementing a complex multi-asset portfolio optimizer (focus is on single-asset logic).
- High-frequency tick-by-tick indicator updates (indicators will be updated on bar close).

## Decisions

### 1. Indicator Calculation
**Decision**: Indicators (ATR and N-period High) will be calculated within the strategy using a sliding window of recent bars.
**Rationale**: While a global `FactorService` exists, implementing these specific indicators locally ensures the strategy is self-contained and avoids dependency on pre-registered factor logic that may not exist in the environment.

### 2. State Machine and Risk
**Decision**: Override `check_risk` in `StatefulStrategy` to compare the current price against a dynamic `stop_loss_price` calculated at entry.
**Rationale**: This aligns with the `StatefulStrategy` pattern while allowing volatility-based (non-percentage) stops.

### 3. Position Sizing Logic
**Decision**: 
1. Calculate `stop_distance = multiplier * ATR`.
2. Calculate `risk_quantity = (Total Equity * 0.01) / stop_distance`.
3. Calculate `limit_quantity = (Total Equity * 0.05) / Current Price`.
4. Final `Quantity = min(risk_quantity, limit_quantity)`.
**Rationale**: This multi-layered approach ensures that a single trade never risks more than 1% of the portfolio, and its total market exposure never exceeds 5%, satisfying both risk-management and regulatory/safety constraints.

## Risks / Trade-offs

- **[Risk] Gap Openings** → **Mitigation**: ATR-based stops are calculated at entry but execution depends on market liquidity. The `StatefulStrategy` state machine will attempt liquidation as soon as the price is breached.
- **[Risk] Indicator Lag** → **Mitigation**: Use a 20-period breakout which is a standard trend-following parameter to balance responsiveness and noise filtering.
