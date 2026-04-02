import pandas as pd
import numpy as np

def load_data(file_path='health_data.csv'):
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

def calculate_bmi(weight_kg, height_cm=170):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        category = "Thiếu cân"
    elif 18.5 <= bmi < 25:
        category = "Bình thường"
    elif 25 <= bmi < 30:
        category = "Thừa cân"
    else:
        category = "Béo phì"
    return round(bmi, 1), category

def calculate_bmi_series(df, height_cm=170):
    """Tính BMI cho toàn bộ chuỗi thời gian."""
    height_m = height_cm / 100
    df = df.copy()
    df['bmi'] = round(df['weight'] / (height_m ** 2), 1)
    return df

def get_summary_stats(df):
    stats = {
        'avg_steps': round(df['steps'].mean(), 0),
        'avg_heart_rate': round(df['heart_rate'].mean(), 1),
        'total_calories': round(df['calories'].sum(), 0),
        'avg_sleep': round(df['sleep_hours'].mean(), 1),
        'avg_weight': round(df['weight'].mean(), 1),
        'avg_calories': round(df['calories'].mean(), 0),
    }
    return stats

def analyze_activity_density(df):
    """Phân loại mức độ hoạt động mỗi ngày."""
    df = df.copy()
    conditions = [
        df['steps'] < 5000,
        (df['steps'] >= 5000) & (df['steps'] < 10000),
        df['steps'] >= 10000
    ]
    labels = ['Thấp', 'Trung bình', 'Cao']
    df['activity_level'] = np.select(conditions, labels, default='Trung bình')
    
    density = df['activity_level'].value_counts().to_dict()
    for label in labels:
        if label not in density:
            density[label] = 0
    return df, density

def analyze_trends(df):
    """So sánh tuần 1 vs tuần 4."""
    df = df.sort_values('date')
    week1 = df.iloc[:7]
    week4 = df.iloc[-7:]
    
    metrics = ['steps', 'heart_rate', 'weight', 'calories', 'sleep_hours']
    labels = {
        'steps': 'Bước chân',
        'heart_rate': 'Nhịp tim',
        'weight': 'Cân nặng',
        'calories': 'Calories',
        'sleep_hours': 'Giấc ngủ'
    }
    trends = {}
    
    for metric in metrics:
        v1 = week1[metric].mean()
        v4 = week4[metric].mean()
        percent_change = ((v4 - v1) / v1) * 100 if v1 != 0 else 0
        trends[metric] = {
            'label': labels[metric],
            'w1_avg': round(v1, 1),
            'w4_avg': round(v4, 1),
            'change_pct': round(percent_change, 1)
        }
    return trends

def get_fitness_improvement(df, height_cm=170):
    """Đánh giá mức cải thiện thể lực sau 1 tháng."""
    df = df.sort_values('date')
    week1 = df.iloc[:7]
    week4 = df.iloc[-7:]
    
    improvements = []
    score = 0
    total = 0
    
    # Bước chân
    steps_change = week4['steps'].mean() - week1['steps'].mean()
    total += 1
    if steps_change > 500:
        improvements.append(("✅", "Bước chân", f"Tăng {int(steps_change)} bước/ngày", "Tốt"))
        score += 1
    elif steps_change < -500:
        improvements.append(("⚠️", "Bước chân", f"Giảm {int(abs(steps_change))} bước/ngày", "Cần cải thiện"))
    else:
        improvements.append(("➡️", "Bước chân", "Không thay đổi đáng kể", "Ổn định"))
        score += 0.5
    
    # Nhịp tim
    hr_change = week4['heart_rate'].mean() - week1['heart_rate'].mean()
    total += 1
    if hr_change < -3:
        improvements.append(("✅", "Nhịp tim nghỉ", f"Giảm {abs(hr_change):.1f} bpm", "Tốt - tim khỏe hơn"))
        score += 1
    elif hr_change > 5:
        improvements.append(("⚠️", "Nhịp tim nghỉ", f"Tăng {hr_change:.1f} bpm", "Cần theo dõi"))
    else:
        improvements.append(("➡️", "Nhịp tim nghỉ", "Ổn định", "Bình thường"))
        score += 0.5
    
    # Giấc ngủ
    sleep_change = week4['sleep_hours'].mean() - week1['sleep_hours'].mean()
    total += 1
    if sleep_change > 0.5:
        improvements.append(("✅", "Giấc ngủ", f"Tăng {sleep_change:.1f} giờ/đêm", "Tốt"))
        score += 1
    elif sleep_change < -0.5:
        improvements.append(("⚠️", "Giấc ngủ", f"Giảm {abs(sleep_change):.1f} giờ/đêm", "Cần cải thiện"))
    else:
        improvements.append(("➡️", "Giấc ngủ", "Không thay đổi đáng kể", "Ổn định"))
        score += 0.5
    
    # BMI
    height_m = height_cm / 100
    bmi1 = week1['weight'].mean() / (height_m ** 2)
    bmi4 = week4['weight'].mean() / (height_m ** 2)
    bmi_change = bmi4 - bmi1
    total += 1
    if 18.5 <= bmi4 < 25:
        improvements.append(("✅", "BMI", f"{bmi4:.1f} (Bình thường)", "Tốt"))
        score += 1
    elif bmi4 < 18.5:
        improvements.append(("⚠️", "BMI", f"{bmi4:.1f} (Thiếu cân)", "Cần tăng cân"))
    else:
        improvements.append(("⚠️", "BMI", f"{bmi4:.1f} (Thừa cân)", "Cần giảm cân"))
        if bmi_change < 0:
            score += 0.5
    
    overall_pct = round((score / total) * 100, 0) if total > 0 else 0
    
    return {
        'improvements': improvements,
        'score_pct': overall_pct,
        'score': score,
        'total': total,
    }

