# Project Usage Guide

## Installation

1. Ensure you have Python 3.8+ installed.
2. Clone the repository.
3. (Optional) Create and activate a virtual environment.
4. Install any necessary dependencies (if applicable).

## Running a Sample Backtest

1. Generate sample data:
   ```bash
   python3 generate_sample_data.py
   ```
2. Execute the backtest script:
   ```bash
   export PYTHONPATH=$PYTHONPATH:.
   python3 run_backtest.py
   ```
3. Review results:
   The script will print signal generation logs, order submissions, and final position summaries to the console.

## Configuration

Modify `run_backtest.py` to change strategy parameters such as:
- `fast_period`
- `slow_period`
- `quantity`
- `initial_capital`
