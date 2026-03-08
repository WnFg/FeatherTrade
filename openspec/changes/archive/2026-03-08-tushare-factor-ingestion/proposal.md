## Why

The current factor system relies on local CSV files or simulated API data. To support real-world quantitative analysis, we need to integrate with professional financial data providers like TuShare. This integration requires a standardized interface where all data sources (file or API) return data in a `pandas.DataFrame` format, and allows for customizable, parameter-driven data ingestion strategies.

## What Changes

- **TuShare Data Source**: Implement a new `TuShareDataSource` using the TuShare SDK to fetch market and financial data.
- **DataFrame Standardization**: Refactor the `BaseDataSource` interface to ensure `fetch_data` returns a `pandas.DataFrame` instead of a list of dictionaries.
- **Customizable Ingestion Strategy**: Introduce a mechanism to instantiate data sources with specific query parameters (e.g., fields, date offsets, filtering conditions) to create tailored ingestion instances.
- **Factor Mapping**: Logic to convert the standardized DataFrame results into the internal `FactorValue` storage format.

## Capabilities

### New Capabilities
- `tushare-data-source`: Integration with the TuShare SDK for professional financial data fetching.
- `customizable-ingestion`: Support for generating data source instances based on specific query strategies and parameters.

### Modified Capabilities
- `factor-registry`: Update the ingestion logic to handle `pandas.DataFrame` inputs and mapping to database records.

## Impact

- **`src/trading_system/factors/service.py`**: Changes to `BaseDataSource` and implementation of the DataFrame mapping logic.
- **Dependencies**: Addition of `tushare` and `pandas` to the project dependencies.
- **Factor Database**: Potential updates to the insertion logic to handle batch DataFrame writes efficiently.
