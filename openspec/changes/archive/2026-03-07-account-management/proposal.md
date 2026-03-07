## Why

A trading system must track user resources to ensure financial integrity and operational feasibility. Currently, the system lacks a centralized account management service, making it impossible to enforce risk limits (e.g., insufficient funds) or accurately track the impact of trades on a user's total equity and portfolio.

## What Changes

- **New Account Service**: A centralized module to manage balances and asset holdings.
- **Resource Constraints**: Order execution will now be gated by account solvency (e.g., cannot buy if cash is insufficient).
- **Execution-Account Linkage**: Trade fills will automatically update account cash and position state.

## Capabilities

### New Capabilities
- `account-service`: Tracks cash balances, margin requirements, and consolidated portfolio value. Provides APIs for balance checks and updates.

### Modified Capabilities
- `execution-engine`: Order submission and fulfillment requirements will be updated to include mandatory account balance/margin validation before execution.

## Impact

This change introduces a dependency for the `execution-engine` on the `account-service`. It affects core trade workflows and introduces new validation logic for order processing.
