"""M-Pesa STK push (Daraja API). Settings come from mpesa_config.json."""
import base64
import json
import time
from datetime import datetime
from pathlib import Path

import requests

CONFIG = Path(__file__).parent / "mpesa_config.json"
_token = {"value": None, "expires": 0}


def config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _url(cfg, path):
    host = "sandbox.safaricom.co.ke" if cfg.get("environment", "sandbox") == "sandbox" else "api.safaricom.co.ke"
    return f"https://{host}{path}"


def _post(cfg, path, data):
    r = requests.post(_url(cfg, path), json=data, timeout=30,
                      headers={"Authorization": "Bearer " + _get_token(cfg)})
    try:
        return r.json()
    except ValueError:
        return {"errorMessage": f"HTTP {r.status_code}: {r.text[:200]}"}


def _get_token(cfg):
    keys = (cfg.get("environment"), cfg.get("consumer_key"), cfg.get("consumer_secret"))
    if _token["value"] and time.time() < _token["expires"] and _token.get("keys") == keys:
        return _token["value"]
    r = requests.get(_url(cfg, "/oauth/v1/generate?grant_type=client_credentials"),
                     auth=(cfg["consumer_key"], cfg["consumer_secret"]), timeout=30)
    data = r.json() if r.text.strip().startswith("{") else {}
    if "access_token" not in data:
        raise RuntimeError(f"Daraja login failed (HTTP {r.status_code}) - check consumer key/secret")
    _token.update(keys=keys, value=data["access_token"], expires=time.time() + int(data.get("expires_in", 3599)) - 60)
    return _token["value"]


def _password(cfg):
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return base64.b64encode(f"{cfg['shortcode']}{cfg['passkey']}{ts}".encode()).decode(), ts


PENDING_CODES = {"4999", "500.001.1001"}   # "The transaction is still under processing"


def stk_push(phone254, amount, reference="RFID", desc="RFID wallet", callback_url=None):
    """Send the PIN prompt. Returns (True, checkout_id) or (False, error message)."""
    cfg = config()
    pw, ts = _password(cfg)
    r = _post(cfg, "/mpesa/stkpush/v1/processrequest", {
        "BusinessShortCode": cfg["shortcode"],
        "Password": pw,
        "Timestamp": ts,
        "TransactionType": cfg.get("transaction_type", "CustomerPayBillOnline"),
        "Amount": int(amount),
        "PartyA": phone254,
        "PartyB": cfg["shortcode"],
        "PhoneNumber": phone254,
        "CallBackURL": callback_url or cfg.get("callback_url", "https://example.com/mpesa/callback"),
        "AccountReference": reference[:12],
        "TransactionDesc": desc[:13],
    })
    if str(r.get("ResponseCode")) == "0":
        return True, r["CheckoutRequestID"]
    return False, r.get("errorMessage") or r.get("ResponseDescription") or str(r)


def query(checkout_id):
    """One status check. Returns None while still waiting, else (paid, description)."""
    cfg = config()
    pw, ts = _password(cfg)
    try:
        q = _post(cfg, "/mpesa/stkpushquery/v1/query", {
            "BusinessShortCode": cfg["shortcode"], "Password": pw,
            "Timestamp": ts, "CheckoutRequestID": checkout_id,
        })
    except (requests.RequestException, RuntimeError):
        return None
    code = str(q.get("ResultCode", q.get("errorCode", "")))
    if "ResultCode" not in q or code in PENDING_CODES or "under processing" in str(q).lower():
        return None
    return code == "0", q.get("ResultDesc", "")


def wait_for_result(checkout_id, done=lambda: False, tries=36, every=5):
    """Keep checking until the person answers (about 3 minutes).
    Returns (paid, description), or None if done() says the callback already handled it."""
    for _ in range(tries):
        time.sleep(every)
        if done():
            return None
        result = query(checkout_id)
        if result:
            return result
    return False, "No answer from phone"
