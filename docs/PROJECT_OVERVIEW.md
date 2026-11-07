# Project overview

## Purpose

RFID Pay (currently branded **Hydra Pay** in `settings.json`) is a locally hosted Kenyan tap-card payment system. Each RFID card is linked to a person's name, telephone number, price, state, and—when wallet mode is used—prepaid balance.

## Architecture

```text
RFID card
   -> RC522 reader + ESP32
   -> USB serial: "UID:AA BB CC DD"
   -> dashboard.py (Flask, port 8000)
      -> SQLite database: rfid.db
      -> Browser dashboard: static/index.html
      -> M-Pesa Daraja STK push
      -> UltraMsg WhatsApp API
      -> Switchable SMS provider (ThriveVAS / Africa's Talking)
      -> Switchable USSD provider (ThriveVAS mapper / Africa's Talking)
      -> Gemini / ElevenLabs (optional)
      -> Africa's Talking USSD callback (optional)
```

`ngrok` is optional for local dashboard use. It supplies a public HTTPS URL needed for incoming M-Pesa callbacks, incoming WhatsApp webhooks, and externally hosted WhatsApp voice audio.

## Main components

| Component | Responsibility |
| --- | --- |
| `dashboard.py` | Flask application, serial-port discovery and reading, dashboard/API routes, payment callback, USSD, and WhatsApp webhook endpoints. |
| `store.py` | SQLite schema and operations for cards, scans, wallet transactions, M-Pesa payment attempts, reports, and CSV export. |
| `wallet.py` | Tap behaviour, M-Pesa top-ups/payments, cash top-ups, reversals, receipts, and notifications. |
| `mpesa.py` | Safaricom Daraja authentication, STK Push, status query, and payment polling. |
| `whatsapp.py` | UltraMsg messages/webhook configuration, Gemini calls and transcription, ElevenLabs synthesis. |
| `sms.py` / `telco/` | Transactional SMS queue, delivery/inbound handling, and switchable ThriveVAS/Africa's Talking adapters. |
| `bot.py` | WhatsApp menu, card/payment lookup, phone-number change, AI conversation, and voice-note handling. |
| `ussd.py` | Provider-neutral USSD state machine for PIN-protected cards, statements, M-Pesa, blocking, and language choice. |
| `micropython/` | Firmware currently intended for the ESP32; emits RFID UID lines to USB serial. |
| `RFID_ESP32/` | Arduino firmware alternative; it is not the default firmware described by the code comments. |

## Hardware and firmware

The documented RC522 wiring is SDA/SS→GPIO 5, SCK→18, MOSI→23, MISO→19, RST→22, 3.3V→3V3, and GND→GND. The MicroPython firmware uses the same pins, prints `READY` when the reader is detected, and prints `UID:<UID>` once per card hold.

The dashboard detects common ESP32 USB/serial adapters automatically. A port can be forced with `python dashboard.py COM6`.

## Tap modes

### Prompt mode (current setting)

For a registered card:

1. An OUT card is tapped.
2. The app records it as IN and sends an STK prompt for that card's price.
3. Payment is confirmed by Daraja status polling and, when reachable, its callback.
4. On successful payment, the app records the payment and sends a WhatsApp receipt/optional voice receipt.
5. The next tap changes IN to OUT without charge.

Unknown cards are logged and exposed to the dashboard for registration.

### Wallet mode

In `settings.json`, set `"mode": "wallet"`. An IN tap deducts the card's configured price from its stored balance when sufficient; OUT is free. Balances can be credited by M-Pesa top-up or cash top-up. Low balance can optionally trigger an automatic M-Pesa top-up prompt.

## Data and configuration

| File | Role |
| --- | --- |
| `rfid.db` | Active SQLite database. It is the source of truth for cards, scans, wallet transactions, and payment attempts. |
| `settings.json` | Business name, mode, PIN, prices/limits, notification settings, and webhook behaviour. |
| `mpesa_config.json` | Daraja environment and payment credentials/callback URL. Keep private. |
| `.env` | UltraMsg, Gemini, and ElevenLabs keys. Keep private. |
| `.flask_secret` | Flask session signing secret; generated if absent. Keep private. |
| `names.json`, `phones.json`, `rfid_log.csv` | Legacy data sources used only by the one-time migration in `store.init`; current operations use SQLite. |

## HTTP endpoints

The local dashboard and its JSON APIs require an authenticated session when accessed remotely; loopback access is trusted. `POST /webhook`, `POST /mpesa/callback`, `POST /ussd`, and `GET /voice/<file>.mp3` are deliberately available to third-party integrations.

The main browser endpoint is `/`. Dashboard JSON is served from `/api/data`. The dashboard also provides card registration/editing/replacement, cash or M-Pesa top-up, top-up reversal, and CSV report downloads.
