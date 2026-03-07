import csv
from datetime import datetime, timedelta

def generate_csv(file_path):
    header = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    start_time = datetime(2023, 1, 1, 9, 30, 0)
    
    with open(file_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        # Generate 30 bars. 
        # First 15 bars: price going down.
        # Next 15 bars: price going up.
        price = 100.0
        for i in range(30):
            timestamp = (start_time + timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M:%S')
            
            if i < 15:
                price -= 1.0
            else:
                price += 2.0
                
            writer.writerow([timestamp, price, price+0.5, price-0.5, price, 1000])

if __name__ == '__main__':
    generate_csv('sample_data.csv')
    print("sample_data.csv generated.")
