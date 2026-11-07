"""Prepares the environment variables for the Hydra Pay cloud server (e.g. Rumpty).

Usage:  python cloud_env.py https://your-app-address

- Writes .env.cloud: every variable to paste into the host's Environment variables / Env tab.
  It holds secrets: it is git-ignored and never goes into the Docker image. Delete it after pasting.
- Adds CLOUD_URL and BRIDGE_TOKEN to .env, so start_bridge.bat on this laptop talks to that server.
Nothing secret is printed to the screen.
"""
import json
import secrets
import sys
from pathlib import Path

from dotenv import dotenv_values, set_key

HERE = Path(__file__).resolve().parent
ENV = HERE / ".env"
OUT = HERE / ".env.cloud"

# .env keys that belong on the cloud server (the rest are laptop-only)
CLOUD_KEYS = (
    "ULTRAMSG_INSTANCE", "ULTRAMSG_TOKEN", "GEMINI_API_KEY", "GEMINI_MODEL",
    "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "ELEVENLABS_MODEL", "VOICE_ENDPOINT",
    "SMS_PROVIDER", "USSD_PROVIDER", "TELCO_CALLBACK_TOKEN", "TELCO_ALLOWED_IPS",
    "THRIVEVAS_API_KEY", "THRIVEVAS_SENDER_ID", "THRIVEVAS_MSISDN", "THRIVEVAS_PASSWORD",
    "AT_USERNAME", "AT_API_KEY", "AT_SENDER_ID",
)


def main():
    if len(sys.argv) < 2 or not sys.argv[1].startswith("https://"):
        print("Usage: python cloud_env.py https://your-app-address")
        sys.exit(1)
    url = sys.argv[1].rstrip("/")
    local = {k: (v or "").strip() for k, v in dotenv_values(ENV).items()} if ENV.exists() else {}

    token = local.get("BRIDGE_TOKEN") or secrets.token_urlsafe(32)
    ENV.touch(exist_ok=True)
    set_key(str(ENV), "BRIDGE_TOKEN", token, quote_mode="never")
    set_key(str(ENV), "CLOUD_URL", url, quote_mode="never")

    out = {"READER": "bridge", "DATA_DIR": "/data", "PUBLIC_URL": url, "BRIDGE_TOKEN": token}

    try:
        pin = str(json.loads((HERE / "settings.json").read_text(encoding="utf-8")).get("admin_pin", ""))
    except Exception:
        pin = ""
    if pin and pin != "1234":
        out["ADMIN_PIN"] = pin
    else:
        print("! No admin PIN found (settings.json still 1234): add ADMIN_PIN yourself, or changes stay locked.")

    for k, v in local.items():
        if v and (k in CLOUD_KEYS or k.startswith(("THRIVEVAS_", "AT_", "USSD_"))):
            out[k] = v
    out["TELCO_CALLBACK_BASE_URL"] = url        # callbacks go to the cloud now, not ngrok

    try:
        mp = json.loads((HERE / "mpesa_config.json").read_text(encoding="utf-8"))
        mp["callback_url"] = f"{url}/mpesa/callback"
        out["MPESA_CONFIG_JSON"] = json.dumps(mp, separators=(",", ":"))
    except Exception:
        print("! No mpesa_config.json found: M-Pesa prompts won't work in the cloud until MPESA_CONFIG_JSON is set.")

    OUT.write_text("".join(f"{k}={v}\n" for k, v in out.items()), encoding="utf-8")
    print(f"Wrote {OUT.name} with {len(out)} variables: {', '.join(out)}")
    print("Added CLOUD_URL and BRIDGE_TOKEN to .env for the laptop bridge.")
    print("Paste each line of .env.cloud into the host's environment variables, then delete .env.cloud.")


if __name__ == "__main__":
    main()
