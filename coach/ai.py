import json

import anthropic

from .config import ai_enabled_from_env
from .scoring import fmt_pace

__all__ = ["AIError", "ai_enabled_from_env", "build_prompt", "generate_feedback", "make_client"]

RECENT_LIMIT = 8
MAX_TOKENS = 16000
EFFORT = "medium"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
# Server-side fallback chỉ nhận ở các model này; model khác gửi request thường.
SERVER_FALLBACK_MODELS = {"claude-fable-5-2", "claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}
WEEK_KEYS = ("week", "phase_name", "total_km", "long_run_km", "session_type", "target_pace_min",
             "target_pace_max", "target_hr_max", "note", "deload", "taper", "race_week")

SYSTEM_PROMPT = """Bạn là huấn luyện viên chạy bộ giàu kinh nghiệm, đang theo dõi một học viên tập theo giáo án.
Bạn nhận dữ liệu JSON gồm: thông tin giáo án, mục tiêu tuần đang xét và tuần kế tiếp, ghi chú của nhóm,
và tối đa 8 buổi tập gần nhất kèm kết quả chấm tự động (điểm, badge, cảnh báo).

Trả lời bằng tiếng Việt, ngắn gọn, thực tế, giọng HLV nói chuyện trực tiếp với học viên, dạng Markdown với đúng 4 mục:

## 1. Đánh giá tổng quan
3–4 câu: học viên đang bám giáo án thế nào, điểm mạnh, vấn đề cần chú ý.

## 2. Phân tích chi tiết
- Volume: có đủ km so với mục tiêu tuần không.
- Pace: có chạy đúng vùng không, có xu hướng chạy quá nhanh/chậm không.
- HR: có kiểm soát nhịp tim không.

## 3. Điều chỉnh tuần kế tiếp
Có nên tăng/giảm volume không (bao nhiêu %), cần nhấn mạnh loại bài nào, cảnh báo cụ thể.

## 4. Gợi ý long run kế tiếp
Quãng đường, pace và HR mục tiêu cụ thể.

Chỉ dựa trên dữ liệu được cung cấp. Nếu dữ liệu quá ít để kết luận, nói rõ điều đó. Pace tính bằng phút:giây/km."""


class AIError(Exception):
    pass


def make_client():
    return anthropic.Anthropic()


def _week(week):
    return {k: week.get(k) for k in WEEK_KEYS} if week else None


def _activity(a):
    an = a.get("analysis") or {}
    return {
        "date": a.get("date"), "session_type": a.get("session_type"), "plan_week": a.get("plan_week"),
        "distance_km": a.get("distance_km"), "duration_min": round((a.get("duration_sec") or 0) / 60),
        "pace": fmt_pace(a.get("avg_pace_sec")), "avg_hr": a.get("avg_hr"), "max_hr": a.get("max_hr"),
        "cadence_spm": a.get("avg_cadence"), "elevation_gain_m": a.get("elevation_gain_m"),
        "score": an.get("score"), "badge": an.get("badge"), "flags": an.get("flags") or [],
        "note": an.get("note"),
    }


def build_prompt(plan, week_num, activities, group_notes):
    weeks = plan["weeks"]
    current = weeks[week_num - 1] if 1 <= week_num <= len(weeks) else None
    nxt = weeks[week_num] if week_num < len(weeks) else None
    payload = {
        "plan": {"name": plan["name"], "distance_target_km": plan["distance_target_km"],
                 "total_weeks": plan["total_weeks"], "description": plan.get("description", "")},
        "current_week": _week(current),
        "next_week": _week(nxt),
        "group_notes": group_notes or "",
        "recent_activities": [_activity(a) for a in activities[-RECENT_LIMIT:]],
    }
    intro = (f"Học viên đang tập giáo án \"{plan['name']}\" (cự ly mục tiêu {plan['distance_target_km']} km), "
             f"đang xét tuần {week_num}/{plan['total_weeks']}. Dữ liệu:\n")
    return intro + json.dumps(payload, ensure_ascii=False, indent=2)


def generate_feedback(model, prompt, client=None):
    client = client or make_client()
    kwargs = {
        "model": model, "max_tokens": MAX_TOKENS, "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
        "output_config": {"effort": EFFORT},
    }
    try:
        if model in SERVER_FALLBACK_MODELS:
            resp = client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
        else:
            resp = client.messages.create(**kwargs)
    except anthropic.AuthenticationError as e:
        raise AIError("Thông tin xác thực AI không hợp lệ — kiểm tra ANTHROPIC_API_KEY") from e
    except anthropic.PermissionDeniedError as e:
        raise AIError("Tài khoản AI không có quyền dùng model này") from e
    except anthropic.NotFoundError as e:
        raise AIError(f"Model '{model}' không tồn tại — kiểm tra COACH_AI_MODEL") from e
    except anthropic.RateLimitError as e:
        raise AIError("Dịch vụ AI đang quá tải, thử lại sau ít phút") from e
    except anthropic.APIStatusError as e:
        raise AIError(f"Dịch vụ AI trả lỗi ({e.status_code}), thử lại sau") from e
    except anthropic.APIConnectionError as e:
        raise AIError("Không kết nối được dịch vụ AI — kiểm tra mạng") from e

    if resp.stop_reason == "refusal":
        raise AIError("AI từ chối trả lời yêu cầu này, thử lại hoặc chọn tuần khác")
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    if not text:
        raise AIError("AI không trả về nội dung, thử lại")
    if resp.stop_reason == "max_tokens":
        text += "\n\n_(Câu trả lời bị cắt do quá dài)_"
    return text