def calculate_health_score(df, height_cm=170):
    """Tính điểm sức khỏe tổng hợp (0-100)."""
    latest = df.iloc[-1]
    score = 0
    details = []
    
    # Bước chân (0-25 điểm)
    steps = latest['steps']
    if steps >= 10000:
        s = 25
    elif steps >= 7000:
        s = 20
    elif steps >= 5000:
        s = 15
    elif steps >= 3000:
        s = 10
    else:
        s = 5
    score += s
    details.append(('Vận động', s, 25))
    
    # Nhịp tim (0-25 điểm)
    hr = latest['heart_rate']
    if 60 <= hr <= 80:
        s = 25
    elif 55 <= hr <= 90:
        s = 18
    elif 50 <= hr <= 100:
        s = 12
    else:
        s = 5
    score += s
    details.append(('Nhịp tim', s, 25))
    
    # Giấc ngủ (0-25 điểm)
    sleep = latest['sleep_hours']
    if 7 <= sleep <= 9:
        s = 25
    elif 6 <= sleep <= 10:
        s = 18
    elif 5 <= sleep <= 11:
        s = 12
    else:
        s = 5
    score += s
    details.append(('Giấc ngủ', s, 25))
    
    # BMI (0-25 điểm)
    height_m = height_cm / 100
    bmi = latest['weight'] / (height_m ** 2)
    if 18.5 <= bmi < 25:
        s = 25
    elif 17 <= bmi < 30:
        s = 15
    else:
        s = 5
    score += s
    details.append(('BMI', s, 25))
    
    return score, details

def get_recommendations(df):
    """Gợi ý nhanh dựa trên chỉ số mới nhất."""
    latest = df.iloc[-1]
    recommendations = []
    insights = []
    
    if latest['steps'] < 5000:
        insights.append("Số bước chân hôm nay rất thấp.")
        recommendations.append("Hãy đi bộ nhẹ nhàng ít nhất 15 phút.")
    
    if latest['sleep_hours'] < 6:
        insights.append("Bạn đã ngủ ít hơn 6 tiếng.")
        recommendations.append("Cân nhắc đi ngủ sớm hơn vào tối nay để phục hồi sức khỏe.")
        
    if latest['heart_rate'] > 90:
        insights.append("Nhịp tim lúc nghỉ ngơi hơi cao.")
        recommendations.append("Tránh các bài tập cường độ cao và hạn chế caffeine.")

    if not insights:
        insights.append("Các chỉ số sức khỏe của bạn đang ở mức ổn định.")
        recommendations.append("Tiếp tục duy trì lối sống lành mạnh này nhé!")
        
    return {
        "insight": " ".join(insights),
        "recommendation": " ".join(recommendations)
    }

