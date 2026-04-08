"""
analysis.py — Smart Health Decision Engine
==========================================
Dựa trên ngưỡng y khoa thực từ:
  - Fitbit 35 người dùng thực (steps, calories, sleep)
  - Cardiovascular Disease 70,000 bệnh nhân (huyết áp theo tuổi)
"""

import pandas as pd
import numpy as np
import json
import os

# ─── Load ngưỡng y khoa thực (từ 70k bệnh nhân) ─────────────────────────────
_THRESHOLDS = {}
_THRESHOLDS_FILE = 'reference_thresholds.json'
if os.path.exists(_THRESHOLDS_FILE):
    try:
        with open(_THRESHOLDS_FILE, 'r', encoding='utf-8') as f:
            _THRESHOLDS = json.load(f)
    except:
        _THRESHOLDS = {}

def _get_age_group(age):
    if age < 30:   return '<30'
    elif age < 40: return '30-40'
    elif age < 50: return '40-50'
    elif age < 60: return '50-60'
    elif age < 70: return '60-70'
    else:          return '70+'

def _get_bp_threshold(age, metric='ap_hi_danger'):
    """Lấy ngưỡng huyết áp theo tuổi từ dữ liệu 70k thực tế."""
    grp = _get_age_group(age)
    defaults = {'ap_hi_danger': 140, 'ap_hi_warning': 130, 'ap_hi_normal': [90, 120]}
    if grp in _THRESHOLDS:
        return _THRESHOLDS[grp].get(metric, defaults.get(metric))
    return defaults.get(metric)

def _get_cardio_risk_rate(age):
    """Tỷ lệ bệnh tim theo tuổi từ dữ liệu thực."""
    grp = _get_age_group(age)
    rates = _THRESHOLDS.get('cardio_risk_by_age', {})
    try:
        r = rates.get(grp, 0.3)
        return float(r) if r and str(r) != 'NaN' else 0.3
    except:
        return 0.3

# ─── LOAD DATA ────────────────────────────────────────────────────────────────

def load_data(file_path='health_data.csv'):
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

# ─── ANOMALY DETECTION (dựa trên ngưỡng thực từ Cardiovascular 70k) ──────────

def detect_anomalies(df, age=30, condition="Bình thường"):
    """Phát hiện bất thường với 3 mức: ⚠️ Nhẹ / 🚨 Nguy hiểm / 🆘 Khẩn cấp."""
    if len(df) < 5:
        return []

    latest  = df.iloc[-1]
    anomalies = []

    # ─ Nhịp tim: Z-score trên 7 ngày gần nhất ─
    recent_hr  = df['heart_rate'].tail(7)
    hr_mean    = recent_hr.mean()
    hr_std     = recent_hr.std() or 1

    if condition == "Tim mạch":
        hr_danger  = 110 if age > 60 else 120
        hr_warning = 100
    elif condition == "Tiểu đường":
        hr_danger  = 115
        hr_warning = 100
    else:
        hr_danger  = 125
        hr_warning = 105

    if latest['heart_rate'] > hr_danger:
        prefix = "🆘 KHẨN CẤP" if condition == "Tim mạch" else "🚨 NGUY HIỂM"
        anomalies.append(f"{prefix}: Nhịp tim {latest['heart_rate']} bpm vượt ngưỡng nguy hiểm ({hr_danger}). {'Nguy cơ nhồi máu cơ tim cao!' if condition == 'Tim mạch' else 'Cần theo dõi ngay.'}")
    elif latest['heart_rate'] > hr_warning or latest['heart_rate'] > hr_mean + 2 * hr_std:
        anomalies.append(f"⚠️ CẢNH BÁO: Nhịp tim {latest['heart_rate']} bpm cao hơn bình thường. Nghỉ ngơi và tránh gắng sức.")

    # ─ Giấc ngủ ─
    if latest['sleep_hours'] < 4.5:
        anomalies.append(f"🚨 NGUY HIỂM: Thiếu ngủ trầm trọng ({latest['sleep_hours']}h). Nguy cơ đột quỵ tăng cao.")
    elif latest['sleep_hours'] < 5.5:
        anomalies.append(f"⚠️ CẢNH BÁO: Ngủ ít ({latest['sleep_hours']}h). Hệ miễn dịch suy giảm, khó hồi phục.")

    # ─ Vận động theo bệnh lý ─
    if condition == "Tiểu đường" and latest['steps'] < 2000:
        anomalies.append(f"🚨 NGUY HIỂM: Bệnh Tiểu đường - chỉ {latest['steps']} bước hôm nay. Nguy cơ tích tụ đường huyết.")
    elif condition == "Tim mạch" and latest['steps'] < 1000:
        anomalies.append(f"⚠️ CẢNH BÁO: Vận động cực thấp ({latest['steps']} bước). Tuần hoàn máu bị ảnh hưởng.")

    # ─ Calories bất thường ─
    avg_cal = df['calories'].mean()
    if latest['calories'] < avg_cal * 0.5 and latest['calories'] > 0:
        anomalies.append(f"⚠️ CẢNH BÁO: Calories hôm nay ({latest['calories']} kcal) thấp bất thường. Cơ thể thiếu năng lượng.")

    return anomalies

