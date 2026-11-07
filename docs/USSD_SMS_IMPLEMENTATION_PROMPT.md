# Implementation prompt: USSD + SMS with switchable providers (ThriveVAS and Africa's Talking)

> Hand this whole file to the developer / AI coding agent doing the work.
> Repo: `ESP32_RFID` (Hydra Pay). Read `docs/PROJECT_OVERVIEW.md` first.

---

## 1. Context — what exists today

| Where | What it does |
|---|---|
| `ussd.py` (47 lines) | `handle(phone, text)` builds a 3-option menu: **1** My card, **2** My payments, **3** Top up with M-Pesa. Returns `CON …` / `END …` strings (Africa's Talking format). |
| `dashboard.py` → `ussd_route()` (`POST /ussd`) | Reads `phoneNumber` and `text` from the form, calls `ussd.handle`, returns `text/plain`. Listed in `open_paths` so it skips login. |
| `wallet.notify(card, text)` | The **only** customer-notification path. Sends WhatsApp (UltraMsg) to the card owner + optional admin copy. |
| `store.py` | SQLite (`rfid.db`). Tables: `cards(uid, name, phone, price, balance, status, created)`, `scans`, `transactions`, `payments(… source, status, checkout_id, mpesa_receipt, name)`. `to_254()` normalises phones. |
| `settings.json` | `business_name`, `mode` (`prompt`/`wallet`), `admin_pin`, limits, `notify_taps`, `admin_whatsapp`, … |
| `.env` | UltraMsg, Gemini, ElevenLabs keys only. **No SMS/USSD keys.** |

Africa's Talking is **not** in use: there is no AT account configured, no AT library, and no code that calls any AT API — `ussd.py` only mimics its callback format. There is **no SMS code anywhere** in the project.

## 2. What is missing / wrong in the current USSD

1. **Locked to one provider's request format.** Field names (`phoneNumber`, `text`) and the `CON`/`END` reply are hard-coded for Africa's Talking. No way to use ThriveVAS.
2. **No caller verification.** `/ussd` is public and trusts any POST. Anyone who finds the ngrok URL can query any phone's card data or trigger M-Pesa prompts to any linked number.
3. **Ignores `sessionId`, `serviceCode`, `networkCode`.** No session log, no per-session state, can't tell which short code was dialled.
4. **Only the first card is used.** `cards[0]` — a phone with several cards (parent with kids' cards, etc.) can't reach the others.
5. **No navigation.** No "0 Back" / "00 Main menu"; one wrong key ends the session with `END Invalid choice.`
6. **Shows "Balance" in prompt mode**, where balance is meaningless (settings default is `prompt`). Menu must adapt to `wallet.prompt_mode()`.
7. **Amount validation happens late.** Invalid/out-of-range amounts only fail inside `start_mpesa_topup`; user gets no chance to re-enter. Decimal/comma input (`"50.5"`, `"1,000"`) is truncated silently.
8. **No confirmation step** before sending an M-Pesa STK prompt.
9. **Payment history is inefficient**: `recent_payments(200)` then filters in Python; misses older payments and shows `not paid` for still-pending ones.
10. **No length control.** USSD screens are limited (~160–182 chars depending on network/provider); long names or 3 payment rows can be cut off.
11. **No unregistered-user path** beyond a dead-end `END`.
12. **No security PIN** for money actions or for anything that reveals personal data.
13. **No Swahili** option.
14. **No logging/rate-limit**: errors print to console only; a caller can spam top-up prompts.
15. **No SMS at all**: no SMS receipts, no fallback when WhatsApp is off/unreachable, no SMS keywords, no delivery reports.
16. **Docs/pitch claim USSD "running end to end"** — not verifiable without a provider account.

## 3. Goal

Build a **provider-agnostic SMS + USSD layer** where the active provider is chosen in config:

- `thrivevas` — **primary** (the account we have).
- `africastalking` — **second adapter**, fully implemented so we can switch later without code changes.
- `none` — feature off (current behaviour for SMS = nothing sent; USSD route returns 404 or a polite `END`).

USSD and SMS may use **different** providers (e.g. `ussd_provider=thrivevas`, `sms_provider=africastalking`).

## 4. Architecture to build

```
telco/
  __init__.py        get_sms(), get_ussd()  → returns the configured adapter
  base.py            SmsProvider / UssdProvider interfaces + common dataclasses
  thrivevas.py       ThriveVAS adapter (SMS send, delivery report, inbound SMS, USSD parse/format)
  africastalking.py  Africa's Talking adapter (same interface)
  null.py            no-op adapter (provider = none)
sms.py               high-level: send(phone, text, kind), keywords, opt-out, queue/retry
ussd.py              menu engine — provider-neutral, works only with UssdRequest / UssdReply
```

### 4.1 Common types (`telco/base.py`)

```python
@dataclass
class UssdRequest:
    session_id: str
    service_code: str
    phone: str          # already normalised with store.to_254()
    text: str           # full '*'-joined input history ('' on first screen)
    network: str = ""
    raw: dict = field(default_factory=dict)

@dataclass
class UssdReply:
    message: str
    end: bool           # True = close session

class UssdProvider:
    name: str
    def parse(self, flask_request) -> UssdRequest: ...
    def render(self, reply: UssdReply) -> flask.Response: ...
    def verify(self, flask_request) -> bool: ...   # caller authentication

class SmsProvider:
    name: str
    def send(self, phone254: str, text: str) -> SmsResult: ...   # SmsResult(ok, message_id, cost, error)
    def parse_delivery(self, flask_request) -> DeliveryReport | None: ...
    def parse_inbound(self, flask_request) -> InboundSms | None: ...
    def verify(self, flask_request) -> bool: ...
```

`ussd.py` must **never** read raw form fields or emit `CON`/`END` itself — only `UssdReply`.

### 4.2 Africa's Talking adapter (`telco/africastalking.py`)

Use plain `requests` (no new SDK dependency).

- **SMS send**: `POST https://api.africastalking.com/version1/messaging` (sandbox: `https://api.sandbox.africastalking.com/version1/messaging`).
  Headers: `apiKey: <AT_API_KEY>`, `Accept: application/json`, `Content-Type: application/x-www-form-urlencoded`.
  Form: `username`, `to` (`+2547…`), `message`, optional `from` (sender ID / short code).
  Success = `SMSMessageData.Recipients[0].statusCode` in (100, 101, 102); store `messageId` and `cost`.
- **USSD callback** (form POST): `sessionId`, `serviceCode`, `phoneNumber`, `text`, `networkCode`. Reply `text/plain` starting `CON ` or `END `.
- **Delivery report** callback: `id`, `status`, `phoneNumber`, `networkCode`, `failureReason`.
- **Inbound SMS** callback: `from`, `to`, `text`, `date`, `id`, `linkId`.
- AT does not sign callbacks → verify with the shared-secret token in the URL (see §7) and optional IP allowlist.

### 4.3 ThriveVAS adapter (`telco/thrivevas.py`)

Source: ThriveVas public docs at https://docs.thrivevas.com (page content served from `/content/*.md`), read 2026-11-07. **SMS is fully documented; USSD is not documented at all** (see 4.3.4).

#### 4.3.1 Getting an API key (confirmed)

API keys are **generated from account credentials** and can **expire**.

```
POST https://identity.thrivevas.com/v1/auth/api-key/generate
Content-Type: application/json
Authorization: Basic base64(MSISDN:password)     # MSISDN as stored on the account, e.g. 254700000001 (no +, not 07…)
Body: {"name": "hydra-pay", "lifetime_seconds": 86400}
→ 200 {"token": "<API key>"}
```

Requirements:
- Support **both** config styles: a fixed `THRIVEVAS_API_KEY`, **or** `THRIVEVAS_MSISDN` + `THRIVEVAS_PASSWORD` so the adapter generates a key itself.
- In generate mode, cache the token in memory (never write the password or token to logs or `rfid.db`), refresh it before `lifetime_seconds` runs out, and on a **428** ("Invalid API Key or session expired") or **401** regenerate once and retry the request once.
- The docs say `base64url(MSISDN:password)`. Use standard Basic auth (`requests.auth.HTTPBasicAuth`) first. If that returns 401, try URL-safe base64, and record which one works in a code comment.
- Make `lifetime_seconds` configurable (`THRIVEVAS_KEY_LIFETIME`, default 86400). Ask ThriveVas what the maximum allowed value is.

#### 4.3.2 Sending SMS (confirmed)

```
POST https://sms.thrivevas.com/v1/message/send
Content-Type: application/json
x-api-key: <token>
{
  "message": "Hydra Pay: KSh 200 received ...",
  "msisdn": "+254712345678",                 # comma-separated for up to 50 numbers
  "sender_id": "ThriveVas",                  # optional; your registered sender ID, defaults to ThriveVas
  "callback_url": "https://<public>/sms/delivery/<token>"   # optional; delivery report destination
}
→ success: {"message": "SMS successfully queued for sending. Total recipients 1", "status": 200, "transaction_id": 2295}
→ failure: {"status": 428, "message": "error message"}
```

- Send numbers as `+254…`. Convert with `"+" + store.to_254(phone)`.
- Success means `status == 200` **in the JSON body** (also check the HTTP status). Save `transaction_id` as `sms_log.message_id`.
- Optional extra fields: `country_code` (default `ke`), and for scheduling `schedule: true`, `date` (`YYYY-MM-DD`) and `send_time` (`HH:MM:SS`). Scheduled sending can be used for the admin daily summary.
- At most **50 recipients** per call. Larger admin broadcasts must be split into batches, or use the file-upload endpoint below.
- Error codes to handle:

  | Code | Meaning |
  |---|---|
  | 400, 418, 421, 422 | Bad or invalid parameters. Don't retry. |
  | 401, 428 | Bad or expired key. Regenerate the key once (see 4.3.1). |
  | 403 | Forbidden. |
  | 404 | Not found. |
  | 405 | Wrong method. |
  | 406 | Not JSON. |
  | 429 | Too many requests. Back off and retry. |
  | 500, 503 | Server error or maintenance. Retry with backoff. |

- **Bulk and personalised sending (optional, for admin broadcasts).** `POST https://sms.thrivevas.com/v1/message/send/upload-file` (multipart form) takes these fields: `message`, `file` (CSV, first row is headers, first column `msisdn`), and optionally `sender_id`, `campaign_name`, `country_code`, `callback_url`, `schedule`, `date`, `send_time`. Later columns can be referenced in the message as `[name]`, `[balance]` and so on, for example "Dear [name], your balance is KSh [balance]". The file must be under 100 MB.

#### 4.3.3 Delivery reports (confirmed)

ThriveVas posts a JSON report to the `callback_url` you send with each SMS once the message has been delivered or has failed:

```json
{"msisdn": "254710XXXXXX", "status": 3, "country": "ke", "network": "Safaricom",
 "status_description": "Delivered To Teminal", "transaction_id": 2295}
```

Map the `status` value as follows:

| `status` | Meaning | `sms_log.status` |
|---|---|---|
| 0 | Failed, not sent to the network (billing issue) | `FAILED_BILLING` |
| 1 | Failed, not sent to the network | `FAILED` |
| 2 | Sent to the network, but no delivery report came back | `PENDING` |
| 3 | Delivered to the phone | `DELIVERED` |

Match the report by `transaction_id`, and also by `msisdn` when a single send had several recipients. Because ThriveVas doesn't sign these callbacks, secure them with the URL token from §7. If a status-0 (billing) report comes in, alert the admin (throttled to once per day).

#### 4.3.4 Not documented publicly — get these from ThriveVas before building

Contact: 0701468468 · management@thrive-waves.com · https://thrivevas.com/contact. Their USSD page only says "session-based flows, two-way responses, webhooks".

| Item | Status |
|---|---|
| **USSD callback**: HTTP method, field names (session ID, service code, MSISDN, input, network) | `TODO`: ask ThriveVas |
| USSD input: full `*`-joined history (like Africa's Talking) **or** only the latest key? | `TODO` |
| USSD reply format: `CON`/`END` prefix, JSON, or something else | `TODO` |
| Maximum USSD screen length and session timeout | `TODO` |
| USSD code assignment (shared code such as `*XXX*YY#` vs a dedicated code), cost, and how the callback URL is set | `TODO` |
| **Inbound / two-way SMS** callback fields (for `BAL`, `STMT`, `STOP` keywords) | `TODO`: listed as a product, not documented |
| SMS balance/credit-check endpoint | `TODO`: none documented. Until there is one, show "unknown" on the dashboard. |
| Callback IP ranges for allowlisting | `TODO` |
| Test/sandbox environment | None documented. Test against live with your own number and a small amount of credit. |
| Sender ID | The default `ThriveVas` works. A branded "HYDRAPAY" sender ID costs KSh 7,500 per network (pricing page) and needs network approval. |

Requirements for building the USSD and inbound parts before the spec arrives:
- Build the ThriveVas USSD adapter as a **configurable mapper**. Field names (`THRIVEVAS_USSD_FIELD_SESSION`, `…_PHONE`, `…_TEXT`, `…_CODE`), the input style (`cumulative` or `latest`), and the reply style (`prefix` or `json`) all come from `.env`. Default to the Africa's Talking-style values so the adapter works if ThriveVas copies that format, which most Kenyan aggregators do.
- If the input style is `latest`, rebuild the full `text` history from the session store keyed by `session_id` (§5.6), so `ussd.py` always receives cumulative, Africa's Talking-style `text`.
- When `TELCO_DEBUG=1`, log the raw headers and body of every USSD or inbound callback so the field names can be confirmed from live traffic on the first test dial. Mask phone numbers in the logs except for the last 3 digits.
- If ThriveVas can't provide USSD, set `USSD_PROVIDER=africastalking` and keep `SMS_PROVIDER=thrivevas`. That combination must work.

#### 4.3.5 Pricing reference (thrivevas.com/pricing, updated 2025-10-12, KES excluding VAT)

Per-SMS rates fall with volume:

| Network | Volume | KES per SMS |
|---|---|---|
| Safaricom | Below 50k | 0.70 |
| Safaricom | 50k–300k | 0.50 |
| Safaricom | Above 300k | 0.35 |
| Other networks | Below 200k | 0.70 |
| Other networks | Above 200k | 0.50 |

This is why §6 requires stripping emoji: each message must stay within one 160-character GSM-7 segment.

### 4.4 Config

`.env` (secrets):
```
# active providers: thrivevas | africastalking | none
USSD_PROVIDER=thrivevas
SMS_PROVIDER=thrivevas

# ThriveVas: either a fixed key...
THRIVEVAS_API_KEY=
# ...or account login, so the app generates and refreshes keys itself
THRIVEVAS_MSISDN=            # 2547XXXXXXXX exactly as on the account
THRIVEVAS_PASSWORD=
THRIVEVAS_KEY_LIFETIME=86400
THRIVEVAS_IDENTITY_URL=https://identity.thrivevas.com/v1/auth/api-key/generate
THRIVEVAS_SMS_URL=https://sms.thrivevas.com/v1/message/send
THRIVEVAS_SENDER_ID=ThriveVas
# ThriveVas USSD mapping (undocumented; confirm with ThriveVas, defaults = Africa's Talking style)
THRIVEVAS_USSD_FIELD_SESSION=sessionId
THRIVEVAS_USSD_FIELD_PHONE=phoneNumber
THRIVEVAS_USSD_FIELD_TEXT=text
THRIVEVAS_USSD_FIELD_CODE=serviceCode
THRIVEVAS_USSD_INPUT=cumulative     # cumulative | latest
THRIVEVAS_USSD_REPLY=prefix         # prefix (CON/END) | json
TELCO_DEBUG=0

AT_USERNAME=sandbox
AT_API_KEY=
AT_SENDER_ID=
AT_ENV=sandbox               # sandbox | live

TELCO_CALLBACK_TOKEN=        # long random string, part of every callback URL
TELCO_ALLOWED_IPS=           # optional comma list
```
Add a `.env.example` with these names and empty values. Never print keys.

`settings.json` (non-secret, editable from dashboard):
```json
"ussd_code": "*XXX*YY#",
"ussd_language_default": "en",
"sms_receipts": true,
"sms_when_whatsapp_fails": true,
"sms_low_balance": true,
"sms_admin_alerts": true,
"ussd_pin_required": true,
"ussd_max_prompts_per_hour": 5
```

## 5. USSD menu to implement (`ussd.py`)

Screen text must stay ≤ **160 chars** (configurable) — add a `fit(text)` helper that trims names and asserts length in tests.

### 5.1 Navigation rules (every screen)
- `0` = Back, `00` = Main menu, `99` = Exit/Language where shown.
- Invalid input → re-show the same screen prefixed `Invalid choice.` (do **not** end session).
- Implement the menu as a small state machine walked over the cumulative `text` history, handling `0`/`00` by popping/clearing the step stack.

### 5.2 Registered caller — main menu
```
CON Hydra Pay - Jane
1. My card
2. My payments
3. Pay / Top up (M-Pesa)
4. Get statement by SMS
5. Lost card / block card
6. Change PIN
7. Lugha / Language
```
- If the phone has **more than one card**: first screen is `Choose card: 1. Jane 2. Tom …` (max 5, paginate `9. More`). Selected card carries through the session.
- In **prompt mode**: hide balance; "My card" shows price per tap and IN/OUT status; option 3 becomes "Pay now (KSh {price})".
- In **wallet mode**: show balance; option 3 asks for amount.

### 5.3 Top-up / pay flow
1. Enter amount → validate with `wallet.check_amount` **immediately**; accept `1,000`, reject decimals with a clear message, allow re-entry (max 3 tries).
2. Ask `Pay to: 1. This number 2. Another M-Pesa number` → if 2, enter number, validate with `to_254` (must be `2547…`/`2541…`, 12 digits).
3. Confirm: `Send M-Pesa prompt of KSh 200 to 0712…678 for Jane? 1. Yes 2. No`.
4. PIN check if `ussd_pin_required` (see §5.5).
5. Rate-limit per phone (`ussd_max_prompts_per_hour`) and refuse if `store.pending_payment(uid)` exists.
6. Call `wallet.start_mpesa_topup(uid, amount, source="ussd", phone=…)` → `END Check your phone for the M-Pesa prompt.`
7. Final confirmation arrives later via SMS (and WhatsApp if on).

### 5.4 Other options
- **My payments**: last 3 for the selected card via a new `store.payments_for_uid(uid, limit)` (indexed query). Show `PAID`, `PENDING`, `FAILED` correctly, short date `07/11 14:05`.
- **Statement by SMS**: send last 5–10 payments/transactions by SMS → `END Statement sent by SMS.`
- **Lost card / block card**: confirm + PIN → set card blocked (add `blocked INTEGER DEFAULT 0` column via the same `PRAGMA table_info` migration style in `store.init`). `wallet.on_tap` / `on_tap_prompt` must refuse blocked cards and alert the owner + admin. Unblocking is admin-only on the dashboard.
- **Change PIN**: old PIN → new 4-digit PIN → confirm.
- **Language**: English / Kiswahili; store per phone. All strings in one `STRINGS = {"en": {...}, "sw": {...}}` dict.

### 5.5 Customer PIN
- New table `ussd_users(phone TEXT PRIMARY KEY, pin_hash TEXT, lang TEXT, failed INTEGER, locked_until TEXT, created TEXT)`.
- First use: "Set a 4-digit PIN" → enter twice. Hash with `hashlib.scrypt` + per-user salt (no plain PINs).
- 3 wrong PINs → lock 30 min, SMS the owner.
- Reject `0000`, `1234`, repeated digits.

### 5.6 Sessions & logging
- New table `ussd_sessions(session_id PRIMARY KEY, phone, service_code, provider, started, last_seen, steps TEXT, last_screen TEXT, ended INTEGER)` — used for audit, for ThriveVAS input reconstruction, and for dashboard display.
- Purge sessions older than 30 days.

### 5.7 Unregistered caller
```
CON Hydra Pay
This number has no card.
1. How to get a card
2. Contact the desk
```
Option 1/2 → `END` with info; also SMS the admin "Unregistered USSD caller 2547…" (throttled, once per number per day).

## 6. SMS features (`sms.py`)

`sms.send(phone, text, kind)` → picks provider, writes to a new `sms_log(id, time, phone, kind, text, provider, message_id, status, cost, error)` table, sends in a background thread, retries 2× with backoff on network errors (not on provider rejections).

Wire it into the app:
1. **Payment receipt**: in `wallet.finish_payment` send a short SMS receipt (≤160 chars, no emoji/markdown) when `sms_receipts` is on: `Hydra Pay: KSh 200 received from Jane. M-Pesa QWE123ABC. Ref RFP00042. 07/11 14:05`.
2. **WhatsApp fallback**: change `wallet.notify` to call `whatsapp.send_text`; if it returns `False` (or WhatsApp is off) and `sms_when_whatsapp_fails` is on, send the SMS version. Add a plain-text `sms_text` variant for each notification instead of reusing WhatsApp markdown.
3. **Low balance** (wallet mode) and **failed/cancelled payment** SMS.
4. **Card blocked / PIN locked / PIN changed** security SMS.
5. **Admin alerts** to `admin_phone` (new setting): unknown card taps (throttled), daily summary at a set time (from `store.daily_summary`), provider errors.
6. **Inbound SMS keywords** (if the provider gives a two-way number): `BAL`, `STMT`, `HELP`, `STOP`/`START`. Route: `POST /sms/inbound/<token>`.
7. **Opt-out**: `STOP` sets `sms_opt_out=1` on `ussd_users`; never send marketing/non-transactional SMS to opted-out numbers (Kenya Data Protection Act / CA rules). Transactional receipts may still go if policy allows — make it a setting.
8. **Delivery reports**: `POST /sms/delivery/<token>` updates `sms_log.status`.
9. **Encoding**: strip emoji and non-GSM-7 characters before sending to avoid UCS-2 (70-char) splitting and double cost; warn when a message is > 160 chars.

## 7. Routes & security (`dashboard.py`)

| Route | Purpose |
|---|---|
| `POST /ussd/<token>` | USSD callback (provider chosen by `USSD_PROVIDER`). Keep old `/ussd` returning 404 once migrated. |
| `POST /sms/delivery/<token>` | Delivery reports |
| `POST /sms/inbound/<token>` | Inbound SMS |
| `GET /api/telco/status` (login required) | Providers active, balance if provider API supports it, last 20 sms_log / ussd_sessions |
| `POST /api/sms/test` (login required) | Send a test SMS from the dashboard |
| `POST /api/ussd/simulate` (login required) | Run `ussd.handle` with a fake request for testing |

- `<token>` = `TELCO_CALLBACK_TOKEN`; compare with `secrets.compare_digest`; wrong token → 404. Add the `/ussd/`, `/sms/` prefixes to `open_paths`.
- Optional IP allowlist from `TELCO_ALLOWED_IPS` (respect `X-Forwarded-For` only when behind ngrok).
- Call the adapter's `verify()` too (for providers that sign requests).
- Limit request body size; always return a valid provider reply even on exceptions (`END Sorry, try again later.`).
- Never echo full phone numbers or names to unregistered callers.

## 8. Dashboard UI (`static/index.html`)

- **SMS & USSD** panel: active providers, USSD code, callback URLs to paste into the provider portal (built from the ngrok URL like the WhatsApp webhook), test-SMS box, recent SMS log with status, recent USSD sessions.
- **USSD simulator**: phone field + input box that shows each screen exactly as a handset would — so the menu can be tested without a provider.
- Card list: "Blocked" badge + Unblock button.
- Settings form for the new `settings.json` keys.

## 9. Startup

In `dashboard.py __main__`, add `connect_telco()` like `connect_whatsapp()`: print the active providers, warn on missing keys, and print the exact callback URLs (`{ngrok}/ussd/{token}`, etc.). Update `start.bat` to copy these too.

## 10. Tests (`tests/`, pytest)

- `ussd.handle` for every path: registered/unregistered, multi-card, prompt vs wallet mode, back/home navigation, invalid inputs, PIN set/verify/lockout, rate limit, pending-payment guard, ≤160-char screens.
- Each adapter: `parse()` and `render()` round-trip with recorded sample payloads (AT samples from their docs; ThriveVAS samples captured with `TELCO_DEBUG`).
- `sms.send` with `requests` mocked: success, provider rejection, network retry, emoji stripping, opt-out.
- Route tests with Flask test client: bad token → 404, good token → valid reply.
- Use a temporary SQLite DB, never `rfid.db`.

## 11. Docs to update

`docs/PROJECT_OVERVIEW.md` (architecture diagram, components table), `docs/WHAT_WORKS.md`, `docs/WHAT_TO_ADD.md` (remove the "unauthenticated /ussd" item once done), `README.md`, and add `docs/USSD_SMS_SETUP.md`: how to register the USSD code and sender ID with ThriveVAS, which URLs to paste, how to switch to Africa's Talking.

## 12. Constraints

- Python + Flask + `requests` only; no new heavy dependencies.
- Follow the existing code style (small modules, plain functions, `store` is the only DB layer, background threads via `wallet._async`).
- Don't break current WhatsApp, M-Pesa, or tap behaviour; all new features off unless configured.
- Keep secrets in `.env`; keep `settings.json` free of keys.

## 13. Definition of done

- With `USSD_PROVIDER=none` / `SMS_PROVIDER=none` the app behaves exactly as today.
- Switching `thrivevas` ↔ `africastalking` requires only `.env` changes and a restart.
- A real handset can dial the code and: view card, view payments, pay/top up with confirmation + PIN, get an SMS statement, block a lost card.
- Every confirmed M-Pesa payment sends an SMS receipt (when enabled) and the delivery status shows on the dashboard.
- All tests pass.
