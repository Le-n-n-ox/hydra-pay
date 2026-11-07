# RFID Pay documentation

This folder describes the current application as implemented in the source code on 7 November 2026. It distinguishes a capability that is implemented locally from a capability that is ready to use in production with a real payment provider.

| Document | Purpose |
| --- | --- |
| [Project overview](PROJECT_OVERVIEW.md) | Architecture, data flow, components, and operating modes. |
| [What works](WHAT_WORKS.md) | Features that are implemented and how to verify them. |
| [What to add](WHAT_TO_ADD.md) | Missing work, deployment prerequisites, security work, and known documentation drift. |

## Fast orientation

The application runs a Flask server on port 8000. An ESP32 with an RC522 RFID reader sends card UID lines through USB serial. The server records card, scan, transaction, and payment data in `rfid.db`, serves a browser dashboard, and can call external services for M-Pesa, WhatsApp, Gemini, ElevenLabs, and USSD.

The configured mode is `prompt`: an IN tap sends an M-Pesa STK prompt; an OUT tap is free. Set `"mode": "wallet"` in `settings.json` to instead deduct an IN-tap price from prepaid card balance.
