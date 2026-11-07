# SMS and USSD setup

Hydra Pay has switchable SMS and USSD providers. No credentials are enabled by default, so the existing RFID, M-Pesa, and WhatsApp behaviour remains available while SMS and USSD callbacks are off.

## 1. Configure `.env`

Copy the relevant entries from [`.env.example`](../.env.example) into the existing `.env`. Never commit or share the real `.env`.

Choose the providers independently:

```dotenv
USSD_PROVIDER=thrivevas       # thrivevas | africastalking | none
SMS_PROVIDER=thrivevas        # thrivevas | africastalking | none
TELCO_CALLBACK_TOKEN=use-a-long-random-secret
```

`none` disables that channel. For example, `USSD_PROVIDER=africastalking` and `SMS_PROVIDER=thrivevas` is supported.

## ThriveVAS

For outbound SMS, configure either a pre-generated API key or account credentials. With account credentials, Hydra Pay requests and refreshes a short-lived key in memory; it never writes the password or generated token to SQLite or logs.

```dotenv
THRIVEVAS_API_KEY=
# Or use both of these instead:
THRIVEVAS_MSISDN=2547XXXXXXXX
THRIVEVAS_PASSWORD=
THRIVEVAS_SENDER_ID=ThriveVas
```

ThriveVAS has not published a fixed USSD callback wire format. Its adapter is configurable through the `THRIVEVAS_USSD_*` variables in `.env.example`, defaulting to the common `sessionId`, `phoneNumber`, `text`, `serviceCode`, and `CON`/`END` format. Confirm the actual field/reply format with ThriveVAS before enabling its USSD service. If needed, run ThriveVAS for SMS and Africa's Talking for USSD.

## Africa's Talking

```dotenv
AT_USERNAME=sandbox
AT_API_KEY=your-api-key
AT_SENDER_ID=
AT_ENV=sandbox
```

Set `AT_ENV=live` only when you have a live application username/key and a registered sender ID or shortcode. Africa's Talking's sandbox username is `sandbox`.

## 2. Configure non-secret options

In the dashboard's **SMS & USSD** panel, set the USSD code and optional admin SMS number. The equivalent non-secret options live in `settings.json`:

- `sms_receipts`: SMS after confirmed M-Pesa payment.
- `sms_when_whatsapp_fails`: fall back to SMS if UltraMsg cannot send.
- `sms_low_balance`: SMS a low-balance warning in wallet mode.
- `ussd_pin_required`: require a customer PIN before personal/payment actions.
- `ussd_max_prompts_per_hour`: per-phone limit for M-Pesa prompts requested over USSD.
- `admin_daily_summary_time`: optional `HH:MM` local-time SMS summary; leave blank to disable it.

## 3. Publish the callbacks

Start ngrok and the dashboard, then open the **SMS & USSD** panel. It displays the exact URLs when `TELCO_CALLBACK_TOKEN` is configured:

```text
https://YOUR-NGROK-HOST/ussd/YOUR_TOKEN
https://YOUR-NGROK-HOST/sms/delivery/YOUR_TOKEN
https://YOUR-NGROK-HOST/sms/inbound/YOUR_TOKEN
```

Paste the first URL as the provider's USSD callback. Configure the delivery and inbound URLs only if the chosen SMS product supports them. The token is mandatory: a missing or incorrect token produces `404` and the callback cannot access card data.

## 4. Test safely

1. Use the on-dashboard USSD simulator before configuring a service code.
2. Use **Send test SMS** with your own approved test number.
3. Use a provider sandbox where available. ThriveVAS documentation does not describe a sandbox, so test its live channel only with your own number and a small credit balance.
4. Test PIN setup, incorrect PIN lockout, payment cancellation, card blocking, and delivery reports before opening the service to customers.

Run the automated checks with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp
```

## What the implementation does

- Records every outbound SMS in `sms_log` and updates it from delivery reports.
- Handles `BAL`, `STMT`, `HELP`, `STOP`, and `START` inbound SMS keywords when the provider supplies two-way callbacks.
- Stores only a salted `scrypt` hash for USSD PINs, locks after three failed attempts for 30 minutes, and keeps USSD session state in SQLite.
- Supports multiple cards per telephone number, English/Kiswahili choice, `0` back, `00` home, PIN-gated payment/card actions, card blocking, and M-Pesa confirmation.
