"""WhatsApp (UltraMsg), Gemini AI and ElevenLabs voice helpers.

Keys are read from .env in this folder (same names as the AquaTrace .env:
ULTRAMSG_INSTANCE, ULTRAMSG_TOKEN, GEMINI_API_KEY, GEMINI_MODEL,
ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID). Keys are never printed.
"""
import base64
import uuid
from pathlib import Path

import requests
from dotenv import dotenv_values

HERE = Path(__file__).parent
import config

VOICE_DIR = config.DATA_DIR / "voice_cache"
VOICE_DIR.mkdir(exist_ok=True)


KEYS_PATH = HERE / ".env"
_FILE_KEYS = {k: (v or "").strip() for k, v in dotenv_values(KEYS_PATH).items()}
# Environment variables (cloud) win over .env (laptop).
KEYS = {k: config.env(k) or v for k, v in _FILE_KEYS.items()}
for _k in ("ULTRAMSG_INSTANCE", "ULTRAMSG_TOKEN", "GEMINI_API_KEY", "GEMINI_MODEL", "ELEVENLABS_API_KEY",
           "ELEVENLABS_VOICE_ID", "ELEVENLABS_MODEL", "VOICE_ENDPOINT"):
    KEYS[_k] = config.env(_k) or KEYS.get(_k, "")
INSTANCE = KEYS.get("ULTRAMSG_INSTANCE", "")
TOKEN = KEYS.get("ULTRAMSG_TOKEN", "")
GEMINI_KEY = KEYS.get("GEMINI_API_KEY", "")
GEMINI_MODEL = KEYS.get("GEMINI_MODEL") or "gemini-flash-latest"
ELEVEN_KEY = KEYS.get("ELEVENLABS_API_KEY", "")
ELEVEN_VOICE = KEYS.get("ELEVENLABS_VOICE_ID") or "21m00Tcm4TlvDq8ikWAM"
ELEVEN_MODEL = KEYS.get("ELEVENLABS_MODEL") or "eleven_multilingual_v2"
VOICE_ENDPOINT = KEYS.get("VOICE_ENDPOINT") or "audio"


def status():
    return {
        "whatsapp": bool(INSTANCE and TOKEN),
        "gemini": bool(GEMINI_KEY),
        "voice": bool(ELEVEN_KEY),
        "keys_file": KEYS_PATH.exists(),
    }


# ---------- public link (ngrok) ----------

_public = {"url": ""}


def public_url():
    if config.PUBLIC_URL:      # cloud: fixed address
        return config.PUBLIC_URL
    if _public["url"]:
        return _public["url"]
    try:
        for t in requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2).json().get("tunnels", []):
            if str(t.get("public_url", "")).startswith("https"):
                _public["url"] = t["public_url"].rstrip("/")
                return _public["url"]
    except Exception:
        pass
    return ""


def set_webhook(url):
    """Point the UltraMsg instance's 'message received' webhook at this app."""
    r = requests.post(f"https://api.ultramsg.com/{INSTANCE}/instance/settings", timeout=20, data={
        "token": TOKEN, "webhook_url": url, "webhook_message_received": "true",
        "webhook_message_download_media": "true",
    })
    return r.ok and '"error"' not in r.text[:200], r.text[:200]


# ---------- sending ----------

def _to(phone):
    phone = str(phone)
    return phone if "@" in phone else "+" + phone.lstrip("+")


def send_text(phone, body):
    if not (INSTANCE and TOKEN) or not phone:
        return False
    try:
        r = requests.post(f"https://api.ultramsg.com/{INSTANCE}/messages/chat", timeout=20,
                          data={"token": TOKEN, "to": _to(phone), "body": body})
        ok = r.ok and '"error"' not in r.text[:200]
        print(f"[WhatsApp] text to {phone}: {'sent' if ok else 'FAILED ' + r.text[:150]}")
        return ok
    except requests.RequestException as e:
        print(f"[WhatsApp] text to {phone} FAILED: {e}")
        return False


def tts(text):
    """ElevenLabs text-to-speech. Returns mp3 bytes or None."""
    if not ELEVEN_KEY:
        return None
    try:
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE}?output_format=mp3_44100_128",
                          headers={"xi-api-key": ELEVEN_KEY}, json={"text": text[:800], "model_id": ELEVEN_MODEL},
                          timeout=60)
        if r.ok:
            return r.content
        print(f"[VOICE] ElevenLabs HTTP {r.status_code}: {r.text[:150]}")
    except requests.RequestException as e:
        print(f"[VOICE] ElevenLabs FAILED: {e}")
    return None


def send_voice(phone, text):
    """Speak the text with ElevenLabs and send it as a WhatsApp audio message."""
    audio = tts(text)
    if not audio or not (INSTANCE and TOKEN):
        return False
    name = f"{uuid.uuid4().hex}.mp3"
    (VOICE_DIR / name).write_bytes(audio)
    url = f"https://api.ultramsg.com/{INSTANCE}/messages/{VOICE_ENDPOINT}"

    def post(audio_value):
        r = requests.post(url, timeout=40, data={"token": TOKEN, "to": _to(phone), "audio": audio_value})
        return r.ok and '"error"' not in r.text[:200]

    try:
        base = public_url()
        ok = (base and post(f"{base}/voice/{name}")) or post(base64.b64encode(audio).decode())
        print(f"[VOICE] voice note to {phone}: {'sent' if ok else 'FAILED'}")
        return ok
    except requests.RequestException as e:
        print(f"[VOICE] voice note to {phone} FAILED: {e}")
        return False


# ---------- Gemini ----------

def gemini(contents, system=None, json_mode=False):
    payload = {"contents": contents}
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    if json_mode:
        payload["generationConfig"] = {"responseMimeType": "application/json"}
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                      headers={"x-goog-api-key": GEMINI_KEY}, json=payload, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Gemini HTTP {r.status_code}: {r.text[:200]}")
    parts = r.json()["candidates"][0]["content"].get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()


def transcribe(media_url):
    """Download a WhatsApp voice note and let Gemini write down what was said."""
    if not GEMINI_KEY:
        return ""
    a = requests.get(media_url, timeout=40)
    a.raise_for_status()
    mime = a.headers.get("Content-Type", "audio/ogg").split(";")[0]
    if not mime.startswith("audio/"):
        mime = "audio/ogg"
    return gemini([{"parts": [
        {"text": "Transcribe this WhatsApp voice note exactly as spoken (English, Kiswahili or Sheng). "
                 "Reply with only the words, nothing else."},
        {"inline_data": {"mime_type": mime, "data": base64.b64encode(a.content).decode()}},
    ]}])
