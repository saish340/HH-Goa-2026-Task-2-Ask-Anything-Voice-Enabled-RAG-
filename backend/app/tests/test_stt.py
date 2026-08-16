import asyncio
import os

from backend.app.stt.sarvam_client import transcribe_audio


def test_transcribe_empty_audio():
    result = asyncio.run(transcribe_audio(b""))
    assert result["error"] == "Empty audio input"
    assert result["transcript"] == ""


def test_transcribe_without_api_key_skips_network():
    old = os.environ.get("SARVAM_API_KEY")
    os.environ.pop("SARVAM_API_KEY", None)
    try:
        result = asyncio.run(transcribe_audio(b"\x00\x01\x02", "hi-IN"))
        assert result["transcript"] == ""
        assert "not configured" in result["error"]
    finally:
        if old is not None:
            os.environ["SARVAM_API_KEY"] = old


def test_transcribe_uses_multipart_upload_with_subscription_key(monkeypatch):
    """Lock the live-verified Sarvam contract: multipart file + api-subscription-key."""
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"transcript": "hello", "language_code": "en-IN"}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, **kwargs):
            captured.update(kwargs)
            return FakeResponse()

    monkeypatch.setenv("SARVAM_API_KEY", "test-key-123")
    monkeypatch.setattr("backend.app.stt.sarvam_client.httpx.AsyncClient", FakeClient)

    result = asyncio.run(transcribe_audio(b"\x01\x02\x03\x04", "hi-IN", "audio.wav"))

    assert result["transcript"] == "hello"
    assert captured["headers"] == {"api-subscription-key": "test-key-123"}
    assert captured["data"] == {"language_code": "hi-IN", "model": "saaras:v3"}
    name, blob, mime = captured["files"]["file"]
    assert name == "audio.wav"
    assert blob == b"\x01\x02\x03\x04"
    assert mime == "audio/wav"
