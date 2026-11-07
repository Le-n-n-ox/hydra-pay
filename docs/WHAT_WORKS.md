# What works now

“Works” below means there is working application code for the feature. Integrations require their service account, credentials, and public callback configuration to be valid before they can operate end to end.

## Local functionality

| Capability | Current behaviour | How to verify |
| --- | --- | --- |
| Dashboard startup | Flask serves the landing page at `http://localhost:8000` and the dashboard at `http://localhost:8000/dashboard`. | Start `dashboard.py` and open the URL. |
| ESP32 reader connection | Detects common USB serial adapters and reads `UID:` lines at 115200 baud. | Plug in the programmed board; dashboard status should show **Reader: connected**. |
| Unknown card handling | Logs the UID and presents it as a new card in the dashboard for registration. | Tap an unregistered tag. |
| Card management | Admin can add/edit a card's name, phone and price, or move a person's record to a replacement tag. | Use the Cards panel and provide the admin PIN. |
| Tap tracking | Records IN/OUT status and scan history. Duplicate card reads are suppressed by firmware. | Tap a registered card, then tap it again. |
| Wallet mode | Prepaid balance is charged for an IN tap; insufficient funds are refused. | Change `settings.json` mode to `wallet`, restart, top up, then tap. |
| Cash top-up and reversal | Admin credits a wallet in cash and can reverse a cash or M-Pesa top-up while retaining an audit row. | Use the dashboard top-up/reversal controls. |
| SQLite persistence | Cards, scans, transactions and payment attempts survive application restarts in `rfid.db`. | Restart the app, then refresh the dashboard. |
| Reports | Daily card/payment/scan/transaction data can be downloaded as CSV. | Use the dashboard download buttons or `/api/export`. |
| Local network access | Binds to all interfaces and displays a same-Wi-Fi address. | Visit the displayed LAN URL from another device on the network. |

## Payment and messaging connectors

| Capability | Implemented flow | Required for end-to-end use |
| --- | --- | --- |
| M-Pesa STK Push | Creates a payment attempt, sends an STK request, polls its status, accepts the Daraja callback, and records success/failure. | Valid Daraja credentials, correct shortcode/passkey/environment, a reachable HTTPS callback, and a customer phone. |
| Tap-to-pay | In prompt mode, an IN tap requests M-Pesa for the card price and sends a receipt after confirmation. | The M-Pesa requirements above. |
| M-Pesa wallet top-up | Requests an STK prompt, credits the wallet only after confirmed payment, then notifies the card holder. | The M-Pesa requirements above. |
| WhatsApp receipts | Sends text receipts to card holder and optional admin copy through UltraMsg. | Valid `ULTRAMSG_INSTANCE` and `ULTRAMSG_TOKEN`. |
| WhatsApp menu | Lets linked users view cards/payment history, change their phone number, request help, and start an AI chat. | UltraMsg webhook configured to public `https://.../webhook`. |
| Gemini assistant and transcription | Builds a constrained, card-aware AI response and can transcribe incoming voice media. | Valid Gemini API key and network access. |
| ElevenLabs voice messages | Creates a voice receipt and can reply to WhatsApp voice messages. | Valid ElevenLabs key; UltraMsg needs access to the audio or accepts base64 audio. |
| USSD menu | Returns Africa's Talking `CON`/`END` responses for card information, recent payments, and M-Pesa top-up. | Africa's Talking service code configured to POST to public `/ussd`. |
| Provider-neutral SMS/USSD | Switches ThriveVAS, Africa's Talking, or disabled (`none`) independently through `.env`; callbacks require a shared token. | Valid provider credentials, callback registration, and a public HTTPS URL. |

## Existing safeguards

- Remote browser access requires a Flask login when `admin_pin` is changed from the shipped `1234` value.
- Admin PIN is required for card edits, replacement, cash top-up, and reversals.
- A payment per card is blocked while another prompt is still pending.
- Payment success is confirmed by a Daraja query; the callback receipt code alone does not mark a payment paid.
- Reversals create separate audit transactions rather than deleting the original top-up.
- The voice-file route restricts names to flat `.mp3` filenames.
