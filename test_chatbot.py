import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import analysis, pandas as pd

df = pd.read_csv('data_user1.csv')
df['date'] = pd.to_datetime(df['date'])

anomalies = analysis.detect_anomalies(df, 45, 'Tim m\u1ea1ch')
risk = analysis.calculate_risk_score(df, 160, 45, 'Tim m\u1ea1ch')
print("ANOMALIES:", anomalies)
print("RISK SCORE:", risk)

r = analysis.chatbot_response('hom nay co nen tap khong', df, 160, 'N\u1eef', 'Yoga', 45, 'Tim m\u1ea1ch', anomalies)
print("\n=QUYET DINH TAP LUYEN=")
print(r)

r2 = analysis.chatbot_response('toi co dang nguy hiem khong', df, 160, 'N\u1eef', 'Yoga', 45, 'Tim m\u1ea1ch', anomalies)
print("\n=DANH GIA NGUY CO=")
print(r2)

df2 = pd.read_csv('data_user2.csv')
df2['date'] = pd.to_datetime(df2['date'])
an2 = analysis.detect_anomalies(df2, 55, 'Ti\u1ec3u \u0111\u01b0\u1eddng')
print("\n=USER2 Tieu Duong=")
print("RISK:", analysis.calculate_risk_score(df2, 175, 55, 'Ti\u1ec3u \u0111\u01b0\u1eddng'))
r4 = analysis.chatbot_response('hom nay an gi', df2, 175, 'Nam', 'Ch\u1ea1y b\u1ed9', 55, 'Ti\u1ec3u \u0111\u01b0\u1eddng', an2)
print(r4)
