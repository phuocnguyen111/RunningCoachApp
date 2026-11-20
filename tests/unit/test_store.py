import pytest

from coach.store import JsonStore, StoreError


def test_write_then_read_roundtrip(tmp_path):
    store = JsonStore(tmp_path)
    store.write({"name": "Nguyễn"}, "athletes", "a.json")
    assert store.read("athletes", "a.json") == {"name": "Nguyễn"}
    assert "Nguyễn" in (tmp_path / "athletes" / "a.json").read_text(encoding="utf-8")


def test_read_missing_returns_default(tmp_path):
    assert JsonStore(tmp_path).read("x.json", default={}) == {}


def test_failed_write_leaves_original_and_no_temp(tmp_path):
    store = JsonStore(tmp_path)
    store.write({"v": 1}, "a.json")
    with pytest.raises(TypeError):
        store.write({"v": object()}, "a.json")
    assert store.read("a.json") == {"v": 1}
    assert [p.name for p in tmp_path.iterdir()] == ["a.json"]


def test_path_outside_root_rejected(tmp_path):
    store = JsonStore(tmp_path / "data")
    with pytest.raises(StoreError):
        store.write({}, "..", "evil.json")


def test_list_and_delete(tmp_path):
    store = JsonStore(tmp_path)
    store.write({"id": "b"}, "g", "b.json")
    store.write({"id": "a"}, "g", "a.json")
    assert [d["id"] for d in store.list_dir("g")] == ["a", "b"]
    store.delete("g", "a.json")
    assert [d["id"] for d in store.list_dir("g")] == ["b"]
    assert store.list_dir("missing") == []
