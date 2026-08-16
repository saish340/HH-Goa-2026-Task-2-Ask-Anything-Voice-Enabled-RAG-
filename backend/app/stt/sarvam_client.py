"""Sarvam AI speech-to-text client with retry and fallback logic."""

import asyncio
import base64
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Sarvam API configuration
SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
MAX_RETRIES = 3
RETRY_DELAY = 0.5


async def transcribe_audio(audio_bytes: bytes, language: str = "hi-IN") -> dict:
    """
    Transcribe audio bytes using Sarvam AI API.

    Args:
        audio_bytes: Raw audio data (WAV, MP3, etc.)
        language: Language code (e.g., 'hi-IN' for Hindi, 'en-IN' for English)

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

    if not SARVAM_API_KEY:
        logger.warning("SARVAM_API_KEY not set; skipping network call")
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": language,
            "duration_ms": 0,
            "error": "STT not configured (set SARVAM_API_KEY)",
        }

    # Encode audio as base64 for API transmission
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {SARVAM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "audio": audio_b64,
        "language_code": language,
        "with_timestamps": False,
    }

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(SARVAM_API_URL, json=payload, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "transcript": data.get("transcript", ""),
                        "confidence": float(data.get("confidence", 0.9)),
                        "language": language,
                        "duration_ms": data.get("duration_ms", 0),
                    }
                elif response.status_code == 401:
                    logger.error("Sarvam API authentication failed")
                    return {
                        "transcript": "",
                        "confidence": 0.0,
                        "language": language,
                        "duration_ms": 0,
                        "error": "Authentication failed",
                    }
                elif response.status_code == 429:
                    # Rate limited; retry with backoff
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY * (2 ** attempt)
                        logger.warning(f"Rate limited; retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                else:
                    logger.error(f"Sarvam API error: {response.status_code} {response.text}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
                        continue
                    return {
                        "transcript": "",
                        "confidence": 0.0,
                        "language": language,
                        "duration_ms": 0,
                        "error": f"API error: {response.status_code}",
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
