"""Africa's Talking SMS and USSD adapters (plain requests, no SDK)."""
import os
from flask import Response, jsonify
import requests
import store
from .base import DeliveryReport, InboundSms, SmsProvider, SmsResult, UssdProvider, UssdRequest


def _env(name, default=""):
    return os.getenv(name, default).strip()


class AfricaTalkingSms(SmsProvider):
    name = "africastalking"

    def _url(self):
        host = "api.sandbox.africastalking.com" if _env("AT_ENV", "sandbox") == "sandbox" else "api.africastalking.com"
        return f"https://{host}/version1/messaging"

    def send(self, phone254, text):
        key, username = _env("AT_API_KEY"), _env("AT_USERNAME")
        if not key or not username:
            return SmsResult(False, error="Africa's Talking credentials are missing")
        data = {"username": username, "to": "+" + store.to_254(phone254), "message": text}
        if _env("AT_SENDER_ID"):
            data["from"] = _env("AT_SENDER_ID")
        try:
            r = requests.post(self._url(), data=data, timeout=20,
                              headers={"apiKey": key, "Accept": "application/json"})
            payload = r.json()
            recipient = (payload.get("SMSMessageData", {}).get("Recipients") or [{}])[0]
            code = int(recipient.get("statusCode", 0) or 0)
            ok = r.ok and code in (100, 101, 102)
            return SmsResult(ok, str(recipient.get("messageId", "")), str(recipient.get("cost", "")),
                             "" if ok else recipient.get("status", r.text[:160]))
        except (requests.RequestException, ValueError) as exc:
            return SmsResult(False, error=str(exc))

    def parse_delivery(self, req):
        f = req.values
        return DeliveryReport(str(f.get("id", "")), store.to_254(f.get("phoneNumber", "")),
                              str(f.get("status", "PENDING")).upper(), str(f.get("failureReason", "")))

    def parse_inbound(self, req):
        f = req.values
        return InboundSms(store.to_254(f.get("from", "")), str(f.get("text", "")), str(f.get("id", "")))


class AfricaTalkingUssd(UssdProvider):
    name = "africastalking"
    def parse(self, req):
        f = req.values
        return UssdRequest(str(f.get("sessionId", "")), str(f.get("serviceCode", "")),
                           store.to_254(f.get("phoneNumber", "")), str(f.get("text", "")),
                           str(f.get("networkCode", "")), dict(f))

    def render(self, reply):
        return Response(("END " if reply.end else "CON ") + reply.message, mimetype="text/plain")
