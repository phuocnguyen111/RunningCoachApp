# plan.py – 27-week marathon training plan data
# pace in sec/km, HR targets in bpm

TRAINING_PLAN = [
    # ── PHASE 1: Xây Nền Tảng (T1–T10) ──────────────────────────────────────
    {"week": 1, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 25,
     "long_run_km": 8, "session_type": "EASY",
     "target_pace_min": 420, "target_pace_max": 480,   # 7:00–8:00/km
     "target_hr_max": 148, "note": "Làm quen nhịp điệu, chạy thoải mái"},

    {"week": 2, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 28,
     "long_run_km": 10, "session_type": "EASY",
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 148, "note": "Giữ HR zone 2"},

    {"week": 3, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 30,
     "long_run_km": 12, "session_type": "EASY",
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 148, "note": "Tăng long run dần"},

    {"week": 4, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 27,
     "long_run_km": 11, "session_type": "EASY", "deload": True,
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 145, "note": "⚠️ Tuần giảm tải"},

    {"week": 5, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 33,
     "long_run_km": 14, "session_type": "EASY",
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 148, "note": "Bắt đầu chạy 5 ngày/tuần"},

    {"week": 6, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 36,
     "long_run_km": 15, "session_type": "EASY",
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 148, "note": "Volume tăng"},

    {"week": 7, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 38,
     "long_run_km": 15, "session_type": "EASY",
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 148, "note": "Pace đều, không nhanh"},

    {"week": 8, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 34,
     "long_run_km": 14, "session_type": "EASY", "deload": True,
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 145, "note": "⚠️ Tuần giảm tải"},

    {"week": 9, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 42,
     "long_run_km": 18, "session_type": "EASY",
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 148, "note": "Long run 18km quan trọng"},

    {"week": 10, "phase": 1, "phase_name": "Xây Nền Tảng", "total_km": 38,
     "long_run_km": 16, "session_type": "EASY", "deload": True,
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 145, "note": "⚠️ Giảm tải cuối GĐ1"},

    # ── PHASE 2: Phát Triển Tốc Độ (T11–T20) ──────────────────────────────
    {"week": 11, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 43,
     "long_run_km": 18, "session_type": "TEMPO",
     "target_pace_min": 370, "target_pace_max": 395,   # 6:10–6:35/km tempo
     "target_hr_max": 165, "note": "Bắt đầu tempo run"},

    {"week": 12, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 46,
     "long_run_km": 20, "session_type": "SPEED",
     "target_pace_min": 310, "target_pace_max": 340,   # 5:10–5:40/km intervals
     "target_hr_max": 175, "note": "Interval 6×400m"},

    {"week": 13, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 49,
     "long_run_km": 21, "session_type": "TEMPO",
     "target_pace_min": 370, "target_pace_max": 395,
     "target_hr_max": 165, "note": "Tăng long run lên 21km"},

    {"week": 14, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 40,
     "long_run_km": 16, "session_type": "EASY", "deload": True,
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 148, "note": "⚠️ Tuần giảm tải"},

    {"week": 15, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 52,
     "long_run_km": 22, "session_type": "MP",
     "target_pace_min": 384, "target_pace_max": 426,   # 6:24–7:06/km marathon pace
     "target_hr_max": 162, "note": "Marathon pace run 8km"},

    {"week": 16, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 55,
     "long_run_km": 24, "session_type": "TEMPO",
     "target_pace_min": 370, "target_pace_max": 395,
     "target_hr_max": 165, "note": "Long run 24km – dùng gel"},

    {"week": 17, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 56,
     "long_run_km": 24, "session_type": "SPEED",
     "target_pace_min": 310, "target_pace_max": 340,
     "target_hr_max": 175, "note": "4×1000m intervals"},

    {"week": 18, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 45,
     "long_run_km": 18, "session_type": "EASY", "deload": True,
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 148, "note": "⚠️ Tuần giảm tải"},

    {"week": 19, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 57,
     "long_run_km": 25, "session_type": "MP",
     "target_pace_min": 384, "target_pace_max": 426,
     "target_hr_max": 162, "note": "Long run 25km + MP run"},

    {"week": 20, "phase": 2, "phase_name": "Phát Triển Tốc Độ", "total_km": 50,
     "long_run_km": 22, "session_type": "SPEED", "deload": True,
     "target_pace_min": 310, "target_pace_max": 340,
     "target_hr_max": 175, "note": "⚠️ Giảm tải cuối GĐ2"},

    # ── PHASE 3: Nâng Cao & Race Prep (T21–T27) ──────────────────────────
    {"week": 21, "phase": 3, "phase_name": "Race Prep", "total_km": 55,
     "long_run_km": 27, "session_type": "MP",
     "target_pace_min": 384, "target_pace_max": 426,
     "target_hr_max": 162, "note": "Long run 27km – test dinh dưỡng"},

    {"week": 22, "phase": 3, "phase_name": "Race Prep", "total_km": 59,
     "long_run_km": 30, "session_type": "LONG",
     "target_pace_min": 450, "target_pace_max": 510,   # 7:30–8:30/km easy long
     "target_hr_max": 155, "note": "🔑 Long run 30km lần 1"},

    {"week": 23, "phase": 3, "phase_name": "Race Prep", "total_km": 58,
     "long_run_km": 32, "session_type": "LONG",
     "target_pace_min": 480, "target_pace_max": 540,   # 8:00–9:00/km
     "target_hr_max": 158, "note": "🔥 LONG RUN 32km – bài quan trọng nhất"},

    {"week": 24, "phase": 3, "phase_name": "Race Prep", "total_km": 59,
     "long_run_km": 30, "session_type": "LONG",
     "target_pace_min": 450, "target_pace_max": 510,
     "target_hr_max": 155, "note": "🔑 Long run 30km lần 2"},

    {"week": 25, "phase": 3, "phase_name": "Race Prep", "total_km": 46,
     "long_run_km": 20, "session_type": "EASY", "taper": True,
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 148, "note": "⚠️ TAPER bắt đầu – giảm 30%"},

    {"week": 26, "phase": 3, "phase_name": "Race Prep", "total_km": 32,
     "long_run_km": 14, "session_type": "EASY", "taper": True,
     "target_pace_min": 420, "target_pace_max": 480,
     "target_hr_max": 145, "note": "⚠️ TAPER sâu – chân tươi"},

    {"week": 27, "phase": 3, "phase_name": "Race Prep", "total_km": 22,
     "long_run_km": 42.195, "session_type": "RACE", "race_week": True,
     "target_pace_min": 384, "target_pace_max": 426,
     "target_hr_max": 170, "note": "🏆 RACE DAY 06/12/2026"},
]
