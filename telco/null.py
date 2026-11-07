from flask import Response
from .base import SmsProvider, SmsResult, UssdProvider, UssdReply


class NullSms(SmsProvider):
    name = "none"
    def send(self, phone254, text):
        return SmsResult(False, error="SMS provider is disabled")


class NullUssd(UssdProvider):
    name = "none"
    def render(self, reply):
        return Response("END USSD is unavailable.", mimetype="text/plain")
    def parse(self, flask_request):
        raise RuntimeError("USSD provider is disabled")
