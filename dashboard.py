"""RFID wallet dashboard.

- Reads card taps from the ESP32 over USB (lines "UID:XX XX XX XX")
- Wallet per card: tap IN costs the card's price, tap OUT is free
- Top up with M-Pesa (STK push) or cash, undo, daily totals, CSV export
- WhatsApp bot + receipts (UltraMsg, Gemini, ElevenLabs) on /webhook
- Open on this laptop:  http://localhost:8000
  on your phone (same WiFi): http://<laptop-ip>:8000   from anywhere: the ngrok link

Usage:  python dashboard.py          (auto-detects the ESP32 port)
        python dashboard.py COM6     (force a port)
"""
import secrets
import os
import re
import socket
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import serial
from flask import Flask, Response, jsonify, redirect, request, send_from_directory, session
from serial.tools import list_ports

import bot
import mpesa
import sms
import store
import telco
import ussd
import wallet
import whatsapp

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
BAUD = 115200
HTTP_PORT = 8000

esp = {"port": None, "connected": False, "message": "Searching for ESP32..."}
last_unknown = {"uid": None, "time": 0}

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
secret_file = HERE / ".flask_secret"
if not secret_file.exists():
    secret_file.write_text(secrets.token_hex(32))
app.secret_key = secret_file.read_text().strip()


# ---------- ESP32 serial ----------

def find_port():
    forced = [a for a in sys.argv[1:] if not a.startswith("--")]
    if forced:
        return forced[0]
    ports = list_ports.comports()
    keys = ("cp210", "ch340", "ch910", "wch", "silicon labs", "usb serial", "usb-serial", "uart")
    for p in ports:
        if any(k in f"{p.description} {p.manufacturer or ''}".lower() for k in keys):
            return p.device
    return None


def serial_loop():
    while True:
        port = find_port()
        if not port:
            esp.update(port=None, connected=False, message="No ESP32 found - plug it in via USB")
            time.sleep(2)
            continue
        try:
            with serial.Serial(port, BAUD, timeout=1) as s:
                esp.update(port=port, connected=True, message=f"Connected on {port}")
                print(f"Connected to ESP32 on {port}")
                while True:
                    line = s.readline().decode(errors="ignore").strip()
                    if line.startswith("UID:"):
                        uid = line[4:].strip().upper()
                        try:
                            ev = wallet.on_tap(uid)
                            if not ev["card"]:
                                last_unknown.update(uid=uid, time=time.time())
                        except Exception as e:
                            print(f"[TAP] error: {e}")
                    elif line:
                        print(f"[ESP32] {line}")
                        if line.startswith(("READY", "ERROR")):
                            esp["message"] = f"{port}: {line}"
        except serial.SerialException as e:
            esp.update(connected=False, message=f"Can't use {port} (close Arduino Serial Monitor?)")
            print(f"Serial problem on {port}: {e} - retrying...")
            time.sleep(2)


# ---------- login ----------

def is_local():
    forwarded = request.headers.get("X-Forwarded-For") or request.headers.get("X-Forwarded-Host")
    return request.remote_addr in ("127.0.0.1", "::1") and not forwarded


def logged_in():
    return is_local() or session.get("ok")


def pin_ok(pin):
    return secrets.compare_digest(str(pin or ""), str(wallet.settings().get("admin_pin", "1234")))


