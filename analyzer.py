# analyzer.py
import anthropic, json

def fmt_pace(sec):
    if not sec or sec <= 0: return "N/A"
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}/km"

def analyze_activity(act, plan_ctx):
    result = {
        "distance_ok": None, "pace_ok": None, "hr_ok": None,
        "distance_delta_km": None, "pace_delta_sec": None,
        "score": 0, "flags": [], "badge": "⚪"
    }
    if not plan_ctx:
        return result

    dist = act.get("distance_km", 0)
    pace = act.get("avg_pace_sec", 0)
    hr   = act.get("avg_hr")
    plan_km   = plan_ctx.get("total_km", 0)
    pace_min  = plan_ctx.get("target_pace_min", 0)
    pace_max  = plan_ctx.get("target_pace_max", 0)
    hr_max    = plan_ctx.get("target_hr_max", 999)

    score = 0

    # Distance: allow ±20%
    if plan_km > 0:
        ratio = dist / plan_km
        result["distance_delta_km"] = round(dist - plan_km, 1)
        if 0.8 <= ratio <= 1.2:
            result["distance_ok"] = True
            score += 30
        elif ratio < 0.8:
            result["distance_ok"] = False
            result["flags"].append(f"Thiếu quãng đường ({dist:.1f}km vs kế hoạch {plan_km}km)")
        else:
            result["distance_ok"] = False
            result["flags"].append(f"Vượt quãng đường ({dist:.1f}km vs kế hoạch {plan_km}km)")

    # Pace
    if pace > 0 and pace_min > 0 and pace_max > 0:
        result["pace_delta_sec"] = pace - int((pace_min + pace_max) / 2)
        if pace_min <= pace <= pace_max:
            result["pace_ok"] = True
            score += 40
        elif pace < pace_min:
            result["pace_ok"] = False
            result["flags"].append(f"Chạy QUÁ NHANH ({fmt_pace(pace)} vs {fmt_pace(pace_min)}–{fmt_pace(pace_max)})")
        else:
            result["pace_ok"] = False
            result["flags"].append(f"Chạy quá chậm ({fmt_pace(pace)} vs {fmt_pace(pace_min)}–{fmt_pace(pace_max)})")

    # HR
    if hr and hr_max:
        if hr <= hr_max:
            result["hr_ok"] = True
            score += 30
        else:
            result["hr_ok"] = False
            result["flags"].append(f"HR cao hơn target ({hr} bpm vs max {hr_max} bpm)")

    result["score"] = score
    if score >= 90: result["badge"] = "🟢"
    elif score >= 60: result["badge"] = "🟡"
    elif score >= 30: result["badge"] = "🟠"
    else: result["badge"] = "🔴"

    return result


def generate_ai_feedback(athlete_name, recent_activities, plan_ctx, week_num):
    """Call Claude API to generate coaching feedback and next session recommendation."""
    client = anthropic.Anthropic()

    # Build summary of recent activities
    acts_summary = []
    for a in recent_activities:
        an = a.get("analysis", {})
        acts_summary.append({
            "date": a.get("date"),
            "week": a.get("plan_week"),
            "distance_km": a.get("distance_km"),
            "pace": fmt_pace(a.get("avg_pace_sec")),
            "avg_hr": a.get("avg_hr"),
            "score": an.get("score"),
            "badge": an.get("badge"),
            "flags": an.get("flags", []),
        })

    next_week_num = week_num + 1 if week_num else None

    prompt = f"""Bạn là HLV chạy bộ chuyên nghiệp, đang huấn luyện học viên "{athlete_name}" chuẩn bị cho Full Marathon ngày 06/12/2026 với target 4:30–5:00.

KẾ HOẠCH TUẦN HIỆN TẠI (Tuần {week_num}):
{json.dumps(plan_ctx, ensure_ascii=False, indent=2)}

CÁC BUỔI TẬP GẦN ĐÂY (8 buổi gần nhất):
{json.dumps(acts_summary, ensure_ascii=False, indent=2)}

Hãy phân tích và đưa ra:

1. **ĐÁNH GIÁ TỔNG QUAN** (3–4 câu): Học viên đang thực hiện giáo án như thế nào? Điểm mạnh và vấn đề cần chú ý?

2. **PHÂN TÍCH CHI TIẾT**:
   - Quãng đường: Có đủ volume không?
   - Pace: Có chạy đúng zone không? Có xu hướng chạy quá nhanh không?
   - HR: Có kiểm soát nhịp tim không?

3. **ĐIỀU CHỈNH BÀI HỌC KẾ TIẾP** (Tuần {next_week_num if next_week_num else 'kế tiếp'}):
   - Có nên tăng/giảm volume không? Bao nhiêu %?
   - Cần nhấn mạnh loại bài tập nào?
   - Cảnh báo/lưu ý gì cụ thể?

4. **GỢI Ý BUỔI LONG RUN KẾ TIẾP**: Pace, distance, HR target cụ thể.

Trả lời bằng tiếng Việt, ngắn gọn, thực tế, như một HLV nói chuyện với học viên."""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text
