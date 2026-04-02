import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import os
import json
import glob

print("""
==================================================
🤖 GIẢ LẬP IOT (MULTI-USER HUB)
==================================================
""")

def simulate_all_devices(interval_seconds=5):
    print(f"Bắt đầu đồng bộ cho TẤT CẢ thiết bị mỗi {interval_seconds} giây...\n")
    
    files = glob.glob('data_*.csv')
    if not files:
        print("Không tìm thấy file dữ liệu người dùng. Đang khởi tạo gốc...")
        import generate_data
        # Khởi tạo mặc định nếu user chưa chạy bên ngoài
        pass
        
    while True:
        try:
            files = glob.glob('data_*.csv')
            for file_path in files:
                username = file_path.replace('data_', '').replace('.csv', '')
                df = pd.read_csv(file_path)
                last_date_str = df['date'].iloc[-1]
                last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
                current_date = datetime.now().date()
                last_weight = float(df['weight'].iloc[-1])
                
                target_weight = last_weight
                sim_config_file = f'sim_config_{username}.json'
                if os.path.exists(sim_config_file):
                    with open(sim_config_file, 'r') as f:
                        try:
                            config = json.load(f)
                            target_weight = config.get('target_weight', last_weight)
                        except: pass
                
                weight_diff = target_weight - last_weight
                new_weight = round(last_weight + (weight_diff * 0.1) + np.random.normal(0, 0.1), 1)

                if last_date > current_date:
                    df['p_date'] = pd.to_datetime(df['date']).dt.date
                    df = df[df['p_date'] <= current_date]
                    df = df.drop(columns=['p_date'])
                    if not df.empty:
                        df.to_csv(file_path, index=False)
                    continue
                    
                elif last_date < current_date:
                    next_date = last_date + timedelta(days=1)
                    new_steps = np.random.randint(100, 2000)
                    new_hr = np.random.randint(60, 100)
                    new_sleep = round(np.random.uniform(5, 9), 1)
                    new_cal = round(new_steps*0.04 + np.random.randint(1500,2000), 0)
                    
                    new_row = {
                        'date': next_date.strftime('%Y-%m-%d'),
                        'steps': new_steps, 'heart_rate': new_hr, 'calories': new_cal,
                        'sleep_hours': new_sleep, 'weight': new_weight
                    }
                    pd.DataFrame([new_row]).to_csv(file_path, mode='a', header=False, index=False)
                    print(f"🌅 [{username}] Sang ngày mới ({new_row['date']}).")
                    
                else:
                    curr_steps = int(df.iloc[-1]['steps'])
                    new_steps = min(curr_steps + np.random.randint(5, 30), 40000)
                    new_hr = np.random.randint(60, 100)
                    new_cal = round(new_steps*0.04 + np.random.randint(1500,2000), 0)
                    
                    df.iloc[-1, df.columns.get_loc('steps')] = new_steps
                    df.iloc[-1, df.columns.get_loc('heart_rate')] = new_hr
                    df.iloc[-1, df.columns.get_loc('weight')] = new_weight
                    df.iloc[-1, df.columns.get_loc('calories')] = new_cal
                    
                    df.to_csv(file_path, index=False)
                    print(f"📡 [{username}] Bước={new_steps} | Nhịp tim={new_hr} | Cân={new_weight}")
            
            time.sleep(interval_seconds)
            
        except Exception as e:
            print(f"Lỗi Simulator: {e}")
            time.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        simulate_all_devices(interval_seconds=5)
    except KeyboardInterrupt:
        print("\nĐã tắt thiết bị Hub.")
