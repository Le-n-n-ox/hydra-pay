"""Provider-neutral types used by the SMS and USSD adapters."""
from dataclasses import dataclass, field


@dataclass
class UssdRequest:
    session_id: str
    service_code: str
    phone: str
    text: str
    network: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class UssdReply:
    message: str
    end: bool = False


@dataclass
class SmsResult:
    ok: bool
    message_id: str = ""
    cost: str = ""
    error: str = ""


@dataclass
class DeliveryReport:
    message_id: str
    phone: str
    status: str
    detail: str = ""


@dataclass
class InboundSms:
    phone: str
    text: str
    message_id: str = ""


class SmsProvider:
    name = "none"
    def send(self, phone254, text):
        raise NotImplementedError
    def parse_delivery(self, flask_request):
        return None
    def parse_inbound(self, flask_request):
        return None
    def verify(self, flask_request):
        return True


class UssdProvider:
    name = "none"
    def parse(self, flask_request):
        raise NotImplementedError
    def render(self, reply):
        raise NotImplementedError
    def verify(self, flask_request):
        return True
