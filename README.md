# RFID Pay 💳

Swipe a card on the ESP32 reader, and the card owner gets an M-Pesa prompt on their phone.
Payments show live on a dashboard, and receipts go out on WhatsApp.

## How it works

```
 Card swipe                                   Card owner (WhatsApp)
     |                                                 |
     v                                                 v
 ESP32 + RC522 --USB--> dashboard.py (port 8000) <-- ngrok <-- UltraMsg (webhook)
                          |  - swipe IN = M-Pesa prompt (mpesa.py, Daraja)
                          |  - dashboard page (static/index.html)
                          |  - WhatsApp menu, AI chat, voice notes (bot.py, whatsapp.py:
                          |    UltraMsg + Gemini + ElevenLabs)
                          |  - receipts after payment (wallet.py)
                          v
                       rfid.db  (SQLite: cards, swipes, payments - store.py)
```

## Run it (every time)
1. Plug in the ESP32.
2. Double-click **`start.bat`** (or the **RFID Pay** shortcut on the Desktop). Two windows open,
   **NGROK** and **RFID PAY**. Keep both open.
3. It prints the webhook link and copies it to your clipboard. The bot also sets it in UltraMsg itself.
   If WhatsApp doesn't reply, paste the link into **UltraMsg > Settings > Webhook URL**.
4. Open http://localhost:8000. To add a card, tap it, click **Register it**, fill in name / phone / price,
   then Save (asks for the admin PIN).
5. WhatsApp the bot: **hi**.

> The ngrok link changes every restart, and while RFID Pay runs it takes the WhatsApp number from AquaTrace.

## Files
| File | What it does |
|---|---|
| `start.bat` / `get_ngrok_url.ps1` | One-click launcher (ngrok + dashboard/bot) |
| `dashboard.py` | Web dashboard, reads the ESP32, `/webhook` for WhatsApp, `/mpesa/callback` |
| `wallet.py` | What happens on a swipe, M-Pesa payments, receipts |
| `mpesa.py` | Daraja STK push + status checks |
| `bot.py` / `whatsapp.py` | WhatsApp menu, AI chat, voice notes |
| `sms.py` / `telco/` | SMS receipts and provider-neutral SMS/USSD adapters |
| `store.py` | The SQLite database `rfid.db` |
| `settings.json` | Admin PIN, default price, business name, `"mode": "prompt"` (or `"wallet"`) |
| `mpesa_config.json` | Daraja keys |
| `.env` | UltraMsg / Gemini / ElevenLabs / telco keys (keep private; see `.env.example`) |
| `micropython/` | Code running on the ESP32 |

## WhatsApp menu
**hi**: 1 my card · 2 my recent payments · 3 chat with AI. Voice notes are understood (Gemini) and
answered with a voice note (ElevenLabs).

## Phone access
Same WiFi: the link at the bottom of the dashboard (allow Python through Windows Firewall if asked).
Anywhere: the ngrok link. Remote login needs the admin PIN and stays off until you change it from 1234.

> **ESP32:** runs **MicroPython** with the code in `micropython/` (already uploaded).
> The Arduino sketch in `RFID_ESP32/` is an alternative and isn't on the board.
> To re-upload the MicroPython code: `python -m mpremote connect COM6 cp micropython/mfrc522.py : + cp micropython/main.py :`

## 1. Wiring (RC522 -> ESP32)

| RC522 pin | ESP32 pin |
|-----------|-----------|
| SDA (SS)  | GPIO 5    |
| SCK       | GPIO 18   |
| MOSI      | GPIO 23   |
| MISO      | GPIO 19   |
| IRQ       | not connected |
| GND       | GND       |
| RST       | GPIO 22   |
| 3.3V      | 3V3  (**NOT 5V/VIN - 5V can kill the RC522**) |

## 2. Flash the ESP32
1. Install Arduino IDE.
2. Add ESP32 boards: File > Preferences > Additional boards URL:
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
   then Tools > Board > Boards Manager > install **esp32 by Espressif**.
3. Sketch > Include Library > Manage Libraries > install **MFRC522** (by GithubCommunity).
4. Open `RFID_ESP32/RFID_ESP32.ino`, pick board **ESP32 Dev Module** and your COM port, Upload.
   (If upload hangs on "Connecting...", hold the **BOOT** button on the ESP32.)
5. Optional check: Serial Monitor at 115200 should say `READY: RC522 firmware 0x92` (or 0x91/0x88).
   **Close the Serial Monitor afterwards** - only one program can use the port.

## 3. Run the dashboard
Double-click `start_dashboard.bat`. Browser opens http://localhost:8000.
Tap card/tag: first tap = IN, next tap = OUT, and so on.

- Every scan is saved in `rfid_log.csv` (opens in Excel).
- Give cards names: copy the UID from the dashboard into `names.json`, e.g.
  `"A3 4F 12 9B": "My Card"` - names update live.
- Wrong port picked? Run `python dashboard.py COM5` (use your port).
