# account-service Specification

## Purpose
TBD - created by archiving change account-management. Update Purpose after archive.
## Requirements
### Requirement: Track Cash Balance
The account service SHALL track the current cash balance for each user. It MUST provide methods for querying the balance and updating it after trades or external transfers.

#### Scenario: Query Initial Balance
- **WHEN** the system starts a new session with an initial capital of $100,000
- **THEN** the account service SHALL return exactly $100,000 for the user's cash balance

#### Scenario: Update Balance After Deposit
- **WHEN** a deposit of $5,000 is made to the account
- **THEN** the cash balance SHALL increase by $5,000

### Requirement: Portfolio Ownership
The account service SHALL be the sole component responsible for managing and tracking asset positions (quantities and average costs). It MUST provide APIs for querying current holdings.

#### Scenario: Query Positions
- **WHEN** a request for current holdings is made
- **THEN** the account service SHALL return a list of all symbols with their respective quantities and average costs.

### Requirement: Position Updates
The account service SHALL update asset positions and average costs immediately upon receiving trade fill notifications.

#### Scenario: Update After Fill Notification
- **WHEN** the account service receives a fill notification for buying 10 units of AAPL at $150
- **THEN** it SHALL update the AAPL position quantity and average cost accordingly.

### Requirement: Insufficient Funds Check
The account service SHALL provide a validation check to determine if an account has enough cash to cover a proposed buy order, including projected fees.

#### Scenario: Successful Balance Check
- **WHEN** a user with $10,000 balance attempts to buy $5,000 worth of assets
- **THEN** the balance check SHALL return SUCCESS

#### Scenario: Failed Balance Check
- **WHEN** a user with $1,000 balance attempts to buy $2,000 worth of assets
- **THEN** the balance check SHALL return FAILURE with an INSUFFICIENT_FUNDS error

