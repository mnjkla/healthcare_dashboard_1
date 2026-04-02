import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_health_data(days=30, filename='health_data.csv', base_weight=70.0):
    start_date = datetime.now() - timedelta(days=days)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Randomly generate health metrics
    np.random.seed(int(base_weight))  # For reproducibility, unique per user
    steps = np.random.randint(2000, 15000, size=days)
    heart_rate = np.random.randint(60, 100, size=days)
    calories = np.round(steps * 0.04 + np.random.randint(1500, 2500, size=days), 0)
    sleep_hours = np.round(np.random.uniform(5, 9, size=days), 1)
    
    # Weight fluctuates slightly
    weight = np.round(base_weight + np.cumsum(np.random.normal(0, 0.3, size=days)), 1)
    weight = np.clip(weight, base_weight - 5.0, base_weight + 5.0)
    
    data = {
        'date': [d.strftime('%Y-%m-%d') for d in dates],
        'steps': steps,
        'heart_rate': heart_rate,
        'calories': calories,
        'sleep_hours': sleep_hours,
        'weight': weight
    }
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Generated {days} days of health data in '{filename}'.")

if __name__ == "__main__":
    users = [
        ('data_admin.csv', 70.0),
        ('data_user1.csv', 47.0),
        ('data_user2.csv', 85.0)
    ]
    for fn, bw in users:
        generate_health_data(filename=fn, base_weight=bw)
