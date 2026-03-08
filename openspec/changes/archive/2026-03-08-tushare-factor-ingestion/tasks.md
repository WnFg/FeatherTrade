## 1. Interface Refactoring

- [x] 1.1 Update `BaseDataSource` in `src/trading_system/factors/service.py` to return `pandas.DataFrame`
- [x] 1.2 Update `BaseFactorLogic` in `src/trading_system/factors/service.py` to accept `pandas.DataFrame`
- [x] 1.3 Refactor `FileDataSource` to return a standardized DataFrame
- [x] 1.4 Refactor `MovingAverageFactor` to use pandas operations on the input DataFrame

## 2. TuShare Integration

- [x] 2.1 Implement `TuShareDataSource` with customizable `api_name` and `params`
- [x] 2.2 Add standardized column mapping (e.g., `ts_code` -> `symbol`, `trade_date` -> `timestamp`) in `TuShareDataSource`
- [x] 2.3 Implement error handling for SDK initialization and API rate limits

## 3. Factor Service Enhancements

- [x] 3.1 Implement DataFrame-to-FactorValue mapping logic in `FactorService.compute_and_store`
- [x] 3.2 Add support for batch database insertion from DataFrame results
- [x] 3.3 Update `FactorRegistry` metadata management if needed for TuShare specific parameters

## 4. Verification

- [x] 4.1 Create unit tests for `TuShareDataSource` using mocks for the TuShare SDK
- [x] 4.2 Create integration tests for the full ingestion pipeline: TuShare -> Logic -> Database
- [x] 4.3 Verify `FileDataSource` still works correctly with the new DataFrame interface
