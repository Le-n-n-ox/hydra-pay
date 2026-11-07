"""Where Hydra Pay keeps its data and how it reaches the outside world.

Laptop (default): everything lives next to the code, the card reader is on USB, ngrok gives the public link.
Cloud (e.g. Rumpty, see docs/CLOUD_DEPLOY.md): set these environment variables instead:

  READER=bridge           taps arrive from bridge.py on the laptop, not from a USB port
  BRIDGE_TOKEN=...        shared secret the laptop bridge must send
  PUBLIC_URL=https://...  this server's public address (M-Pesa, WhatsApp, SMS and USSD callbacks)
  ADMIN_PIN=...           admin PIN (anything but 1234), needed for every change
  DATA_DIR=/data          folder for the database and settings (put it on a persistent volume)
  MPESA_CONFIG_JSON={...} contents of mpesa_config.json
  PORT=8000               port to listen on (most hosts set this for you)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env", override=False)   # real environment variables win over .env


def env(name, default=""):
    return (os.getenv(name) or default).strip()


DATA_DIR = Path(env("DATA_DIR") or HERE)
DATA_DIR.mkdir(parents=True, exist_ok=True)

PORT = int(env("PORT", "8000"))
READER = env("READER", "usb").lower()          # "usb" (laptop) or "bridge" (cloud)
BRIDGE_TOKEN = env("BRIDGE_TOKEN")
PUBLIC_URL = env("PUBLIC_URL").rstrip("/")
ADMIN_PIN = env("ADMIN_PIN")

# SMS/USSD callbacks default to the public address when it is fixed.
if PUBLIC_URL and not env("TELCO_CALLBACK_BASE_URL"):
    os.environ["TELCO_CALLBACK_BASE_URL"] = PUBLIC_URL
