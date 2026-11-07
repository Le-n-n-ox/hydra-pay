"""ThriveVAS SMS adapter and configurable USSD mapper.

ThriveVAS has public SMS documentation but not a fixed public USSD wire format.
The mapper defaults to Africa's Talking style and can be changed through .env.
"""
import base64
import os
import time
from flask import Response, jsonify
import requests
import store
from .base import DeliveryReport, InboundSms, SmsProvider, SmsResult, UssdProvider, UssdRequest


def _env(name, default=""):
    return os.getenv(name, default).strip()


class ThriveVasSms(SmsProvider):
    name = "thrivevas"
    _token = ""
    _expires = 0

    def _key(self, force=False):
        fixed = _env("THRIVEVAS_API_KEY")
        if fixed:
            return fixed
        if self._token and not force and time.time() < self._expires - 60:
            return self._token
        msisdn, password = _env("THRIVEVAS_MSISDN"), _env("THRIVEVAS_PASSWORD")
        if not msisdn or not password:
            return ""
        body = {"name": "hydra-pay", "lifetime_seconds": int(_env("THRIVEVAS_KEY_LIFETIME", "86400"))}
        url = _env("THRIVEVAS_IDENTITY_URL", "https://identity.thrivevas.com/v1/auth/api-key/generate")
        # HTTPBasicAuth is attempted first. Some deployments document base64url;
        # retry with URL-safe encoding only when normal Basic auth is rejected.
        r = requests.post(url, json=body, auth=requests.auth.HTTPBasicAuth(msisdn, password), timeout=20)
        if r.status_code == 401:
            encoded = base64.urlsafe_b64encode(f"{msisdn}:{password}".encode()).decode()
            r = requests.post(url, json=body, headers={"Authorization": "Basic " + encoded}, timeout=20)
        data = r.json() if r.content else {}
        token = data.get("token", "")
        if not r.ok or not token:
            return ""
        self._token = token
        self._expires = time.time() + body["lifetime_seconds"]
        return token

    def send(self, phone254, text):
        def attempt(refresh=False):
            token = self._key(refresh)
            if not token:
                return None, SmsResult(False, error="ThriveVAS credentials are missing or key generation failed")
            payload = {"message": text, "msisdn": "+" + store.to_254(phone254),
                       "sender_id": _env("THRIVEVAS_SENDER_ID", "ThriveVas"), "country_code": "ke"}
            base = _env("TELCO_CALLBACK_BASE_URL").rstrip("/")
            callback_token = _env("TELCO_CALLBACK_TOKEN")
            if base and callback_token:
                payload["callback_url"] = f"{base}/sms/delivery/{callback_token}"
            try:
                r = requests.post(_env("THRIVEVAS_SMS_URL", "https://sms.thrivevas.com/v1/message/send"),
                                  json=payload, headers={"x-api-key": token}, timeout=20)
                data = r.json() if r.content else {}
                if r.status_code in (401, 428):
                    return r.status_code, SmsResult(False, error=data.get("message", "expired key"))
                ok = r.ok and int(data.get("status", 0) or 0) == 200
                return r.status_code, SmsResult(ok, str(data.get("transaction_id", "")), "",
                                                "" if ok else str(data.get("message", r.text[:160])))
            except (requests.RequestException, ValueError) as exc:
                return 0, SmsResult(False, error=str(exc))
        code, result = attempt()
        return attempt(True)[1] if code in (401, 428) and not _env("THRIVEVAS_API_KEY") else result

    def parse_delivery(self, req):
        data = req.get_json(silent=True) or req.values
        status = {0: "FAILED_BILLING", 1: "FAILED", 2: "PENDING", 3: "DELIVERED"}.get(
            int(data.get("status", 2)), "PENDING")
        return DeliveryReport(str(data.get("transaction_id", "")), store.to_254(data.get("msisdn", "")), status,
                              str(data.get("status_description", "")))

    def parse_inbound(self, req):
        data = req.get_json(silent=True) or req.values
        return InboundSms(store.to_254(data.get("msisdn", data.get("from", ""))), str(data.get("text", "")),
                          str(data.get("id", "")))


class ThriveVasUssd(UssdProvider):
    name = "thrivevas"
    def _field(self, name, default):
        return _env("THRIVEVAS_USSD_FIELD_" + name, default)
    def parse(self, req):
        raw = req.get_json(silent=True) or req.values
        sid = str(raw.get(self._field("SESSION", "sessionId"), ""))
        text = str(raw.get(self._field("TEXT", "text"), ""))
        if _env("THRIVEVAS_USSD_INPUT", "cumulative") == "latest":
            text = store.append_ussd_step(sid, text)
        return UssdRequest(sid, str(raw.get(self._field("CODE", "serviceCode"), "")),
                           store.to_254(raw.get(self._field("PHONE", "phoneNumber"), "")), text,
                           str(raw.get("networkCode", raw.get("network", ""))), dict(raw))
    def render(self, reply):
        if _env("THRIVEVAS_USSD_REPLY", "prefix") == "json":
            return jsonify({"message": reply.message, "end": reply.end})
        return Response(("END " if reply.end else "CON ") + reply.message, mimetype="text/plain")