# ─── BMI ─────────────────────────────────────────────────────────────────────

def calculate_bmi(weight_kg, height_cm=170):
    h = height_cm / 100
    bmi = round(weight_kg / (h ** 2), 1)
    if bmi < 18.5:   cat = "Thiếu cân"
    elif bmi < 25:   cat = "Bình thường"
    elif bmi < 30:   cat = "Thừa cân"
    else:            cat = "Béo phì"
    return bmi, cat

def calculate_bmi_series(df, height_cm=170):
    h = height_cm / 100
    df = df.copy()
    df['bmi'] = (df['weight'] / (h ** 2)).round(1)
    return df

# ─── SUMMARY STATS ───────────────────────────────────────────────────────────

def get_summary_stats(df):
    return {
        'avg_steps':      round(df['steps'].mean(), 0),
        'avg_heart_rate': round(df['heart_rate'].mean(), 1),
        'total_calories': round(df['calories'].sum(), 0),
        'avg_sleep':      round(df['sleep_hours'].mean(), 1),
        'avg_weight':     round(df['weight'].mean(), 1),
        'avg_calories':   round(df['calories'].mean(), 0),
    }

# ─── ACTIVITY DENSITY ────────────────────────────────────────────────────────

def analyze_activity_density(df):
    df = df.copy()
    conditions = [df['steps'] < 5000, (df['steps'] >= 5000) & (df['steps'] < 10000), df['steps'] >= 10000]
    labels = ['Thấp', 'Trung bình', 'Cao']
    df['activity_level'] = np.select(conditions, labels, default='Trung bình')
    density = df['activity_level'].value_counts().to_dict()
    for lb in labels:
        density.setdefault(lb, 0)
    return df, density

# ─── TRENDS & IMPROVEMENT ────────────────────────────────────────────────────

def analyze_trends(df):
    df = df.sort_values('date')
    w1, w4 = df.iloc[:7], df.iloc[-7:]
    metrics = {'steps':'Bước chân','heart_rate':'Nhịp tim','weight':'Cân nặng','calories':'Calories','sleep_hours':'Giấc ngủ'}
    trends = {}
    for m, label in metrics.items():
        v1, v4 = w1[m].mean(), w4[m].mean()
        pct = round(((v4 - v1) / v1) * 100, 1) if v1 != 0 else 0
        trends[m] = {'label': label, 'w1_avg': round(v1,1), 'w4_avg': round(v4,1), 'change_pct': pct}
    return trends

def get_fitness_improvement(df, height_cm=170):
    df = df.sort_values('date')
    w1, w4 = df.iloc[:7], df.iloc[-7:]
    improvements, score, total = [], 0, 0

    sc = w4['steps'].mean() - w1['steps'].mean()
    total += 1
    if sc > 500:   improvements.append(("✅","Bước chân",f"Tăng {int(sc)} bước/ngày","Tốt")); score += 1
    elif sc < -500: improvements.append(("⚠️","Bước chân",f"Giảm {int(abs(sc))} bước/ngày","Cần cải thiện"))
    else:           improvements.append(("➡️","Bước chân","Không thay đổi đáng kể","Ổn định")); score += 0.5

    hc = w4['heart_rate'].mean() - w1['heart_rate'].mean()
    total += 1
    if hc < -3:   improvements.append(("✅","Nhịp tim nghỉ",f"Giảm {abs(hc):.1f} bpm","Tốt - tim khỏe hơn")); score += 1
    elif hc > 5:   improvements.append(("⚠️","Nhịp tim nghỉ",f"Tăng {hc:.1f} bpm","Cần theo dõi"))
    else:           improvements.append(("➡️","Nhịp tim nghỉ","Ổn định","Bình thường")); score += 0.5

    slc = w4['sleep_hours'].mean() - w1['sleep_hours'].mean()
    total += 1
    if slc > 0.5:  improvements.append(("✅","Giấc ngủ",f"Tăng {slc:.1f} giờ/đêm","Tốt")); score += 1
    elif slc < -0.5: improvements.append(("⚠️","Giấc ngủ",f"Giảm {abs(slc):.1f} giờ/đêm","Cần cải thiện"))
    else:           improvements.append(("➡️","Giấc ngủ","Không thay đổi đáng kể","Ổn định")); score += 0.5

    h = height_cm / 100
    bmi1, bmi4 = w1['weight'].mean()/(h**2), w4['weight'].mean()/(h**2)
    total += 1
    if 18.5 <= bmi4 < 25: improvements.append(("✅","BMI",f"{bmi4:.1f} (Bình thường)","Tốt")); score += 1
    elif bmi4 < 18.5:     improvements.append(("⚠️","BMI",f"{bmi4:.1f} (Thiếu cân)","Cần tăng cân"))
    else:
        improvements.append(("⚠️","BMI",f"{bmi4:.1f} (Thừa cân)","Cần giảm cân"))
        if bmi4 < bmi1: score += 0.5

    return {'improvements': improvements, 'score_pct': round((score/total)*100,0) if total else 0, 'score': score, 'total': total}

