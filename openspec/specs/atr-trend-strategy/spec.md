## ADDED Requirements

### Requirement: ATR-Based Trend Entry
The system SHALL monitor price trends using a configurable indicator (e.g., price breakout) and generate a BUY signal when the trend condition is met.

#### Scenario: Trend breakout entry
- **WHEN** the current price breaks above the high of the last 20 bars
- **THEN** the strategy SHALL calculate the "1 UNIT" quantity and generate a BUY signal

### Requirement: ATR-Based Unit Sizing
The system SHALL calculate the number of shares for "1 UNIT" such that the potential loss (Risk Amount) from the entry price to the ATR-based stop-loss price equals a fixed percentage of total equity (e.g., 1%). 
Formula: `Quantity = (Total Equity * Risk Percentage) / (Stop Distance in Price)`.

#### Scenario: Calculating unit size
- **WHEN** total equity is 100,000, risk percentage is 1% (1,000 risk), entry price is 150, and ATR(14) is 2.5 with a 2x ATR stop (5.0 distance)
- **THEN** the strategy SHALL calculate 1 UNIT as 200 shares (1,000 / 5.0)

### Requirement: Volatility-Based Risk (ATR)
The system SHALL calculate the Average True Range (ATR) over a configurable period and use it to set the initial stop-loss price.

#### Scenario: Setting ATR-based stop loss
- **WHEN** a BUY signal is generated at 150.0 and ATR(14) is 2.5
- **THEN** the strategy SHALL set a Stop-Loss at 145.0 (Entry - 2 * ATR)

### Requirement: Position Sizing Limit
The system SHALL limit the total nominal value of the strategy's position to no more than 5% of the total account capital. This limit SHALL take precedence over the unit sizing calculation.

#### Scenario: Unit size exceeds 5% limit
- **WHEN** 1 UNIT is calculated as 200 shares at $150 ($30,000 value), but 5% of a $400,000 account is $20,000
- **THEN** the strategy SHALL cap the BUY order at 133 shares ($19,950 value) to respect the 5% limit
