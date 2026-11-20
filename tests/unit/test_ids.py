import re

from coach.ids import new_activity_id, slugify, unique_id


def test_slugify_strips_vietnamese_diacritics():
    assert slugify("Nguyễn Văn A") == "nguyen-van-a"
    assert slugify("Đặng Thị Đào") == "dang-thi-dao"
    assert slugify("  Trần   Bình!! ") == "tran-binh"


def test_slugify_empty_and_symbols_only():
    assert slugify("") == ""
    assert slugify("!!!") == ""


def test_unique_id_appends_suffix():
    taken = {"nguyen-van-a", "nguyen-van-a-2"}
    assert unique_id("nguyen-van-a", taken.__contains__) == "nguyen-van-a-3"
    assert unique_id("tran-b", taken.__contains__) == "tran-b"


def test_unique_id_falls_back_when_base_empty():
    assert unique_id("", lambda _: False, fallback="hv") == "hv"


def test_new_activity_id_is_12_hex_and_unique():
    ids = {new_activity_id() for _ in range(200)}
    assert len(ids) == 200
    assert all(re.fullmatch(r"[0-9a-f]{12}", i) for i in ids)