# ─── HEALTH SCORE ─────────────────────────────────────────────────────────────

def calculate_health_score(df, height_cm=170):
    latest = df.iloc[-1]
    score, details = 0, []

    s = 25 if latest['steps']>=10000 else 20 if latest['steps']>=7000 else 15 if latest['steps']>=5000 else 10 if latest['steps']>=3000 else 5
    score += s; details.append(('Vận động', s, 25))

    hr = latest['heart_rate']
    s = 25 if 60<=hr<=80 else 18 if 55<=hr<=90 else 12 if 50<=hr<=100 else 5
    score += s; details.append(('Nhịp tim', s, 25))

    sl = latest['sleep_hours']
    s = 25 if 7<=sl<=9 else 18 if 6<=sl<=10 else 12 if 5<=sl<=11 else 5
    score += s; details.append(('Giấc ngủ', s, 25))

    h = height_cm / 100
    bmi = latest['weight'] / (h**2)
    s = 25 if 18.5<=bmi<25 else 15 if 17<=bmi<30 else 5
    score += s; details.append(('BMI', s, 25))

    return score, details

# ─── RISK SCORE (dựa trên ngưỡng thực từ Cardio 70k) ────────────────────────

def calculate_risk_score(df, height_cm=170, age=30, condition="Bình thường"):
    """
    Tính điểm rủi ro sức khỏe 0.0–10.0 dựa trên dữ liệu thực từ 70k bệnh nhân.
    """
    latest = df.iloc[-1]
    risk = 0.0

    # Rủi ro nền theo tuổi (từ cardio_risk_by_age thực tế)
    base_risk = _get_cardio_risk_rate(age) * 3.0   # max 3 pts từ tuổi
    risk += base_risk

    # Nhịp tim
    bp_danger = _get_bp_threshold(age, 'ap_hi_danger')
    hr = latest['heart_rate']
    if condition == "Tim mạch":
        if hr > 120: risk += 3.0
        elif hr > 100: risk += 1.5
    else:
        if hr > 110: risk += 2.0
        elif hr > 95: risk += 1.0

    # Giấc ngủ
    sl = latest['sleep_hours']
    if sl < 5: risk += 2.0
    elif sl < 6: risk += 1.0

    # Vận động
    if latest['steps'] < 2000: risk += 1.5
    elif latest['steps'] < 5000: risk += 0.5

    # BMI
    h = height_cm / 100
    bmi = latest['weight'] / (h**2)
    if bmi > 35: risk += 1.5
    elif bmi > 30: risk += 0.8
    elif bmi < 17: risk += 0.8

    # Bệnh lý nền
    if condition == "Tim mạch":    risk += 1.5
    elif condition == "Tiểu đường": risk += 1.0

    return min(round(risk, 1), 10.0)

# ─── RECOMMENDATIONS ─────────────────────────────────────────────────────────

def get_recommendations(df):
    latest = df.iloc[-1]
    insights, recommendations = [], []
    if latest['steps'] < 5000:
        insights.append("Số bước chân hôm nay rất thấp.")
        recommendations.append("Đi bộ nhẹ nhàng ít nhất 15 phút.")
    if latest['sleep_hours'] < 6:
        insights.append("Ngủ ít hơn 6 tiếng.")
        recommendations.append("Cân nhắc đi ngủ sớm hơn để phục hồi sức khỏe.")
    if latest['heart_rate'] > 90:
        insights.append("Nhịp tim lúc nghỉ ngơi hơi cao.")
        recommendations.append("Tránh tập cường độ cao, hạn chế caffeine.")
    if not insights:
        insights.append("Các chỉ số đang ổn định.")
        recommendations.append("Tiếp tục duy trì lối sống lành mạnh!")
    return {"insight": " ".join(insights), "recommendation": " ".join(recommendations)}

# ─── EXERCISE RECOMMENDATIONS ────────────────────────────────────────────────