def get_exercise_recommendations(df, height_cm=170, gender="Nam", pref="Gym"):
    """Gợi ý chế độ tập luyện chi tiết dựa trên chỉ số sinh học và sở thích cá nhân."""
    latest = df.iloc[-1]
    stats = get_summary_stats(df)
    height_m = height_cm / 100
    bmi = latest['weight'] / (height_m ** 2)
    _, bmi_cat = calculate_bmi(latest['weight'], height_cm)
    
    recs = []
    
    # Dựa trên BMI, Giới tính và Sở thích
    if bmi < 18.5:
        if pref == "Gym":
            detail = 'BMI thấp (Thiếu cân) – Tập tạ nặng 3-4 lần/tuần, ưu tiên bài compound (squats, deadlift). Tập trung phần trên cơ thể.' if gender == "Nam" else 'BMI thấp – Tập tạ nhẹ vừa phải hoặc Pilates để săn chắc. Tăng lượng protein.'
        elif pref == "Yoga":
            detail = 'Tập Yoga kết hợp (Power Yoga) để tăng cường sức mạnh cơ bắp toàn diện, không ráng kéo dãn quá sức.'
        else:
            detail = f'Bạn đang thiếu cân. Với sở thích {pref}, cố gắng không hoạt động cường độ quá cao gây thâm hụt calo lớn.'
        recs.append({
            'icon': '🏋️‍♀️' if gender == "Nữ" else '🏋️‍♂️', 'title': 'Tăng cơ & Săn chắc',
            'detail': f"{detail} Cần tăng lượng calo nạp vào thêm 300-500 kcal/ngày.",
            'priority': 'Cao'
        })
    elif bmi >= 25:
        if pref == "Yoga":
            detail = 'Với Yoga, hãy thử Vinyasa hoặc Hot Yoga để đốt calo nhanh hơn.' if gender == "Nữ" else 'Tập Hatha Yoga kết hợp cardio để tối ưu hóa việc phân giải mỡ.'
        elif pref == "Gym":
            detail = 'Tăng cường Cardio (HIIT) cuối buổi tập tạ. Hạn chế nghỉ quá lâu giữa các hiệp.'
        else:
            detail = f'BMI đang ở mức ({bmi_cat}). Hãy dành ít nhất 30-45 phút {pref} mỗi ngày ở cường độ trung bình cao.'
        recs.append({
            'icon': '🏃‍♀️' if gender == "Nữ" else '🏃‍♂️', 'title': 'Giảm mỡ tích cực',
            'detail': f"{detail} Giảm 200-300 kcal/ngày từ chế độ ăn (Cắt giảm tinh bột xấu).",
            'priority': 'Cao'
        })
    
    # Dựa trên bước chân
    avg_steps = stats['avg_steps']
    if avg_steps < 5000:
        recs.append({
            'icon': '🚶', 'title': 'Tăng vận động',
            'detail': f'Trung bình chỉ {int(avg_steps)} bước/ngày. Mục tiêu: 7,000-10,000 bước. Bắt đầu bằng đi bộ 20 phút sau bữa ăn.',
            'priority': 'Cao'
        })
    elif avg_steps < 8000:
        recs.append({
            'icon': '🏃‍♂️', 'title': 'Nâng mức vận động',
            'detail': f'Trung bình {int(avg_steps)} bước/ngày – khá tốt. Thử chạy bộ nhẹ 15-20 phút hoặc đạp xe để đạt 10,000 bước.',
            'priority': 'Trung bình'
        })
    
    # Dựa trên nhịp tim
    avg_hr = stats['avg_heart_rate']
    if avg_hr > 85:
        recs.append({
            'icon': '❤️', 'title': 'Cải thiện tim mạch',
            'detail': f'Nhịp tim nghỉ TB {avg_hr} bpm (hơi cao). Tập cardio nhẹ đều đặn: đi bộ nhanh, yoga, bơi lội. Hạn chế caffeine.',
            'priority': 'Cao'
        })
    elif avg_hr < 60:
        recs.append({
            'icon': '💚', 'title': 'Tim mạch tốt',
            'detail': f'Nhịp tim nghỉ TB {avg_hr} bpm – rất tốt! Duy trì thói quen tập luyện hiện tại.',
            'priority': 'Thấp'
        })
    
    # Dựa trên giấc ngủ
    avg_sleep = stats['avg_sleep']
    if avg_sleep < 6:
        recs.append({
            'icon': '😴', 'title': 'Cải thiện giấc ngủ',
            'detail': f'Giấc ngủ TB chỉ {avg_sleep} giờ. Không tập HIIT sau 19:00. Thử yoga hoặc thiền 10 phút trước khi ngủ. Tránh màn hình 1 giờ trước khi ngủ.',
            'priority': 'Cao'
        })
    elif avg_sleep < 7:
        recs.append({
            'icon': '🌙', 'title': 'Tối ưu giấc ngủ',
            'detail': f'Giấc ngủ TB {avg_sleep} giờ – cần tăng lên 7-8 giờ. Tập thể dục buổi sáng giúp cải thiện chất lượng giấc ngủ.',
            'priority': 'Trung bình'
        })
    
    # Dựa trên xu hướng cân nặng
    df_sorted = df.sort_values('date')
    weight_change = df_sorted.iloc[-1]['weight'] - df_sorted.iloc[0]['weight']
    if weight_change > 2:
        recs.append({
            'icon': '⚖️', 'title': 'Kiểm soát cân nặng',
            'detail': f'Cân nặng đã tăng {weight_change:.1f}kg trong tháng. Tăng cường cardio và giảm tinh bột vào buổi tối.',
            'priority': 'Trung bình'
        })
    elif weight_change < -2:
        recs.append({
            'icon': '⚖️', 'title': 'Theo dõi cân nặng',
            'detail': f'Cân nặng đã giảm {abs(weight_change):.1f}kg trong tháng. Đảm bảo ăn đủ chất, bổ sung protein sau tập.',
            'priority': 'Trung bình'
        })
    
    if not recs:
        recs.append({
            'icon': '👍', 'title': 'Duy trì & nâng cao',
            'detail': 'Các chỉ số tốt! Thử thêm bài tập HIIT 2 lần/tuần hoặc yoga để linh hoạt hơn.',
            'priority': 'Thấp'
        })
    
    return recs

