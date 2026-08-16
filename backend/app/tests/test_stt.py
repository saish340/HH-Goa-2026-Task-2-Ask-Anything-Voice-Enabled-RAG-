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