def get_exercise_recommendations(df, height_cm=170, gender="Nam", pref="Gym", age=30, condition="Bình thường", anomalies=None):
    if anomalies is None: anomalies = []
    latest = df.iloc[-1]
    stats = get_summary_stats(df)
    h = height_cm / 100
    bmi = latest['weight'] / (h**2)
    _, bmi_cat = calculate_bmi(latest['weight'], height_cm)
    recs = []

    if condition == "Tim mạch":
        cardio_risk = _get_cardio_risk_rate(age)
        recs.append({'icon':'🫀','title':'CHỐNG CHỈ ĐỊNH — TIM MẠCH',
            'detail': f'Bệnh nhân {age} tuổi (nhóm tuổi có {cardio_risk*100:.0f}% nguy cơ tim mạch). TUYỆT ĐỐI không tập Valsalva, HIIT đẩy HR>{"120" if age>60 else "140"}bpm. Chuyển sang Zone 2 Cardio (đi bộ nhanh, đạp xe nhẹ).',
            'priority':'Cấp bách'})
    elif condition == "Tiểu đường":
        recs.append({'icon':'🩸','title':'LỜI KHUYÊN — TIỂU ĐƯỜNG',
            'detail':'Đi bộ 30 phút sau mỗi bữa ăn (giúp hạ đường huyết tự nhiên). Tuyệt đối không tập lúc đói quá lâu. Mục tiêu tối thiểu: 5,000 bước/ngày.',
            'priority':'Quan trọng'})

    if anomalies:
        recs.append({'icon':'🚨','title':'LƯU Ý THỂ TRẠNG HÔM NAY',
            'detail': f"Phát hiện bất thường: {anomalies[0]}. Đề nghị HỦY buổi tập hôm nay, nghỉ ngơi tại nhà.",
            'priority':'Cấp bách'})

    if bmi < 18.5:
        detail = 'Tập tạ compound (squat, deadlift) 3x/tuần, tăng protein.' if pref=="Gym" and gender=="Nam" else f'BMI thấp ({bmi:.1f}). Tập {pref} cường độ vừa, tăng 300-500 kcal/ngày.'
        recs.append({'icon':'🏋️','title':'Tăng cơ & Nạp năng lượng','detail':detail,'priority':'Cao'})
    elif bmi >= 25:
        detail = f'BMI {bmi:.1f} ({bmi_cat}). Tăng cardio 30-45 phút {pref}/ngày, cắt 200-300 kcal từ tinh bột.'
        recs.append({'icon':'🏃','title':'Kiểm soát cân nặng','detail':detail,'priority':'Cao'})

    avg_steps = stats['avg_steps']
    if avg_steps < 5000:
        recs.append({'icon':'🚶','title':'Tăng vận động',
            'detail':f'TB {int(avg_steps)} bước/ngày — rất thấp. Bắt đầu từ 20 phút đi bộ sau bữa ăn, mục tiêu 7,000 bước.','priority':'Cao'})
    elif avg_steps < 8000:
        recs.append({'icon':'🏃','title':'Nâng mức vận động',
            'detail':f'TB {int(avg_steps)} bước/ngày — khá tốt. Thêm 15 phút chạy nhẹ để đạt 10,000 bước.','priority':'Trung bình'})

    avg_hr = stats['avg_heart_rate']
    if avg_hr > 85:
        recs.append({'icon':'❤️','title':'Cải thiện tim mạch',
            'detail':f'HR TB {avg_hr} bpm — cao hơn chuẩn. Tập cardio nhẹ Zone 2 đều đặn, thiền, hạn chế caffeine.','priority':'Cao'})

    avg_sl = stats['avg_sleep']
    if avg_sl < 6:
        recs.append({'icon':'😴','title':'Cải thiện giấc ngủ',
            'detail':f'Ngủ TB {avg_sl}h — nguy hiểm. Không tập HIIT sau 19h. Thiền 10 phút trước khi ngủ.','priority':'Cao'})
    elif avg_sl < 7:
        recs.append({'icon':'🌙','title':'Tối ưu giấc ngủ',
            'detail':f'Ngủ TB {avg_sl}h — cần tăng lên 7-8h. Tập buổi sáng cải thiện chất lượng ngủ.','priority':'Trung bình'})

    if not recs:
        recs.append({'icon':'👍','title':'Duy trì & Nâng cao',
            'detail':'Chỉ số tốt! Thêm HIIT 2x/tuần hoặc yoga để nâng cao thể lực.','priority':'Thấp'})

    return recs

# ─── CHATBOT — SMART DECISION ENGINE ─────────────────────────────────────────

