import csv
from datetime import datetime, timedelta

def generate_csv(file_path):
    header = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    start_time = datetime(2023, 1, 1, 9, 30, 0)
    
    with open(file_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        # 1. Start low, then sharp rise to trigger BUY
        prices = [
            100.0, 100.0, 100.0, 100.0, 100.0, # Initial flat
            105.0, 106.0, 107.0, 108.0, 109.0, # Rise (fast > slow)
            110.0, 110.0, 110.0, 110.0, 110.0, # Hold
            95.0, 90.0, 85.0, 80.0, 75.0       # Sharp drop (triggers Stop Loss)
        ]
        
        for i, price in enumerate(prices):
            timestamp = (start_time + timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([timestamp, price, price+0.5, price-0.5, price, 1000])

if __name__ == '__main__':
    generate_csv('risk_sample_data.csv')
    print("risk_sample_data.csv generated.")
