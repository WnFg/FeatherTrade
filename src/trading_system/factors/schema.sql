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

-- Data source templates/instances with parameters
CREATE TABLE IF NOT EXISTS data_source_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,          -- User-defined name for the instance
    class_path TEXT NOT NULL,           -- Python class path (e.g., 'src.trading_system.factors.builtin.data_sources.TuShareDataSource')
    parameters TEXT,                    -- JSON string for constructor parameters
    transformation_config TEXT,         -- JSON string for post-fetch transformations
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Linking factors with data sources and scheduling info
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factor_definition_id INTEGER NOT NULL,
    data_source_instance_id INTEGER NOT NULL,
    trigger_type TEXT NOT NULL,         -- 'cron', 'one-off', 'interval'
    trigger_config TEXT NOT NULL,       -- JSON string or cron expression
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (factor_definition_id) REFERENCES factor_definitions(id) ON DELETE CASCADE,
    FOREIGN KEY (data_source_instance_id) REFERENCES data_source_instances(id) ON DELETE CASCADE
);

-- Execution history for scheduled tasks
CREATE TABLE IF NOT EXISTS task_execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,           -- Reference to scheduled_tasks
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status TEXT NOT NULL,               -- 'PENDING', 'RUNNING', 'SUCCESS', 'FAILURE'
    error_message TEXT,
    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id) ON DELETE CASCADE
);

-- Indexes for tasks and logs
CREATE INDEX IF NOT EXISTS idx_task_execution_status ON task_execution_logs (task_id, status);
CREATE INDEX IF NOT EXISTS idx_task_execution_time ON task_execution_logs (start_time);