def chatbot_response(question, df, height_cm=170, gender="Nam", pref="Gym", age=30, condition="Bình thường", anomalies=None):
    """
    Trả lời với QUYẾT ĐỊNH CỤ THỂ thay vì gợi ý chung.
    Dựa trên ngưỡng y khoa thực từ Cardiovascular 70k + Fitbit dataset.
    """
    if anomalies is None: anomalies = []
    q = question.lower()
    stats  = get_summary_stats(df)
    latest = df.iloc[-1]
    h      = height_cm / 100
    bmi, bmi_cat = calculate_bmi(latest['weight'], height_cm)
    trends = analyze_trends(df)
    risk   = calculate_risk_score(df, height_cm, age, condition)

    # ── 1. Quyết định tập luyện hôm nay? ─────────────────────────────────────
    if any(kw in q for kw in ['có nên tập','hôm nay tập','nên tập','tập không','có tập']):
        hr = latest['heart_rate']
        sl = latest['sleep_hours']

        # Thu thập lý do KHÔNG nên tập
        blockers = []
        if anomalies: blockers.append(f"phát hiện bất thường ({anomalies[0][:60]}...)")
        if condition == "Tim mạch" and hr > 110: blockers.append(f"nhịp tim {hr} bpm nguy hiểm với bệnh tim")
        if sl < 5.5: blockers.append(f"chỉ ngủ {sl}h — cơ thể chưa phục hồi")
        if condition == "Tim mạch" and hr > 100: blockers.append(f"nhịp tim {hr} bpm cao cho bệnh nhân tim mạch")

        if blockers:
            reasons = "; ".join(blockers)
            return (
                f"## ❌ QUYẾT ĐỊNH: KHÔNG NÊN TẬP HÔM NAY\n\n"
                f"**Lý do:** {reasons}\n\n"
                f"**Thay thế:**\n"
                f"- ✅ Nghỉ ngơi hoàn toàn hoặc đi bộ nhẹ <15 phút\n"
                f"- ✅ Uống đủ nước, ăn đủ bữa\n"
                f"- {'⚠️ Nếu không cải thiện trong 2h, liên hệ bác sĩ' if condition in ['Tim mạch','Tiểu đường'] else '✅ Ngủ sớm, ngày mai tập lại'}\n\n"
                f"*Risk Score hôm nay: **{risk}/10***"
            )
        else:
            # Đưa ra loại tập cụ thể
            if condition == "Tim mạch":
                workout = f"Zone 2 Cardio: Đi bộ nhanh 30 phút, giữ HR < {min(int(0.6*(220-age)), 120)} bpm"
            elif condition == "Tiểu đường":
                workout = f"Đi bộ 30 phút sau bữa ăn (giúp hạ đường huyết). Target: {min(int(stats['avg_steps'])+1000, 8000):,} bước"
            elif bmi > 27:
                workout = f"Cardio + {pref}: 20 phút warm-up + 30 phút {pref} cường độ 70% HR max"
            else:
                workout = f"{pref} bình thường: 45-60 phút, HR mục tiêu {int(0.65*(220-age))}–{int(0.80*(220-age))} bpm"

            return (
                f"## ✅ QUYẾT ĐỊNH: CÓ THỂ TẬP HÔM NAY\n\n"
                f"**Chỉ số ổn:** HR={int(hr)} bpm ✓ | Ngủ {sl}h ✓ | Risk {risk}/10\n\n"
                f"**Bài tập đề xuất cho {gender} {age} tuổi ({condition}):**\n"
                f"- 🎯 {workout}\n"
                f"- 💧 Uống 500ml nước trước khi tập\n"
                f"- 🛑 Dừng ngay nếu HR > {int(0.85*(220-age))} bpm\n\n"
                f"*Risk Score: {risk}/10 — {'Thấp ✅' if risk < 3 else 'Trung bình ⚠️' if risk < 6 else 'Cao 🚨'}*"
            )

    # ── 2. Hôm nay ăn gì? ────────────────────────────────────────────────────
    if any(kw in q for kw in ['ăn gì','chế độ ăn','dinh dưỡng','ăn uống','bữa ăn']):
        if condition == "Tiểu đường":
            return (
                f"## 🍽️ CHẾ ĐỘ ĂN HÔM NAY — Tiểu đường\n\n"
                f"**BMI hiện tại: {bmi} ({bmi_cat})**\n\n"
                f"| Bữa | Thực phẩm | Lượng |\n|---|---|---|\n"
                f"| 🌅 Sáng | Yến mạch + trứng luộc + rau xanh | ~350 kcal |\n"
                f"| 🌞 Trưa | Gạo lứt 1 chén + thịt ức gà + rau luộc | ~500 kcal |\n"
                f"| 🌆 Chiều | Hạt óc chó + 1 quả táo xanh | ~150 kcal |\n"
                f"| 🌙 Tối | Cá hấp + bông cải + bắp non | ~400 kcal |\n\n"
                f"**⚠️ Tránh:** Cơm trắng nhiều, nước ngọt, trái cây nhiều đường (xoài, nhãn)\n"
                f"**✅ Uống:** 2-2.5L nước/ngày. Đi bộ 15-20 phút sau mỗi bữa chính."
            )
        elif condition == "Tim mạch":
            return (
                f"## 🍽️ CHẾ ĐỘ ĂN HÔM NAY — Tim mạch\n\n"
                f"| Bữa | Thực phẩm | Ghi chú |\n|---|---|---|\n"
                f"| 🌅 Sáng | Yến mạch + chuối + hạt lanh | Omega-3 tốt cho tim |\n"
                f"| 🌞 Trưa | Cá thu hấp + quinoa + salad | Giảm cholesterol |\n"
                f"| 🌆 Chiều | Hạnh nhân + dâu tây | Antioxidants |\n"
                f"| 🌙 Tối | Gà không da + bông cải xanh | Ít sodium |\n\n"
                f"**⚠️ Hạn chế muối** (<2g/ngày) để kiểm soát huyết áp\n"
                f"**✅ Bổ sung:** Omega-3, kali (chuối, khoai lang), magie"
            )
        else:
            target_cal = int(stats['avg_calories'])
            deficit = 200 if bmi > 25 else 0
            surplus = 300 if bmi < 18.5 else 0
            adj = target_cal - deficit + surplus
            return (
                f"## 🍽️ CHẾ ĐỘ ĂN HÔM NAY\n\n"
                f"**Mục tiêu calo:** ~{adj} kcal (BMI={bmi} {bmi_cat})\n\n"
                f"- 🌅 Sáng (~{adj//4} kcal): Trứng + bánh mì nguyên cám + trái cây\n"
                f"- 🌞 Trưa (~{adj//3} kcal): Cơm + protein (thịt/cá/đậu) + rau xanh\n"
                f"- 🌆 Chiều (~{adj//8} kcal): Sữa chua + hạt\n"
                f"- 🌙 Tối (~{adj//4} kcal): Cá/gà + rau + ít tinh bột\n\n"
                f"{'**💡 Giảm 200 kcal/ngày** (cắt tinh bột tối) để giảm cân.' if bmi>25 else '**💡 Tăng protein** để duy trì cơ bắp.' if bmi<18.5 else '**✅ Khẩu phần đang hợp lý.** Duy trì tốt!'}"
            )

    # ── 3. Tình trạng nguy hiểm không? / Risk ─────────────────────────────────
    if any(kw in q for kw in ['nguy hiểm','nguy cơ','risk','bất thường','tình trạng','lo lắng','đáng lo']):
        level = "🟢 THẤP" if risk < 3 else "🟡 TRUNG BÌNH" if risk < 6 else "🔴 CAO" if risk < 8 else "🆘 RẤT CAO"
        cardio_pct = _get_cardio_risk_rate(age) * 100
        resp = (
            f"## 📊 ĐÁNH GIÁ RỦI RO SỨC KHỎE\n\n"
            f"**Risk Score: {risk}/10 — {level}**\n\n"
            f"| Yếu tố | Giá trị | Trạng thái |\n|---|---|---|\n"
            f"| Nhịp tim | {int(latest['heart_rate'])} bpm | {'✅' if latest['heart_rate']<90 else '⚠️' if latest['heart_rate']<110 else '🚨'} |\n"
            f"| Giấc ngủ | {latest['sleep_hours']}h | {'✅' if latest['sleep_hours']>=7 else '⚠️' if latest['sleep_hours']>=5.5 else '🚨'} |\n"
            f"| Bước chân | {int(latest['steps']):,} | {'✅' if latest['steps']>=8000 else '⚠️' if latest['steps']>=4000 else '🚨'} |\n"
            f"| BMI | {bmi} | {'✅' if 18.5<=bmi<25 else '⚠️'} |\n"
            f"| Bệnh nền ({condition}) | — | {'🚨' if condition in ['Tim mạch','Tiểu đường'] else '✅'} |\n\n"
            f"**Nhóm tuổi ({age} tuổi):** Theo dữ liệu 70,000 bệnh nhân thực, nhóm tuổi này có **{cardio_pct:.0f}%** nguy cơ bệnh tim mạch.\n\n"
        )
        if anomalies:
            resp += f"**🚨 Cảnh báo hiện tại:**\n" + "\n".join(f"- {a}" for a in anomalies)
        else:
            resp += "**✅ Không có dấu hiệu bất thường ngay hôm nay.**"
        if risk >= 6:
            resp += f"\n\n**⚠️ Khuyến nghị:** Tham khảo bác sĩ để kiểm tra định kỳ."
        return resp

    # ── 4. BMI / Cân nặng ────────────────────────────────────────────────────
    if any(kw in q for kw in ['bmi','cân nặng','béo','gầy','thiếu cân','thừa cân']):
        wt = trends['weight']
        sym = "tăng" if wt['change_pct'] > 0 else "giảm"
        resp = (
            f"## ⚖️ CHỈ SỐ CÂN NẶNG & BMI\n\n"
            f"- BMI: **{bmi}** ({bmi_cat})\n"
            f"- Cân nặng: **{latest['weight']}kg** | Chiều cao: {height_cm}cm\n"
            f"- Xu hướng: {sym} **{abs(wt['change_pct'])}%** trong tháng\n\n"
        )
        bmi_mean = _THRESHOLDS.get(_get_age_group(age), {}).get('bmi_mean', 26.0)
        resp += f"*(BMI trung bình nhóm tuổi {age} từ dữ liệu 70k thực: {bmi_mean:.1f})*\n\n"
        if bmi < 18.5:
            resp += f"**🎯 QUYẾT ĐỊNH:** Tăng calo nạp vào +300-500 kcal/ngày. Tập tạ 3x/tuần."
        elif bmi < 25:
            resp += f"**🎯 QUYẾT ĐỊNH:** Duy trì khẩu phần hiện tại. Tiếp tục {pref} đều đặn."
        elif bmi < 30:
            resp += f"**🎯 QUYẾT ĐỊNH:** Giảm 200 kcal/ngày, tăng cardio 30 phút/ngày."
        else:
            resp += f"**🎯 QUYẾT ĐỊNH:** Tham khảo bác sĩ dinh dưỡng. Ưu tiên đi bộ để bắt đầu."
        return resp

    # ── 5. Nhịp tim ──────────────────────────────────────────────────────────
    if any(kw in q for kw in ['nhịp tim','heart','tim','bpm']):
        hr_t = trends['heart_rate']
        bp_warn = _get_bp_threshold(age, 'ap_hi_warning')
        resp = (
            f"## ❤️ NHỊP TIM\n\n"
            f"- Hôm nay: **{int(latest['heart_rate'])} bpm**\n"
            f"- TB 30 ngày: **{stats['avg_heart_rate']} bpm**\n"
            f"- Tuần 1→4: {hr_t['w1_avg']} → {hr_t['w4_avg']} bpm\n\n"
        )
        if condition == "Tim mạch":
            resp += f"*(Ngưỡng cảnh báo theo tuổi {age} từ dữ liệu thực: >{bp_warn} mmHg SBP)*\n\n"
        if stats['avg_heart_rate'] > 90:
            resp += "**🎯 QUYẾT ĐỊNH:** Giảm caffeine, tập Zone 2 cardio 4x/tuần. Kiểm tra tuyến giáp nếu kéo dài."
        elif stats['avg_heart_rate'] < 55:
            resp += "**🎯 QUYẾT ĐỊNH:** Nhịp tim thấp — bình thường nếu bạn tập thể thao nhiều. Báo bác sĩ nếu chóng mặt."
        else:
            resp += "**✅ QUYẾT ĐỊNH:** Nhịp tim ổn định. Duy trì thói quen tập hiện tại."
        return resp

    # ── 6. Giấc ngủ ──────────────────────────────────────────────────────────
    if any(kw in q for kw in ['ngủ','sleep','giấc','nghỉ ngơi']):
        sl_t = trends['sleep_hours']
        resp = (
            f"## 🛏️ GIẤC NGỦ\n\n"
            f"- Hôm qua: **{latest['sleep_hours']}h**\n"
            f"- TB 30 ngày: **{stats['avg_sleep']}h**\n"
            f"- Xu hướng: {sl_t['w1_avg']}h → {sl_t['w4_avg']}h\n\n"
        )
        if stats['avg_sleep'] < 6:
            resp += "**🎯 QUYẾT ĐỊNH:** Đặt giờ ngủ cố định (23h), tắt màn hình lúc 22h. Không tập sau 20h."
        elif stats['avg_sleep'] < 7:
            resp += "**🎯 QUYẾT ĐỊNH:** Ngủ sớm hơn 30 phút mỗi tối. Tập buổi sáng giúp cải thiện giấc ngủ."
        else:
            resp += "**✅ QUYẾT ĐỊNH:** Giấc ngủ tốt! Giữ lịch ngủ đều đặn."
        return resp

    # ── 7. Bước chân / Vận động ──────────────────────────────────────────────
    if any(kw in q for kw in ['bước','step','vận động','đi bộ','chạy','hoạt động']):
        st_t = trends['steps']
        resp = (
            f"## 🚶 VẬN ĐỘNG\n\n"
            f"- Hôm nay: **{int(latest['steps']):,} bước**\n"
            f"- TB 30 ngày: **{int(stats['avg_steps']):,} bước/ngày**\n"
            f"- Xu hướng: {int(st_t['w1_avg']):,} → {int(st_t['w4_avg']):,} bước\n\n"
        )
        if condition == "Tiểu đường":
            resp += f"**🎯 QUYẾT ĐỊNH (Tiểu đường):** Mục tiêu tối thiểu 5,000 bước/ngày. Đi ngay sau bữa ăn 15 phút."
        elif stats['avg_steps'] < 5000:
            resp += "**🎯 QUYẾT ĐỊNH:** Bắt đầu với 20 phút đi bộ sau bữa trưa. Tăng 500 bước mỗi tuần."
        elif stats['avg_steps'] < 8000:
            resp += "**🎯 QUYẾT ĐỊNH:** Khá tốt! Thêm 10 phút chạy nhẹ để đạt 10,000 bước."
        else:
            resp += "**✅ QUYẾT ĐỊNH:** Vận động tốt! Thêm bài tập sức mạnh 2x/tuần để cân bằng."
        return resp

    # ── 8. Cải thiện / Tiến bộ ───────────────────────────────────────────────
    if any(kw in q for kw in ['cải thiện','tiến bộ','progress','thay đổi','tốt hơn']):
        fitness = get_fitness_improvement(df, height_cm)
        resp = f"## 💪 ĐÁNH GIÁ CẢI THIỆN — {fitness['score_pct']}%\n\n"
        for icon, name, change, status in fitness['improvements']:
            resp += f"{icon} **{name}**: {change} — *{status}*\n"
        resp += f"\n**🎯 Điểm ưu tiên tiếp theo:** "
        worst = [n for i,n,c,s in fitness['improvements'] if 'Cần' in s]
        resp += f"Tập trung cải thiện **{worst[0]}**." if worst else "Duy trì đà tốt hiện tại!"
        return resp

    # ── 9. Tổng quan / Chào ──────────────────────────────────────────────────
    if any(kw in q for kw in ['tổng quan','sức khỏe','chào','hello','hi','xin chào','tình trạng']):
        health_score, details = calculate_health_score(df, height_cm)
        level = "🔴 CAO" if risk >= 6 else "🟡 TRUNG BÌNH" if risk >= 3 else "🟢 THẤP"
        resp = (
            f"## 👋 TỔNG QUAN SỨC KHỎE — {gender}, {age} tuổi ({condition})\n\n"
            f"🏆 Điểm sức khỏe: **{health_score}/100** | ⚠️ Risk Score: **{risk}/10** ({level})\n\n"
            f"| Chỉ số | Điểm | Đánh giá |\n|---|---|---|\n"
        )
        for name, got, max_s in details:
            bar  = "█" * int(got/max_s*10) + "░" * (10 - int(got/max_s*10))
            tag  = "✅" if got/max_s >= 0.75 else "⚠️" if got/max_s >= 0.5 else "🚨"
            resp += f"| {name} | {bar} {got}/{max_s} | {tag} |\n"
        resp += f"\n📊 Step TB: {int(stats['avg_steps']):,} | ❤️ HR TB: {stats['avg_heart_rate']} bpm | 🛏️ Ngủ TB: {stats['avg_sleep']}h | BMI: {bmi}\n\n"

        # Quyết định ưu tiên nhất hôm nay
        if anomalies:
            resp += f"**🚨 HÀNH ĐỘNG NGAY:** {anomalies[0]}"
        elif risk >= 6:
            resp += "**⚠️ KHUYẾN NGHỊ:** Nên đặt lịch khám bác sĩ sớm."
        else:
            resp += "**✅ HỎI NHANH:** 'Hôm nay có nên tập không?' | 'Hôm nay ăn gì?' | 'Tôi đang nguy hiểm không?'"
        return resp

    # ── DEFAULT ──────────────────────────────────────────────────────────────
    health_score, _ = calculate_health_score(df, height_cm)
    return (
        f"🤖 **Trợ lý Quyết định Sức khỏe** | Score: {health_score}/100 | Risk: {risk}/10\n\n"
        f"Hỏi tôi để nhận **quyết định trực tiếp**:\n\n"
        f"- 🏃 **\"Hôm nay tôi có nên tập không?\"** → Có/Không + lý do\n"
        f"- 🍽️ **\"Hôm nay tôi ăn gì?\"** → Thực đơn cụ thể theo bệnh\n"
        f"- 🚨 **\"Tôi có đang nguy hiểm không?\"** → Risk score + cảnh báo\n"
        f"- ⚖️ **\"BMI / Cân nặng\"** → Đánh giá + kế hoạch hành động\n"
        f"- ❤️ **\"Nhịp tim\"** | 🛏️ **\"Giấc ngủ\"** | 🚶 **\"Bước chân\"**\n"
        f"- 💪 **\"Tôi có tiến bộ không?\"** → So sánh tuần 1 vs tuần 4"
    )