def chatbot_response(question, df, height_cm=170, gender="Nam", pref="Gym"):
    """Trả lời câu hỏi sức khỏe dựa trên dữ liệu thật, giới tính và sở thích."""
    question_lower = question.lower()
    stats = get_summary_stats(df)
    latest = df.iloc[-1]
    height_m = height_cm / 100
    bmi, bmi_cat = calculate_bmi(latest['weight'], height_cm)
    trends = analyze_trends(df)
    
    # BMI / Cân nặng
    if any(kw in question_lower for kw in ['bmi', 'cân nặng', 'weight', 'béo', 'gầy', 'thiếu cân', 'thừa cân']):
        weight_trend = trends['weight']
        symbol = "tăng" if weight_trend['change_pct'] > 0 else "giảm"
        response = (
            f"📊 **Chỉ số BMI hiện tại:** {bmi} ({bmi_cat})\n\n"
            f"- Cân nặng hiện tại: **{latest['weight']} kg**\n"
            f"- Chiều cao: **{height_cm} cm**\n"
            f"- Xu hướng cân nặng: {symbol} **{abs(weight_trend['change_pct'])}%** so với tuần đầu\n\n"
        )
        if bmi < 18.5:
            response += f"💡 **Lời khuyên cho {gender} đam mê {pref}:** Bạn đang **thiếu cân**. Hãy giảm cường độ cardio, tăng lượng calo nạp vào (~300-500 kcal/ngày), ăn nhiều protein. Nên tập các bài phát triển khối cơ."
        elif 18.5 <= bmi < 25:
            response += f"💡 **Lời khuyên cho {gender} đam mê {pref}:** BMI ở mức **bình thường**! Duy trì chế độ ăn cân bằng và tiếp tục duy trì lịch tập {pref} đều đặn để giữ dáng."
        elif 25 <= bmi < 30:
            response += f"💡 **Lời khuyên cho {gender} đam mê {pref}:** Bạn đang **thừa cân**. Cố gắng đẩy cao nhịp tim hơn một chút ở các buổi tập {pref}, cắt giảm tinh bột nhanh buổi tối, và theo dõi lượng calo mỗi ngày."
        else:
            response += f"💡 **Lời khuyên cho {gender} đam mê {pref}:** BMI ở mức **béo phì**. Nên tham khảo bác sĩ dinh dưỡng, ưu tiên vận động nhẹ như đi bộ trước khi bắt đầu bài tập nặng của {pref}."
        return response
    
    # Nhịp tim
    if any(kw in question_lower for kw in ['nhịp tim', 'heart', 'tim', 'bpm']):
        hr_trend = trends['heart_rate']
        response = (
            f"❤️ **Nhịp tim nghỉ ngơi:**\n\n"
            f"- Hôm nay: **{int(latest['heart_rate'])} bpm**\n"
            f"- Trung bình 30 ngày: **{stats['avg_heart_rate']} bpm**\n"
            f"- Tuần 1 → Tuần 4: {hr_trend['w1_avg']} → {hr_trend['w4_avg']} bpm\n\n"
        )
        if stats['avg_heart_rate'] > 85:
            response += "💡 **Lời khuyên:** Nhịp tim khá cao. Hãy thử thiền, yoga, hít thở sâu. Hạn chế caffeine và tập cardio nhẹ đều đặn."
        elif stats['avg_heart_rate'] < 60:
            response += "💡 **Lời khuyên:** Nhịp tim thấp – dấu hiệu tim mạch tốt! Duy trì thói quen tập luyện hiện tại."
        else:
            response += "💡 **Lời khuyên:** Nhịp tim ở mức bình thường. Tập aerobic đều đặn sẽ giúp nhịp tim nghỉ giảm dần."
        return response
    
    # Giấc ngủ
    if any(kw in question_lower for kw in ['ngủ', 'sleep', 'giấc', 'nghỉ ngơi']):
        sleep_trend = trends['sleep_hours']
        response = (
            f"🛏️ **Giấc ngủ:**\n\n"
            f"- Hôm qua: **{latest['sleep_hours']} giờ**\n"
            f"- Trung bình 30 ngày: **{stats['avg_sleep']} giờ**\n"
            f"- Tuần 1 → Tuần 4: {sleep_trend['w1_avg']} → {sleep_trend['w4_avg']} giờ\n\n"
        )
        if stats['avg_sleep'] < 6:
            response += "💡 **Lời khuyên:** Bạn ngủ **quá ít**! Mục tiêu 7-8 giờ. Tránh màn hình trước khi ngủ, tập yoga buổi tối, giữ phòng tối và mát."
        elif stats['avg_sleep'] < 7:
            response += "💡 **Lời khuyên:** Giấc ngủ hơi thiếu. Thử đi ngủ sớm hơn 30 phút, tránh tập thể dục nặng sau 20:00."
        else:
            response += "💡 **Lời khuyên:** Giấc ngủ tốt! Duy trì thời gian ngủ đều đặn để tối ưu sức khỏe."
        return response
    
    # Bước chân / vận động
    if any(kw in question_lower for kw in ['bước', 'step', 'vận động', 'đi bộ', 'chạy']):
        steps_trend = trends['steps']
        response = (
            f"🚶 **Hoạt động vận động:**\n\n"
            f"- Hôm nay: **{int(latest['steps'])} bước**\n"
            f"- Trung bình 30 ngày: **{int(stats['avg_steps'])} bước/ngày**\n"
            f"- Tuần 1 → Tuần 4: {int(steps_trend['w1_avg'])} → {int(steps_trend['w4_avg'])} bước\n\n"
        )
        if stats['avg_steps'] < 5000:
            response += "💡 **Lời khuyên:** Mức vận động **rất thấp**. Bắt đầu từ mục tiêu 5,000 bước → tăng dần lên 10,000. Đi bộ sau mỗi bữa ăn 15 phút."
        elif stats['avg_steps'] < 8000:
            response += "💡 **Lời khuyên:** Mức vận động khá. Hãy thử đạt mục tiêu 10,000 bước bằng cách đi cầu thang, đi bộ buổi trưa."
        else:
            response += "💡 **Lời khuyên:** Hoạt động vận động tốt! Thử thêm bài tập HIIT hoặc chạy bộ interval để cải thiện."
        return response
    
    # Calories
    if any(kw in question_lower for kw in ['calo', 'calorie', 'calories', 'kcal', 'ăn', 'dinh dưỡng']):
        cal_trend = trends['calories']
        response = (
            f"🔥 **Calories:**\n\n"
            f"- Hôm nay: **{int(latest['calories'])} kcal**\n"
            f"- Trung bình 30 ngày: **{int(stats['avg_calories'])} kcal/ngày**\n"
            f"- Tổng 30 ngày: **{int(stats['total_calories'])} kcal**\n\n"
        )
        if bmi >= 25:
            response += "💡 **Lời khuyên:** Với BMI thừa cân, nên giảm ~200-300 kcal/ngày. Ưu tiên protein, rau xanh, hạn chế đường và tinh bột."
        elif bmi < 18.5:
            response += "💡 **Lời khuyên:** Với BMI thiếu cân, tăng thêm 300-500 kcal/ngày từ thực phẩm giàu protein và chất béo lành mạnh."
        else:
            response += "💡 **Lời khuyên:** Lượng calo hợp lý. Chia thành 3 bữa chính + 2 bữa phụ để duy trì năng lượng ổn định."
        return response
    
    # Tập luyện  
    if any(kw in question_lower for kw in ['tập', 'exercise', 'luyện tập', 'workout', 'gym', 'yoga', 'chạy']):
        recs = get_exercise_recommendations(df, height_cm, gender, pref)
        response = f"🏃 **Gợi ý {pref} dành riêng cho {gender}:**\n\n"
        for rec in recs:
            response += f"{rec['icon']} **{rec['title']}** (Ưu tiên: {rec['priority']})\n{rec['detail']}\n\n"
        return response
    
    # Tổng quan / chào hỏi
    if any(kw in question_lower for kw in ['tổng quan', 'sức khỏe', 'chào', 'hello', 'hi', 'xin chào', 'tình trạng']):
        health_score, details = calculate_health_score(df, height_cm)
        response = (
            f"👋 **Tổng quan sức khỏe của bạn:**\n\n"
            f"🏆 Điểm sức khỏe: **{health_score}/100**\n\n"
            f"| Chỉ số | Điểm |\n|---|---|\n"
        )
        for name, got, max_s in details:
            bar = "█" * int(got / max_s * 10) + "░" * (10 - int(got / max_s * 10))
            response += f"| {name} | {bar} {got}/{max_s} |\n"
        response += f"\n📊 Bước chân TB: {int(stats['avg_steps'])} | ❤️ Nhịp tim TB: {stats['avg_heart_rate']} bpm | 🛏️ Ngủ TB: {stats['avg_sleep']}h | ⚖️ BMI: {bmi}"
        return response
    
    # Cải thiện
    if any(kw in question_lower for kw in ['cải thiện', 'tiến bộ', 'progress', 'improvement', 'thay đổi']):
        fitness = get_fitness_improvement(df, height_cm)
        response = f"💪 **Đánh giá cải thiện thể lực sau 1 tháng:**\n\nĐiểm tổng: **{fitness['score_pct']}%**\n\n"
        for icon, name, change, status in fitness['improvements']:
            response += f"{icon} **{name}**: {change} – _{status}_\n"
        return response
    
    # Mặc định
    health_score, _ = calculate_health_score(df, height_cm)
    return (
        f"🤖 Tôi có thể giúp bạn phân tích các chỉ số sức khỏe! Hãy hỏi về:\n\n"
        f"- 📊 **\"Tổng quan sức khỏe\"** – Xem điểm sức khỏe tổng hợp\n"
        f"- ⚖️ **\"BMI / Cân nặng\"** – Phân tích BMI và lời khuyên\n"
        f"- ❤️ **\"Nhịp tim\"** – Đánh giá tim mạch\n"
        f"- 🚶 **\"Bước chân\"** – Phân tích vận động\n"
        f"- 🛏️ **\"Giấc ngủ\"** – Đánh giá chất lượng giấc ngủ\n"
        f"- 🔥 **\"Calories\"** – Phân tích dinh dưỡng\n"
        f"- 🏃 **\"Tập luyện\"** – Gợi ý chế độ tập\n"
        f"- 💪 **\"Cải thiện\"** – Đánh giá tiến bộ sau 1 tháng\n\n"
        f"🏆 Điểm sức khỏe hiện tại: **{health_score}/100**"
    )

if __name__ == "__main__":
    df = load_data()
    print("Summary Stats:", get_summary_stats(df))
    print("Trends:", analyze_trends(df))
    print("Latest Recommendation:", get_recommendations(df))
    bmi, cat = calculate_bmi(df.iloc[-1]['weight'])
    print(f"Latest BMI: {bmi} ({cat})")
    print("Health Score:", calculate_health_score(df))
    print("Fitness Improvement:", get_fitness_improvement(df))
    print("\nChatbot test:")
    print(chatbot_response("tổng quan sức khỏe", df))
