# Hydra Pay 💳

**Tap. Pay. Done.** A tap-card payment system for busy counters: canteens, shops, market stalls and matatus.

A customer taps a card on the reader, an M-Pesa prompt appears on their phone, and once they enter their PIN the payment is confirmed with Safaricom, recorded, and a receipt is sent on WhatsApp or SMS. The owner watches everything live on a dashboard.

## What it does

| Area | Features |
|---|---|
| **Payments** | M-Pesa STK push on every tap (pay-per-tap) or a prepaid wallet balance. A payment is marked PAID only after Safaricom confirms it (callback, with a status check as backup). Cash top-ups and undo (undo adds a reversal entry; nothing is deleted). |
| **Dashboard** (React) | Live stats, hourly activity and payment-outcome charts, live feed, who is inside. Cards: register, edit, top up, block/unblock, move a person to a replacement card. Payments and activity history with search, filters and CSV export. Light/dark/system mode and six colour themes. Works on phones. |
| **Landing page** | Public page at `/` explaining the product, with an interactive demo (simulated, no real money). |
| **WhatsApp** (UltraMsg) | Receipts with the M-Pesa code. Bot menu: my card, my payments, change my number, AI assistant (Gemini; English, Kiswahili, Sheng), help. Voice notes understood and answered (ElevenLabs). |
| **SMS** (ThriveVAS or Africa's Talking) | Receipts, fallback when WhatsApp fails, low-balance and security alerts, delivery reports, inbound keywords. Emoji are stripped so each message stays one SMS. |
| **USSD** (ThriveVAS or Africa's Talking) | Menu for any phone: my card, my payments, pay/top up, statement by SMS, block a lost card, change PIN, English/Kiswahili. Customer PIN with lockout. |
| **Security** | Admin PIN for every change. Remote dashboard login stays off until the default PIN is changed. Callback URLs carry a secret token. Keys live in `.env`, never in code. |
| **Reader** | ESP32 + RC522 over USB. The dashboard finds the port by itself and reconnects if the reader is unplugged. |

## How it works

```text
 Card tap
    │
    ▼
 ESP32 + RC522 ──USB serial "UID:AA BB CC DD"──▶ dashboard.py  (Flask, port 8000)
                                                  │
                     ┌────────────────────────────┼────────────────────────────┐
                     ▼                            ▼                            ▼
              M-Pesa Daraja              WhatsApp (UltraMsg)          SMS / USSD
              STK push + status          + Gemini + ElevenLabs        ThriveVAS or Africa's Talking
                     │
                     ▼
              rfid.db (SQLite): cards, taps, wallet transactions, payments, SMS log, USSD sessions

 Browser:  /            landing page (public)
           /dashboard   dashboard (admin PIN when opened from another device)
```

ngrok gives the laptop a public HTTPS address, so Safaricom, UltraMsg and the SMS/USSD provider can reach the callbacks and people can open the pages from anywhere.

## Run it (every time)

1. Plug in the ESP32 reader.
2. Double-click **`start.bat`** (or the **RFID Pay** shortcut). Two windows open, **NGROK** and **RFID PAY**. Keep both open.
3. Your browser opens the dashboard at **http://localhost:8000/dashboard**.
   - Landing page: http://localhost:8000
   - Phone on the same WiFi: `http://<laptop-ip>:8000/dashboard` (shown in the dashboard sidebar; allow Python through Windows Firewall if asked)
   - From anywhere: your ngrok address, e.g. `https://<your-domain>.ngrok-free.dev` and `/dashboard`
4. To add a card: tap it on the reader, click **Register it**, enter name, phone and price, then save with the admin PIN.
5. WhatsApp the bot **hi** to see the customer menu.

`start.bat` installs the Python packages, starts ngrok and the dashboard, sets the WhatsApp webhook automatically, and copies the webhook link to your clipboard. If WhatsApp doesn't reply, paste that link into **UltraMsg › Settings › Webhook URL**.

> Free ngrok allows one tunnel at a time and shows a "Visit Site" warning page to first-time browser visitors. Your free ngrok address stays the same between restarts.

### Or run it in the cloud

The dashboard, M-Pesa, WhatsApp, SMS and USSD can run on a cloud server (e.g. Rumpty) from the root `Dockerfile`, while the reader stays on the laptop: **`start_bridge.bat`** sends each tap to the server, so the laptop no longer needs ngrok. Setup: [docs/CLOUD_DEPLOY.md](docs/CLOUD_DEPLOY.md).

## Configuration

| File | What goes in it |
|---|---|
| `settings.json` | Business name, `"mode"` (`"prompt"` = pay per tap, `"wallet"` = prepaid), **admin PIN** (change it from `1234`), prices and top-up limits, notification switches, USSD code. Most SMS/USSD switches can also be changed from the dashboard. |
| `mpesa_config.json` | Safaricom Daraja keys, shortcode, passkey, environment (`sandbox` or live), callback URL. |
| `.env` | Keys for UltraMsg, Gemini, ElevenLabs and the SMS/USSD provider. Copy **`.env.example`** for the full list. |

To turn on SMS with ThriveVAS, add to `.env`:

```ini
SMS_PROVIDER=thrivevas
THRIVEVAS_API_KEY=...            # or THRIVEVAS_MSISDN + THRIVEVAS_PASSWORD so keys renew automatically
TELCO_CALLBACK_TOKEN=...         # any long random string
TELCO_CALLBACK_BASE_URL=https://<your-domain>.ngrok-free.dev
```

Then restart and use **Dashboard › SMS & USSD › Send a test SMS**. That page also shows the callback URLs to paste into the provider's portal. Full guide: [docs/USSD_SMS_SETUP.md](docs/USSD_SMS_SETUP.md).

`.env`, `mpesa_config.json`, `.flask_secret` and `rfid.db` hold secrets or customer data. They are git-ignored; keep them private.

## Project layout

| Path | What it is |
|---|---|
| `start.bat`, `get_ngrok_url.ps1` | One-click launcher |
| `bridge.py`, `start_bridge.bat` | Cloud mode: sends card taps from the USB reader to the cloud server |
| `Dockerfile`, `config.py`, `cloud_env.py` | Cloud server image, environment settings, helper that prepares the cloud variables |
| `dashboard.py` | Flask server: reads the reader, serves the pages, JSON API, M-Pesa / WhatsApp / SMS / USSD callbacks |
| `wallet.py` | What happens on a tap, M-Pesa and cash top-ups, receipts, notifications |
| `mpesa.py` | Daraja STK push and status checks |
| `store.py` | SQLite database (`rfid.db`) |
| `bot.py`, `whatsapp.py` | WhatsApp menu, AI chat, voice notes |
| `sms.py`, `ussd.py`, `telco/` | SMS sending and logging, USSD menu, provider adapters (`thrivevas`, `africastalking`, `none`) |
| `frontend/` | React source for the landing page and dashboard (Vite, TypeScript, Tailwind, shadcn/ui, Recharts, Motion). See [frontend/README.md](frontend/README.md). |
| `static/` | Built frontend served by Flask. Rebuild with `cd frontend && npm run build`. |
| `micropython/` | Firmware running on the ESP32 |
| `RFID_ESP32/` | Arduino firmware (alternative, not on the board) |
| `RFID_Tool/`, `tools/` | Utilities to read, dump and change tags |
| `tests/` | Backend tests (`python -m pytest tests`) |
| `docs/` | Overview, what works, what's left, SMS/USSD setup |
| `pitch/` | Pitch decks and QR codes |
| `Daraja_Prompt/` | Separate command-line tool: send an M-Pesa prompt, optional crypto pricing (own `config.json`) |

## Hardware

### Wiring (RC522 → ESP32)

| RC522 pin | ESP32 pin |
|---|---|
| SDA (SS) | GPIO 5 |
| SCK | GPIO 18 |
| MOSI | GPIO 23 |
| MISO | GPIO 19 |
| RST | GPIO 22 |
| IRQ | not connected |
| GND | GND |
| 3.3V | 3V3 (**not 5V/VIN, 5V can damage the RC522**) |

### Firmware

The ESP32 runs **MicroPython** with the code in `micropython/` (already uploaded). It prints `READY: RC522 firmware 0x..` when the reader is found and `UID:XX XX XX XX` once per tap.

To re-upload it (use your COM port):

```bash
python -m mpremote connect COM6 cp micropython/mfrc522.py : + cp micropython/main.py :
```

Only one program can use the serial port at a time, so close any serial monitor before starting the dashboard. If the wrong port is picked, run `python dashboard.py COM5`.

## Development

```bash
# backend tests
python -m pytest tests

# frontend (landing on :5173, dashboard on /dashboard; API calls go to dashboard.py on :8000)
cd frontend
npm install
npm run dev
npm run build      # writes to ../static, which Flask serves
```

## More documentation

- [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md): architecture, components, endpoints
- [docs/WHAT_WORKS.md](docs/WHAT_WORKS.md): implemented features and how to check them
- [docs/WHAT_TO_ADD.md](docs/WHAT_TO_ADD.md): what's still needed before real-world use
- [docs/USSD_SMS_SETUP.md](docs/USSD_SMS_SETUP.md): SMS and USSD providers
- [docs/CLOUD_DEPLOY.md](docs/CLOUD_DEPLOY.md): run the server in the cloud with the laptop bridge

---

Team HYDRA-PAY · Technical University of Kenya
