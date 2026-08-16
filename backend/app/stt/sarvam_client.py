"""Sarvam AI speech-to-text client with retry and fallback logic.

The REST endpoint expects a multipart ``file`` upload and the
``api-subscription-key`` header (verified live: JSON/base64 and Bearer auth are
rejected with 400).
"""

import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Sarvam API configuration
SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_MODEL = "saaras:v3"
MAX_RETRIES = 3
RETRY_DELAY = 0.5


def _mime(filename: str) -> str:
    if filename:
        lower = filename.lower()
        for ext, mime in (
            (".wav", "audio/wav"),
            (".mp3", "audio/mpeg"),
            (".webm", "audio/webm"),
            (".ogg", "audio/ogg"),
            (".m4a", "audio/mp4"),
        ):
            if lower.endswith(ext):
                return mime
    return "audio/webm"


async def transcribe_audio(
    audio_bytes: bytes,
    language: str = "hi-IN",
    filename: str = "audio.webm",
) -> dict:
    """
    Transcribe audio bytes using Sarvam AI REST API (multipart file upload).

    Args:
        audio_bytes: Raw audio data (WebM, WAV, MP3, ...).
        language: Language code (e.g., 'hi-IN' for Hindi, 'en-IN' for English).
        filename: Original upload name; its extension tells Sarvam the codec.

    Returns:
        dict with keys: transcript, confidence, language, duration_ms
    """
    if not audio_bytes or len(audio_bytes) == 0:
        logger.warning("Empty audio bytes received")
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": language,
            "duration_ms": 0,
            "error": "Empty audio input",
        }

    api_key = os.environ.get("SARVAM_API_KEY", "")
    if not api_key:
        logger.warning("SARVAM_API_KEY not set; skipping network call")
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": language,
            "duration_ms": 0,
            "error": "STT not configured (set SARVAM_API_KEY)",
        }

    headers = {"api-subscription-key": api_key}
    files = {"file": (filename or "audio.webm", audio_bytes, _mime(filename or "audio.webm"))}
    data = {"language_code": language, "model": SARVAM_MODEL}

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(SARVAM_API_URL, headers=headers, files=files, data=data)

                if response.status_code == 200:
                    payload = response.json()
                    return {
                        "transcript": payload.get("transcript", ""),
                        "confidence": float(payload.get("language_probability", 1.0)),
                        "language": payload.get("language_code", language),
                        "duration_ms": 0,
                    }
                elif response.status_code == 401:
                    logger.error("Sarvam API authentication failed (check SARVAM_API_KEY)")
                    return {
                        "transcript": "",
                        "confidence": 0.0,
                        "language": language,
                        "duration_ms": 0,
                        "error": "Authentication failed",
                    }
                elif response.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY * (2 ** attempt)
                        logger.warning(f"Rate limited; retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                else:
                    detail = response.text[:200]
                    logger.error(f"Sarvam API error: {response.status_code} {detail}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
                        continue
                    return {
                        "transcript": "",
                        "confidence": 0.0,
                        "language": language,
                        "duration_ms": 0,
                        "error": f"API error: {response.status_code} {detail}",
                    }
        except asyncio.TimeoutError:
            logger.warning(f"Sarvam API timeout (attempt {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
                continue
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": language,
                "duration_ms": 0,
                "error": "API timeout",
            }
        except httpx.RequestError as e:
            logger.error(f"Sarvam API request error: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
                continue
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": language,
                "duration_ms": 0,
                "error": str(e),
            }

    return {
        "transcript": "",
        "confidence": 0.0,
        "language": language,
        "duration_ms": 0,
        "error": "Max retries exceeded",
    }
