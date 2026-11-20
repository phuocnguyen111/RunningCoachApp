from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from coach import ai, create_app
from coach.config import Config


@pytest.fixture
def ai_client(base_dir):
    app = create_app(Config(base_dir=base_dir, ai_enabled=True, ai_model="claude-opus-5-5"))
    c = app.test_client()
    gid = c.post("/api/groups", json={"name": "Half", "plan_id": "halfmarathon_16w"}).get_json()["id"]
    aid = c.post("/api/athletes", json={"name": "Lê C", "group_id": gid}).get_json()["id"]
    return c, aid


class FakeClient:
    def __init__(self, response=None, exc=None):
        self.calls = []
        self._response, self._exc = response, exc
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.calls.append(kw)
        if self._exc:
            raise self._exc
        return self._response


def _resp(text="## Đánh giá\n- tốt", stop="end_turn"):
    return SimpleNamespace(stop_reason=stop, content=[SimpleNamespace(type="thinking", thinking=""),
                                                      SimpleNamespace(type="text", text=text)])


def test_disabled_returns_503(client):
    aid = client.post("/api/athletes", json={"name": "X"}).get_json()["id"]
    r = client.post(f"/api/athletes/{aid}/ai-feedback", json={"plan_week": 1})
    assert r.status_code == 503


def test_success(monkeypatch, ai_client):
    c, aid = ai_client
    fake = FakeClient(_resp())
    monkeypatch.setattr(ai, "make_client", lambda: fake)
    r = c.post(f"/api/athletes/{aid}/ai-feedback", json={"plan_week": 2})
    assert r.status_code == 200 and r.get_json()["feedback"].startswith("## Đánh giá")
    (call,) = fake.calls
    assert call["model"] == "claude-opus-5-5"
    assert call["fallbacks"] == "default" and "server-side-fallback-2026-07-01" in call["betas"]
    assert "Half Marathon" in call["messages"][0]["content"]
    assert "Lê C" not in call["messages"][0]["content"]


def test_refusal_is_502(monkeypatch, ai_client):
    c, aid = ai_client
    monkeypatch.setattr(ai, "make_client", lambda: FakeClient(_resp("", stop="refusal")))
    r = c.post(f"/api/athletes/{aid}/ai-feedback", json={"plan_week": 2})
    assert r.status_code == 502 and "từ chối" in r.get_json()["error"]


def test_connection_error_is_502(monkeypatch, ai_client):
    c, aid = ai_client
    exc = anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"))
    monkeypatch.setattr(ai, "make_client", lambda: FakeClient(exc=exc))
    r = c.post(f"/api/athletes/{aid}/ai-feedback", json={"plan_week": 2})
    assert r.status_code == 502 and "kết nối" in r.get_json()["error"]


def test_bad_week_and_missing_athlete(ai_client):
    c, aid = ai_client
    assert c.post(f"/api/athletes/{aid}/ai-feedback", json={"plan_week": 99}).status_code == 400
    assert c.post("/api/athletes/missing/ai-feedback", json={"plan_week": 1}).status_code == 404


def test_model_without_server_fallback(monkeypatch, base_dir):
    app = create_app(Config(base_dir=base_dir, ai_enabled=True, ai_model="claude-haiku-5-5"))
    c = app.test_client()
    aid = c.post("/api/athletes", json={"name": "Y"}).get_json()["id"]
    fake = FakeClient(_resp())
    monkeypatch.setattr(ai, "make_client", lambda: fake)
    r = c.post(f"/api/athletes/{aid}/ai-feedback", json={"plan_id": "5k_8w", "plan_week": 1})
    assert r.status_code == 200
    assert "fallbacks" not in fake.calls[0]
