import re
import unicodedata
import uuid


def slugify(text):
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def unique_id(base, exists, fallback="item"):
    base = base or fallback
    candidate, n = base, 2
    while exists(candidate):
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def new_activity_id():
    return uuid.uuid4().hex[:12]