LOGIN_PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login</title><style>body{font-family:Segoe UI,sans-serif;background:#111827;color:#e5e7eb;display:grid;place-items:center;height:100vh;margin:0}
form{background:#1f2937;padding:28px;border-radius:12px;display:grid;gap:12px;min-width:260px}
input,button{padding:12px;border-radius:8px;border:0;font-size:16px}button{background:#2563eb;color:#fff;cursor:pointer}
.err{color:#f87171}</style></head><body><form method="post"><h2>🔒 RFID Wallet</h2>%s
<input type="password" name="pin" placeholder="Admin PIN" inputmode="numeric" autofocus><button>Open dashboard</button></form></body></html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if str(wallet.settings().get("admin_pin", "1234")) == "1234":
        return LOGIN_PAGE % ('<div class="err">Remote login is off until you change "admin_pin" in settings.json '
                             '(it is still 1234). Then restart the dashboard.</div>')
    if request.method == "POST":
        if pin_ok(request.form.get("pin")):
            session["ok"] = True
            return redirect("/")
        time.sleep(1)
        return LOGIN_PAGE % '<div class="err">Wrong PIN</div>'
    return LOGIN_PAGE % ""


@app.before_request
def require_login():
    if request.path == "/ussd":
        return ("", 404)
    open_paths = ("/login", "/webhook", "/voice/", "/mpesa/callback", "/ussd/", "/sms/")
    if not logged_in() and not request.path.startswith(open_paths):
        if request.path.startswith("/api/"):
            return jsonify(error="login required"), 401
        return redirect("/login")


# ---------- pages ----------

def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


@app.route("/")
def index():
    return send_from_directory(HERE / "static", "index.html")


@app.route("/api/data")
def data():
    day = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    cards = store.list_cards()
    unknown = last_unknown["uid"] if (last_unknown["uid"] and time.time() - last_unknown["time"] < 600
                                      and not store.get_card(last_unknown["uid"])) else None
    return jsonify({
        "esp": esp,
        "services": {**whatsapp.status(), "sms": sms.enabled(), "sms_provider": telco.get_sms().name,
                     "ussd_provider": telco.get_ussd().name},
        "lan_url": f"http://{lan_ip()}:{HTTP_PORT}",
        "public_url": whatsapp.public_url(),
        "cards": cards,
        "inside": [c for c in cards if c["status"] == "IN"],
        "new_card": unknown,
        "scans": store.recent_scans(100),
        "transactions": [dict(t, ref=store.receipt_ref(t["id"]), label=store.KIND_LABELS.get(t["kind"], t["kind"]))
                         for t in store.recent_transactions(limit=100)],
        "payments": store.recent_payments(30),
        "summary": store.daily_summary(day),
        "default_price": wallet.settings().get("default_price", 1),
        "mode": "prompt" if wallet.prompt_mode() else "wallet",
    })


def body():
    return request.get_json(force=True, silent=True) or {}


def amount_of(b):
    try:
        return int(float(b.get("amount", 0)))
    except (TypeError, ValueError):
        return 0


@app.route("/api/cards", methods=["POST"])
def save_card():
    b = body()
    if not pin_ok(b.get("pin")):
        return jsonify(error="Wrong admin PIN"), 403
    uid = str(b.get("uid", "")).strip().upper()
    name = str(b.get("name", "")).strip()
    if not uid or not name:
        return jsonify(error="UID and name are required"), 400
    try:
        price = max(0, int(float(b.get("price", wallet.settings().get("default_price", 1)))))
    except (TypeError, ValueError):
        return jsonify(error="Price must be a number"), 400
    card = store.save_card(uid, name, str(b.get("phone", "")).strip(), price)
    if last_unknown["uid"] == uid:
        last_unknown["uid"] = None
    print(f"  Card saved: {name} ({uid}) phone {card['phone']} price KSh {price}")
    return jsonify(ok=True, message=f"Saved {name}")


@app.route("/api/cards/move", methods=["POST"])
def move_card():
    b = body()
    if not pin_ok(b.get("pin")):
        return jsonify(error="Wrong admin PIN"), 403
    old_uid = str(b.get("old_uid", "")).strip().upper()
    new_uid = str(b.get("new_uid", "")).strip().upper()
    card = store.move_card(old_uid, new_uid)
    if not card:
        return jsonify(error="Can't move: pick a registered person and an unregistered new card"), 400
    if last_unknown["uid"] == new_uid:
        last_unknown["uid"] = None
    print(f"  Card replaced: {card['name']} moved from {old_uid} to {new_uid}")
    return jsonify(ok=True, message=f"{card['name']} now uses card {new_uid}")


@app.route("/api/cards/block", methods=["POST"])
def block_card():
    b = body()
    if not pin_ok(b.get("pin")):
        return jsonify(error="Wrong admin PIN"), 403
    card = store.set_card_blocked(str(b.get("uid", "")).strip().upper(), bool(b.get("blocked", True)))
    if not card:
        return jsonify(error="Card not found"), 404
    return jsonify(ok=True, message=f"{card['name']} {'blocked' if card['blocked'] else 'unblocked'}")


@app.route("/api/topup/mpesa", methods=["POST"])
def topup_mpesa():
    b = body()
    ok, msg = wallet.start_mpesa_topup(b.get("uid"), amount_of(b), source="dashboard")
    return (jsonify(ok=True, message=msg) if ok else (jsonify(error=msg), 400))


@app.route("/api/topup/cash", methods=["POST"])
def topup_cash():
    b = body()
    if not pin_ok(b.get("pin")):
        return jsonify(error="Wrong admin PIN"), 403
    tx, msg = wallet.cash_topup(b.get("uid"), amount_of(b))
    return (jsonify(ok=True, message=msg) if tx else (jsonify(error=msg), 400))


@app.route("/api/undo/<int:tx_id>", methods=["POST"])
def undo(tx_id):
    if not pin_ok(body().get("pin")):
        return jsonify(error="Wrong admin PIN"), 403
    tx, msg = wallet.undo(tx_id)
    return (jsonify(ok=True, message=msg) if tx else (jsonify(error=msg), 400))


@app.route("/api/export")
def export():
    what = request.args.get("what", "transactions")
    if what not in ("transactions", "scans", "summary", "payments"):
        what = "transactions"
    day = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    return Response(store.export_csv(what, day), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={what}_{day}.csv"})


# ---------- M-Pesa callback (gives the M-Pesa receipt code) ----------

@app.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    try:
        cb = (request.get_json(force=True, silent=True) or {}).get("Body", {}).get("stkCallback", {})
        pay = store.payment_by_checkout(cb.get("CheckoutRequestID", ""))
        if pay:
            items = {i.get("Name"): i.get("Value") for i in cb.get("CallbackMetadata", {}).get("Item", [])}
            code = str(items.get("MpesaReceiptNumber", "") or "")
            # don't trust the callback alone: confirm with Safaricom before marking paid
            threading.Thread(target=_confirm_callback, args=(pay["id"], pay["checkout_id"], code), daemon=True).start()
    except Exception as e:
        print(f"[M-Pesa callback] error: {e}")
    return jsonify(ResultCode=0, ResultDesc="Accepted")


def _confirm_callback(pid, checkout_id, code):
    result = mpesa.query(checkout_id)
    if result:
        wallet.finish_payment(pid, *result, mpesa_receipt=code if result[0] else "")
    elif code:
        store.update_payment(pid, mpesa_receipt=code)


# ---------- provider-neutral SMS / USSD ----------

def _telco_allowed(token):
    expected = os.getenv("TELCO_CALLBACK_TOKEN", "")
    if not expected or not secrets.compare_digest(str(token or ""), expected):
        return False
    allowed = {ip.strip() for ip in os.getenv("TELCO_ALLOWED_IPS", "").split(",") if ip.strip()}
    if not allowed:
        return True
    remote = request.remote_addr or ""
    # ngrok is the one trusted proxy this launcher configures; do not trust an arbitrary XFF header.
    if request.headers.get("X-Forwarded-Host"):
        remote = (request.headers.get("X-Forwarded-For", remote).split(",")[0].strip())
    return remote in allowed


def _masked(phone):
    phone = str(phone or "")
    return "***" + phone[-3:] if phone else ""


@app.route("/ussd/<token>", methods=["POST"])
def ussd_route(token):
    provider = telco.get_ussd()
    if provider.name == "none" or not _telco_allowed(token) or not provider.verify(request):
        return ("", 404)
    try:
        ussd_request = provider.parse(request)
        if os.getenv("TELCO_DEBUG", "0") == "1":
            print(f"[USSD {provider.name}] phone={_masked(ussd_request.phone)} session={ussd_request.session_id}")
        reply = ussd.handle(ussd_request)
        return provider.render(reply)
    except Exception as exc:
        print(f"[USSD] error: {exc}")
        return provider.render(ussd.UssdReply("Sorry, try again later.", True))


@app.route("/sms/delivery/<token>", methods=["POST"])
def sms_delivery(token):
    provider = telco.get_sms()
    if provider.name == "none" or not _telco_allowed(token) or not provider.verify(request):
        return ("", 404)
    sms.delivery(request)
    return Response("OK", mimetype="text/plain")


@app.route("/sms/inbound/<token>", methods=["POST"])
def sms_inbound(token):
    provider = telco.get_sms()
    if provider.name == "none" or not _telco_allowed(token) or not provider.verify(request):
        return ("", 404)
    reply = sms.inbound(request)
    inbound = provider.parse_inbound(request)
    if reply and inbound and inbound.phone:
        sms.send(inbound.phone, reply, "inbound")
    return Response("OK", mimetype="text/plain")


@app.route("/api/telco/status")
def telco_status():
    base = whatsapp.public_url().rstrip("/")
    token = os.getenv("TELCO_CALLBACK_TOKEN", "")
    urls = {} if not (base and token) else {
        "ussd": f"{base}/ussd/{token}", "delivery": f"{base}/sms/delivery/{token}",
        "inbound": f"{base}/sms/inbound/{token}",
    }
    return jsonify(sms_provider=telco.get_sms().name, ussd_provider=telco.get_ussd().name,
                   ussd_code=wallet.settings().get("ussd_code", ""), callbacks=urls,
                   sms=store.recent_sms(20), sessions=store.recent_ussd_sessions(20),
                   settings={k: wallet.settings().get(k) for k in ("ussd_code", "admin_phone", "sms_receipts",
                             "sms_when_whatsapp_fails", "sms_low_balance", "ussd_pin_required")})


@app.route("/api/sms/test", methods=["POST"])
def sms_test():
    b = body()
    if not pin_ok(b.get("pin")):
        return jsonify(error="Wrong admin PIN"), 403
    phone = store.to_254(b.get("phone", ""))
    if not phone:
        return jsonify(error="Enter a phone number"), 400
    row = sms.send(phone, b.get("text") or "Hydra Pay SMS test.", "test")
    return jsonify(ok=bool(row), message="SMS queued" if row else "SMS is disabled or number is invalid")


@app.route("/api/ussd/simulate", methods=["POST"])
def ussd_simulate():
    from telco.base import UssdRequest
    b = body()
    phone = store.to_254(b.get("phone", ""))
    if not phone:
        return jsonify(error="Enter a phone number"), 400
    req = UssdRequest(str(b.get("session_id") or f"sim-{phone}"), str(b.get("service_code") or "SIM"),
                      phone, str(b.get("text", "")))
    reply = ussd.handle(req)
    return jsonify(message=reply.message, end=reply.end)


@app.route("/api/telco/settings", methods=["POST"])
def telco_settings():
    b = body()
    if not pin_ok(b.get("pin")):
        return jsonify(error="Wrong admin PIN"), 403
    saved = wallet.update_settings(b)
    return jsonify(ok=True, settings={k: saved.get(k) for k in b if k != "pin"})


# ---------- WhatsApp ----------

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        bot.handle(request.get_json(force=True, silent=True) or {})
    except Exception as e:
        print(f"[WEBHOOK] error: {e}")
    return jsonify(status="ok")


@app.route("/voice/<name>")
def voice(name):
    if not name.endswith(".mp3") or "/" in name or "\\" in name or ".." in name:
        return ("", 404)
    return send_from_directory(whatsapp.VOICE_DIR, name, mimetype="audio/mpeg")


def connect_whatsapp():
    st = whatsapp.status()
    if not st["whatsapp"]:
        print("WhatsApp: no UltraMsg keys in .env - WhatsApp bot and receipts are off")
        return
    print(f"WhatsApp: on | AI (Gemini): {'on' if st['gemini'] else 'off'} | voice notes (ElevenLabs): "
          f"{'on' if st['voice'] else 'off'}")
    if not wallet.settings().get("auto_set_webhook", True):
        return
    for _ in range(15):
        url = whatsapp.public_url()
        if url:
            ok, info = whatsapp.set_webhook(url + "/webhook")
            print(f"WhatsApp webhook -> {url}/webhook : {'set' if ok else 'FAILED ' + info}")
            print(f"Dashboard from anywhere: {url}")
            return
        time.sleep(2)
    print("WhatsApp: ngrok is not running, so incoming WhatsApp messages won't reach the bot "
          "(receipts still go out). Start it with: ngrok http 8000")


def connect_telco():
    sms_provider, ussd_provider = telco.get_sms(), telco.get_ussd()
    print(f"Telco: SMS={sms_provider.name} | USSD={ussd_provider.name}")
    if sms_provider.name == "none" and ussd_provider.name == "none":
        return
    token = os.getenv("TELCO_CALLBACK_TOKEN", "")
    if not token:
        print("Telco: TELCO_CALLBACK_TOKEN is missing; public telco callbacks are disabled")
        return
    base = whatsapp.public_url()
    if not base:
        print("Telco: start ngrok or set TELCO_CALLBACK_BASE_URL, then configure the provider callbacks")
        return
    print(f"USSD callback: {base}/ussd/{token}")
    print(f"SMS delivery: {base}/sms/delivery/{token}")
    print(f"SMS inbound: {base}/sms/inbound/{token}")


def daily_sms_summary_loop():
    """Optional once-a-day admin summary; disabled until a HH:MM time is set."""
    sent_day = ""
    while True:
        setting = str(wallet.settings().get("admin_daily_summary_time", "")).strip()
        current = datetime.now()
        if re.fullmatch(r"\d{2}:\d{2}", setting) and current.strftime("%H:%M") == setting and sent_day != current.strftime("%Y-%m-%d"):
            summary = store.daily_summary(sent_day or current.strftime("%Y-%m-%d"))
            sms.send_admin(f"Hydra Pay daily: M-Pesa KSh {summary['mpesa']}, taps {summary['taps']}, denied {summary['denied']}.", "daily_summary")
            sent_day = current.strftime("%Y-%m-%d")
        time.sleep(20)


if __name__ == "__main__":
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)   # hide the per-request log lines
    store.init(wallet.settings().get("default_price", 1))
    threading.Thread(target=serial_loop, daemon=True).start()
    threading.Thread(target=connect_whatsapp, daemon=True).start()
    threading.Thread(target=connect_telco, daemon=True).start()
    threading.Thread(target=daily_sms_summary_loop, daemon=True).start()
    threading.Thread(target=wallet.recheck_stuck, daemon=True).start()
    print(f"Dashboard: http://localhost:{HTTP_PORT}   phone on same WiFi: http://{lan_ip()}:{HTTP_PORT}")
    if "--no-browser" not in sys.argv:
        import webbrowser
        webbrowser.open(f"http://localhost:{HTTP_PORT}")
    app.run(host="0.0.0.0", port=HTTP_PORT, threaded=True)
