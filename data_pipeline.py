"""
data_pipeline.py
================
Pipeline xử lý dữ liệu thực tế từ:
  - Fitbit Kaggle Dataset (dailyActivity, sleep, weight)
  - Cardiovascular Disease 70k Dataset (cardio_train.csv)

Đầu ra:
  - data_admin.csv / data_user1.csv / data_user2.csv (format chuẩn dashboard)
  - reference_thresholds.json   (ngưỡng y khoa theo tuổi/giới)
  - data_quality_report.txt     (báo cáo chất lượng dữ liệu)
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta

# ─── Đường dẫn ───────────────────────────────────────────────────────────────
FITBIT_PATH_1 = r"dataset\mturkfitbit_export_3.12.16-4.11.16\Fitabase Data 3.12.16-4.11.16"
FITBIT_PATH_2 = r"dataset\mturkfitbit_export_4.12.16-5.12.16\Fitabase Data 4.12.16-5.12.16"
CARDIO_PATH   = r"dataset\cardio_train.csv"

# ─── BƯỚC 1: Load & Merge Fitbit data ────────────────────────────────────────

def load_fitbit_daily(path1, path2):
    """Merge dailyActivity từ 2 export batch, trả về DataFrame đã clean."""
    da1 = pd.read_csv(f"{path1}/dailyActivity_merged.csv")
    da2 = pd.read_csv(f"{path2}/dailyActivity_merged.csv")
    da  = pd.concat([da1, da2], ignore_index=True)
    da['ActivityDate'] = pd.to_datetime(da['ActivityDate'])
    da = da.rename(columns={
        'Id': 'user_id',
        'ActivityDate': 'date',
        'TotalSteps': 'steps',
        'Calories': 'calories',
        'VeryActiveMinutes': 'very_active_min',
        'FairlyActiveMinutes': 'fairly_active_min',
        'LightlyActiveMinutes': 'lightly_active_min',
        'SedentaryMinutes': 'sedentary_min'
    })
    # Lọc bỏ ngày steps=0 (thiết bị không đeo)
    da = da[da['steps'] > 0]
    da = da[['user_id', 'date', 'steps', 'calories',
             'very_active_min', 'fairly_active_min', 'lightly_active_min', 'sedentary_min']]
    return da

def load_fitbit_sleep(path2):
    """Load sleepDay, chuyển TotalMinutesAsleep → sleep_hours."""
    sl = pd.read_csv(f"{path2}/sleepDay_merged.csv")
    sl['SleepDay'] = pd.to_datetime(sl['SleepDay'].str.split(' ').str[0])
    sl = sl.rename(columns={'Id': 'user_id', 'SleepDay': 'date',
                             'TotalMinutesAsleep': 'sleep_minutes',
                             'TotalTimeInBed': 'time_in_bed'})
    sl['sleep_hours'] = (sl['sleep_minutes'] / 60).round(1)
    sl['sleep_efficiency'] = (sl['sleep_minutes'] / sl['time_in_bed'] * 100).round(1)
    sl = sl[['user_id', 'date', 'sleep_hours', 'sleep_efficiency']]
    return sl

def load_fitbit_weight(path2):
    """Load weightLogInfo với BMI thực tế."""
    wt = pd.read_csv(f"{path2}/weightLogInfo_merged.csv")
    wt['Date'] = pd.to_datetime(wt['Date'].str.split(' ').str[0])
    wt = wt.rename(columns={'Id': 'user_id', 'Date': 'date',
                             'WeightKg': 'weight', 'BMI': 'bmi_real'})
    wt = wt[['user_id', 'date', 'weight', 'bmi_real']]
    return wt

def merge_fitbit(da, sl, wt):
    """Merge 3 tables theo user_id + date."""
    merged = da.merge(sl, on=['user_id', 'date'], how='left')
    merged = merged.merge(wt, on=['user_id', 'date'], how='left')

    # Forward-fill weight (nhiều ngày không log cân)
    merged = merged.sort_values(['user_id', 'date'])
    merged['weight'] = merged.groupby('user_id')['weight'].ffill().bfill()

    # Impute sleep nếu thiếu (median per user)
    merged['sleep_hours'] = merged.groupby('user_id')['sleep_hours'].transform(
        lambda x: x.fillna(x.median())
    )
    merged['sleep_efficiency'] = merged['sleep_efficiency'].fillna(85.0)

    return merged

# ─── BƯỚC 2: Build Reference Thresholds từ Cardio 70k ────────────────────────

def build_reference_thresholds(cardio_path):
    """
    Từ 70k bệnh nhân thực tế → tính ngưỡng huyết áp bình thường
    theo nhóm tuổi + giới tính. Dùng để calibrate anomaly detection.
    """
    cd = pd.read_csv(cardio_path, sep=';')

    # Chuyển age từ ngày → năm
    cd['age_years'] = (cd['age'] / 365).astype(int)

    # Loại bỏ outliers huyết áp không thực tế
    cd = cd[(cd['ap_hi'] >= 80) & (cd['ap_hi'] <= 250)]
    cd = cd[(cd['ap_lo'] >= 40) & (cd['ap_lo'] <= 150)]

    # Tạo nhóm tuổi
    cd['age_group'] = pd.cut(cd['age_years'],
                              bins=[0, 30, 40, 50, 60, 70, 100],
                              labels=['<30', '30-40', '40-50', '50-60', '60-70', '70+'])

    # Tính ngưỡng theo từng nhóm (percentile 5-95 của người KHÔNG bệnh tim)
    healthy = cd[cd['cardio'] == 0]
    thresholds = {}
    for grp in healthy['age_group'].cat.categories:
        sub = healthy[healthy['age_group'] == grp]
        if len(sub) < 10:
            continue
        thresholds[str(grp)] = {
            'ap_hi_normal':  [float(sub['ap_hi'].quantile(0.10)), float(sub['ap_hi'].quantile(0.90))],
            'ap_lo_normal':  [float(sub['ap_lo'].quantile(0.10)), float(sub['ap_lo'].quantile(0.90))],
            'ap_hi_warning': float(sub['ap_hi'].quantile(0.90)),
            'ap_hi_danger':  float(sub['ap_hi'].quantile(0.95)),
            'bmi_mean':      float(sub['weight'].mean() / ((sub['height'].mean() / 100) ** 2)),
            'sample_count':  len(sub)
        }

    # Phân phối glucose từ cardio dataset (1=normal, 2=above, 3=well above)
    glucose_dist = cd['gluc'].value_counts(normalize=True).to_dict()
    thresholds['glucose_distribution'] = {str(k): round(v, 3) for k, v in glucose_dist.items()}

    # Tỷ lệ bệnh tim theo nhóm tuổi
    cardio_rate = cd.groupby('age_group')['cardio'].mean().round(3)
    thresholds['cardio_risk_by_age'] = cardio_rate.to_dict()

    return thresholds

# ─── BƯỚC 3: Mô phỏng dữ liệu user theo profile hồ sơ bệnh lý ──────────────

def assign_user_profile(fitbit_df, user_id, profile):
    """
    Lấy dữ liệu Fitbit của 1 user cụ thể (user_id từ dataset),
    thêm các chỉ số bệnh lý (heart_rate, huyết áp mô phỏng) phù hợp với condition.
    """
    user_data = fitbit_df[fitbit_df['user_id'] == user_id].copy()
    if user_data.empty:
        return None

    user_data = user_data.sort_values('date').reset_index(drop=True)
    n = len(user_data)
    np.random.seed(profile['age'] + hash(profile['condition']) % 1000)

    condition = profile['condition']
    age = profile['age']

    # ─ Nhịp tim (dựa trên condition + age) ─
    if condition == 'Tim mạch':
        base_hr = min(60 + age * 0.3 + 15, 100)  # Người tim mạch HR cao hơn
        hr_std  = 12
    elif condition == 'Tiểu đường':
        base_hr = 60 + age * 0.2 + 5
        hr_std  = 10
    else:  # Bình thường
        base_hr = max(55, 75 - age * 0.1)
        hr_std  = 8

    heart_rate = np.random.normal(base_hr, hr_std, n).clip(45, 140).astype(int)

    # ─ Inject bất thường thực tế (tần suất theo condition) ─
    anomaly_rate = 0.15 if condition == 'Tim mạch' else 0.10 if condition == 'Tiểu đường' else 0.05
    for i in range(n):
        if np.random.rand() < anomaly_rate:
            if condition == 'Tim mạch':
                heart_rate[i] = np.random.randint(118, 148)
                user_data.loc[i, 'sleep_hours'] = round(np.random.uniform(3.0, 5.2), 1)
            elif condition == 'Tiểu đường':
                user_data.loc[i, 'steps'] = np.random.randint(100, 1500)
                user_data.loc[i, 'sleep_hours'] = round(np.random.uniform(8.5, 11.0), 1)
            else:
                heart_rate[i] = np.random.randint(92, 112)

    user_data['heart_rate'] = heart_rate

    # ─ Chuẩn hóa cân nặng theo profile ─
    if 'base_weight' in profile and not user_data['weight'].isna().all():
        # Scale weight về đúng với profile người dùng
        original_mean = user_data['weight'].mean()
        scale = profile['base_weight'] / original_mean
        user_data['weight'] = (user_data['weight'] * scale).round(1)

    # Chuẩn hóa ngày về hiện tại (shift về 90 ngày gần nhất)
    date_range = pd.date_range(end=datetime.now(), periods=n, freq='D')
    user_data['date'] = date_range

    # Đảm bảo sleep_hours hợp lệ
    user_data['sleep_hours'] = user_data['sleep_hours'].clip(2.0, 12.0)

    # Chọn cột cuối
    result = user_data[['date', 'steps', 'heart_rate', 'calories', 'sleep_hours', 'weight']].copy()
    result['date'] = result['date'].dt.strftime('%Y-%m-%d')

    return result

# ─── BƯỚC 4: Data Quality Report ─────────────────────────────────────────────

def generate_quality_report(raw_da, raw_sl, raw_wt, cardio_df, output_file='data_quality_report.txt'):
    lines = []
    lines.append("=" * 60)
    lines.append("  DATA QUALITY REPORT — Healthcare Dashboard")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    lines.append("\n[1] FITBIT — Daily Activity")
    lines.append(f"  Rows: {len(raw_da)}, Users: {raw_da['user_id'].nunique()}")
    lines.append(f"  Date range: {raw_da['date'].min().date()} → {raw_da['date'].max().date()}")
    missing_steps = (raw_da['steps'] == 0).sum()
    lines.append(f"  Rows with 0 steps (removed): {missing_steps}")
    lines.append(f"  Steps range: {raw_da['steps'].min()} – {raw_da['steps'].max()}")
    lines.append(f"  Calories range: {raw_da['calories'].min()} – {raw_da['calories'].max()}")

    lines.append("\n[2] FITBIT — Sleep Data")
    lines.append(f"  Rows: {len(raw_sl)}, Users: {raw_sl['user_id'].nunique()}")
    lines.append(f"  Missing sleep records (imputed): {raw_da['user_id'].nunique() * 30 - len(raw_sl)} (estimate)")
    lines.append(f"  Sleep hours range: {raw_sl['sleep_hours'].min()} – {raw_sl['sleep_hours'].max()} h")
    lines.append(f"  Avg sleep efficiency: {raw_sl['sleep_efficiency'].mean():.1f}%")

    lines.append("\n[3] FITBIT — Weight Log")
    lines.append(f"  Rows: {len(raw_wt)}, Users: {raw_wt['user_id'].nunique()}")
    lines.append(f"  Weight range: {raw_wt['weight'].min()} – {raw_wt['weight'].max()} kg")
    lines.append(f"  BMI range: {raw_wt['bmi_real'].min():.1f} – {raw_wt['bmi_real'].max():.1f}")

    lines.append("\n[4] CARDIOVASCULAR DISEASE — 70,000 patients")
    lines.append(f"  Rows: {len(cardio_df)}, Columns: {cardio_df.shape[1]}")
    cardio_df['age_years'] = (cardio_df['age'] / 365).astype(int)
    lines.append(f"  Age range: {cardio_df['age_years'].min()} – {cardio_df['age_years'].max()} years")
    cardio_df_clean = cardio_df[(cardio_df['ap_hi']>=80) & (cardio_df['ap_hi']<=250)]
    outlier_bp = len(cardio_df) - len(cardio_df_clean)
    lines.append(f"  BP outliers removed: {outlier_bp} rows ({outlier_bp/len(cardio_df)*100:.1f}%)")
    lines.append(f"  Cardio disease rate: {cardio_df['cardio'].mean()*100:.1f}%")
    lines.append(f"  Normal SBP (p10-p90): {cardio_df_clean['ap_hi'].quantile(0.10):.0f} – {cardio_df_clean['ap_hi'].quantile(0.90):.0f} mmHg")

    lines.append("\n" + "=" * 60)
    lines.append("  ✅ Pipeline completed successfully")
    lines.append("=" * 60)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('\n'.join(lines))

# ─── MAIN: Chạy toàn bộ pipeline ─────────────────────────────────────────────

def run_pipeline():
    print("🔄 Loading Fitbit datasets...")
    da = load_fitbit_daily(FITBIT_PATH_1, FITBIT_PATH_2)
    sl = load_fitbit_sleep(FITBIT_PATH_2)
    wt = load_fitbit_weight(FITBIT_PATH_2)

    print(f"   dailyActivity: {len(da)} rows, {da['user_id'].nunique()} users")
    print(f"   sleep: {len(sl)} rows")
    print(f"   weight: {len(wt)} rows")

    print("\n🔗 Merging Fitbit data...")
    fitbit_df = merge_fitbit(da, sl, wt)
    print(f"   Merged: {len(fitbit_df)} rows")

    print("\n📊 Building reference thresholds from Cardio 70k...")
    thresholds = build_reference_thresholds(CARDIO_PATH)
    with open('reference_thresholds.json', 'w', encoding='utf-8') as f:
        json.dump(thresholds, f, indent=2, ensure_ascii=False)
    print(f"   Thresholds for {len([k for k in thresholds if k not in ('glucose_distribution','cardio_risk_by_age')])} age groups saved.")

    # Chọn users Fitbit có đủ dữ liệu (>= 60 ngày)
    user_counts = fitbit_df.groupby('user_id')['date'].count()
    valid_users = user_counts[user_counts >= 60].index.tolist()
    print(f"\n👥 Valid Fitbit users (≥60 days): {len(valid_users)}")

    # Mapping profile người dùng dashboard
    PROFILES = {
        'admin': {
            'user_id': valid_users[0] if len(valid_users) > 0 else fitbit_df['user_id'].iloc[0],
            'age': 28, 'gender': 'Nam', 'condition': 'Bình thường',
            'base_weight': 70.0, 'height': 170
        },
        'user1': {
            'user_id': valid_users[1] if len(valid_users) > 1 else fitbit_df['user_id'].iloc[-1],
            'age': 45, 'gender': 'Nữ', 'condition': 'Tim mạch',
            'base_weight': 60.0, 'height': 160
        },
        'user2': {
            'user_id': valid_users[2] if len(valid_users) > 2 else fitbit_df['user_id'].iloc[len(fitbit_df)//2],
            'age': 55, 'gender': 'Nam', 'condition': 'Tiểu đường',
            'base_weight': 85.0, 'height': 175
        }
    }

    print("\n💾 Generating per-user CSV files...")
    for username, profile in PROFILES.items():
        df_user = assign_user_profile(fitbit_df, profile['user_id'], profile)
        if df_user is None or len(df_user) < 30:
            print(f"   ⚠️  {username}: không đủ data, fallback sang user khác")
            # Fallback: lấy user có nhiều dữ liệu nhất
            fallback_id = user_counts.idxmax()
            df_user = assign_user_profile(fitbit_df, fallback_id, profile)
        # Lấy 90 ngày gần nhất
        df_user = df_user.tail(90).reset_index(drop=True)
        output_path = f"data_{username}.csv"
        df_user.to_csv(output_path, index=False)
        print(f"   ✅ {output_path}: {len(df_user)} ngày, condition={profile['condition']}")

    print("\n📋 Generating data quality report...")
    raw_sl_for_report = sl.copy()
    raw_sl_for_report['sleep_hours'] = raw_sl_for_report['sleep_hours']
    cardio_raw = pd.read_csv(CARDIO_PATH, sep=';')
    generate_quality_report(da.rename(columns={'user_id':'user_id'}), raw_sl_for_report, wt, cardio_raw)

    print("\n🎉 Pipeline hoàn tất!")
    print("   Files tạo ra:")
    print("   - data_admin.csv, data_user1.csv, data_user2.csv (dữ liệu thực Fitbit)")
    print("   - reference_thresholds.json (ngưỡng y khoa từ 70k bệnh nhân)")
    print("   - data_quality_report.txt (báo cáo chất lượng dữ liệu)")

if __name__ == '__main__':
    run_pipeline()
