-- Metadata for factor definitions
CREATE TABLE IF NOT EXISTS factor_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,          -- Internal identifier (e.g., 'vol_20d_std')
    display_name TEXT,                  -- Human readable name
    category TEXT,                      -- e.g., 'Momentum', 'Volatility', 'Value'
    description TEXT,                   -- Detailed explanation of the factor
    formula_config TEXT,                -- JSON string for parameters (e.g., '{"window": 20}')
    version TEXT DEFAULT '1.0.0',       -- Version of the calculation logic
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Time-series factor values
CREATE TABLE IF NOT EXISTS factor_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factor_id INTEGER NOT NULL,         -- Reference to factor_definitions
    symbol TEXT NOT NULL,               -- Asset identifier (e.g., 'AAPL')
    timestamp DATETIME NOT NULL,        -- Data point timestamp
    value REAL NOT NULL,                -- The computed numeric value
    metadata TEXT,                      -- Optional JSON for extra context (e.g., error bounds)
    FOREIGN KEY (factor_id) REFERENCES factor_definitions(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_factor_values_lookup 
ON factor_values (factor_id, symbol, timestamp);

CREATE INDEX IF NOT EXISTS idx_factor_values_timestamp 
ON factor_values (timestamp);
