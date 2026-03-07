import pandas as pd
from datetime import datetime, timedelta

def generate_breakout_data(file_path="breakout_test_data.csv"):
    data = []
    start_time = datetime(2023, 1, 1, 10, 0, 0)
    
    # 20 bars of sideways range around 100
    for i in range(20):
        data.append({
            "timestamp": (start_time + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"),
            "open": 100, "high": 105, "low": 95, "close": 100, "volume": 1000
        })
        
    # Bar 21: Breakout! High was 105, now close 110. ATR will be around 10.
    data.append({
        "timestamp": (start_time + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
        "open": 100, "high": 110, "low": 100, "close": 110, "volume": 1000
    })
    
    # Subsequent bars to trigger stop loss (SL: 110 - 2*10 = 90)
    data.append({
        "timestamp": (start_time + timedelta(minutes=21)).strftime("%Y-%m-%d %H:%M:%S"),
        "open": 110, "high": 110, "low": 85, "close": 85, "volume": 1000
    })
    
    # One more bar to allow the strategy to process the 85 tick and trigger SL
    data.append({
        "timestamp": (start_time + timedelta(minutes=22)).strftime("%Y-%m-%d %H:%M:%S"),
        "open": 85, "high": 85, "low": 80, "close": 80, "volume": 1000
    })
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    print(f"Generated {file_path}")

if __name__ == "__main__":
    generate_breakout_data()
