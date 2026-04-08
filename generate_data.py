import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_health_data(days=30, filename='health_data.csv', base_weight=70.0, age=30, condition="Bình thường"):
    start_date = datetime.now() - timedelta(days=days)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    np.random.seed(int(base_weight) + age)  # For reproducibility, unique per user
    
    if condition == "Tiểu đường":
        steps = np.random.randint(1000, 6000, size=days) # Ít vận động hơn
        heart_rate = np.random.randint(65, 95, size=days)
        base_calories_multiplier = 0.03 # Trao đổi chất kém
        sleep_hours = np.round(np.random.uniform(4.5, 7.5, size=days), 1)
        weight_volatility = 0.5
    elif condition == "Tim mạch":
        steps = np.random.randint(2000, 8000, size=days)
        heart_rate = np.random.randint(75, 105, size=days) # Nhịp tim nghỉ nề cao
        base_calories_multiplier = 0.04
        sleep_hours = np.round(np.random.uniform(5, 8, size=days), 1)
        weight_volatility = 0.3
    else: # Khỏe mạnh
        steps = np.random.randint(6000, 15000, size=days)
        heart_rate = np.random.randint(60, 85, size=days)
        base_calories_multiplier = 0.045
        sleep_hours = np.round(np.random.uniform(6.5, 9, size=days), 1)
        weight_volatility = 0.2

    calories = np.round(steps * base_calories_multiplier + np.random.randint(1500, 2200, size=days), 0)
    
    # Weight fluctuates slightly
    weight = np.round(base_weight + np.cumsum(np.random.normal(0, weight_volatility, size=days)), 1)
    weight = np.clip(weight, base_weight - 5.0, base_weight + 5.0)

    # --- INJECT ANOMALIES (BẤT THƯỜNG) ---
    for i in range(days):
        # 10% xác suất bị chỉ số bất thường mỗi ngày
        if np.random.rand() < 0.10: 
            if condition == "Tim mạch":
                heart_rate[i] = np.random.randint(120, 150) # Gai nhịp tim
                sleep_hours[i] = round(np.random.uniform(3, 5), 1) # Mất ngủ
            elif condition == "Tiểu đường":
                steps[i] = np.random.randint(100, 1000) # Đuối sức
                sleep_hours[i] = round(np.random.uniform(8, 12), 1) # Ngủ li bì
            else:
                heart_rate[i] = np.random.randint(90, 110) # Hoạt động mạnh hoặc stress
                sleep_hours[i] = round(np.random.uniform(4, 5.5), 1)
    
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
    print(f"Generated {days} days of health data in '{filename}' [Condition: {condition}].")

if __name__ == "__main__":
    users = [
        ('data_admin.csv', 70.0, 28, "Bình thường"),
        ('data_user1.csv', 47.0, 45, "Tim mạch"),
        ('data_user2.csv', 85.0, 55, "Tiểu đường")
    ]
    for fn, bw, age, cond in users:
        generate_health_data(filename=fn, base_weight=bw, age=age, condition=cond)
