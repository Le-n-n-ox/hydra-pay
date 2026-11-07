# What still needs to be added or completed

## Required before real-world use

1. **Change the default admin PIN.** `settings.json` currently has `"admin_pin": "1234"`. Remote browser login intentionally remains disabled while this default is set. Use a strong unique PIN and restart the server.
2. **Move real secrets out of the project directory.** `.env`, `mpesa_config.json`, `.flask_secret`, and `rfid.db` can contain credentials or personal/payment data. Keep them out of source control, restrict filesystem access, and rotate any secrets that were shared.
3. **Use live M-Pesa configuration deliberately.** The checked configuration selects the Daraja `sandbox` environment. Production requires approved live credentials, the correct shortcode/transaction type/passkey, and an HTTPS callback endpoint accessible to Safaricom.
4. **Provide a stable public HTTPS endpoint.** ngrok URLs change on restart. For persistent M-Pesa, WhatsApp, and USSD use, deploy behind a stable domain/reverse proxy or a managed tunnel with a reserved address, then update provider webhooks.
5. **Register/configure external services.** Obtain and validate UltraMsg, Gemini, ElevenLabs, Safaricom Daraja, and Africa's Talking credentials only for the features being used. A connector is not proof that the account is approved or operational.
6. **Confirm with real test cards and sandbox/live accounts.** Exercise success, cancelled STK, timeout, duplicate webhook, network loss, serial reconnect, low balance, and card-replacement cases before charging users.

## Security and operational improvements

| Priority | Work to add | Why it matters |
| --- | --- | --- |
| High | Authenticate and verify M-Pesa and UltraMsg callbacks. | The new SMS/USSD callbacks require `TELCO_CALLBACK_TOKEN`; the older `/mpesa/callback` and `/webhook` routes still need provider-specific verification before a public production deployment. |
| High | Put the dashboard behind HTTPS and explicit user authentication for every non-local deployment. | The Flask development server is started directly and loopback is trusted; it is not a hardened production web server. |
| High | Add rate limiting, request-size limits, and audit logging for public routes and admin actions. | Reduces abuse and makes support/investigation possible. |
| High | Create encrypted backups and a retention policy for `rfid.db`. | The database includes phone numbers, card associations, payment activity, and balances. |
| Medium | Add proper user roles (administrator, attendant, viewer) instead of one shared PIN. | Supports accountability and least-privilege access. |
| Medium | Expand automated coverage for database updates, tap state changes, payment state transitions, and callback idempotency. | The SMS/USSD regression suite exists, but core payment and reader edge cases still need coverage. |
| Medium | Add structured logs, health checks, monitoring, and restart supervision. | Makes serial/device/API failures observable and recoverable. |
| Medium | Pin dependencies in `requirements.txt` or a lock file and add a repeatable deployment script. | Prevents different installations from silently receiving incompatible package versions. |
| Medium | Run with a production WSGI server and service manager. | Flask's built-in server is intended for development, not resilient production hosting. |
| Medium | Decide whether payment polling, callback, or both is authoritative, then document reconciliation. | This lowers the risk of edge-case discrepancies when external confirmation is delayed. |
| Low | Add data validation at all boundaries and clearer end-user error states. | Examples: phone verification, UID format validation, service status details, and clear offline indicators. |

## Product decisions still needed

- Decide whether the intended commercial flow is **prompt mode** (pay every entry) or **wallet mode** (prepay and deduct balance). The current default is prompt mode, while parts of the interface/database support wallet mode.
- Decide the policy for duplicate/tailgating taps, card loss, refund approval, disputed payments, and failed payment after entry state was recorded.
- Define who may modify a phone number. The WhatsApp bot currently lets a person messaging from the existing linked number change it; recovery for lost phone access needs an admin process.
- Define privacy notices, consent, user support, and data retention/deletion procedures for phone, payment, and RFID data.

## Documentation and project cleanup

- Update the root `README.md`: it refers to `start_dashboard.bat`, but the project contains `start.bat`.
- Update the root README's claim that scans are saved to `rfid_log.csv` and that card names are maintained in `names.json`. Current runtime data is in `rfid.db`; those legacy files are only migration inputs.
- Add a `requirements.txt` generated from the supported dependency set, a `.gitignore` for secrets/data/cache/`.venv`, and `.env.example`/`mpesa_config.example.json` files with placeholders.
- Correct the visibly mis-decoded emoji/text in source and README files by saving the files consistently as UTF-8.
- Choose one supported firmware path (MicroPython or Arduino) and provide a repeatable flash/verification guide for it.
