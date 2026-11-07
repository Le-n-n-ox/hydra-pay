import os

import pytest

import sms
import store
import telco
import ussd
import wallet
from telco.base import SmsProvider, SmsResult, UssdRequest


@pytest.fixture(autouse=True)
def temporary_store(tmp_path, monkeypatch):
    store.use_database(tmp_path / "test.db")
    store.init(10)
    monkeypatch.setattr(wallet, "settings", lambda: {
        "business_name": "Hydra Pay", "mode": "wallet", "min_topup": 1, "max_topup": 10000,
        "ussd_pin_required": True, "ussd_max_prompts_per_hour": 5, "ussd_language_default": "en",
    })
    monkeypatch.setenv("SMS_PROVIDER", "none")
    monkeypatch.setenv("USSD_PROVIDER", "none")


def request(session, phone, text):
    return UssdRequest(session, "*123#", phone, text)


def test_ussd_card_path_sets_pin_and_fits_screen():
    store.save_card("AA", "Jane Long Name", "0712345678", 20)
    first = ussd.handle(request("s1", "254712345678", ""))
    assert "My card" in first.message and not first.end
    pin1 = ussd.handle(request("s1", "254712345678", "1"))
    assert "Set a new" in pin1.message
    pin2 = ussd.handle(request("s1", "254712345678", "1*2468"))
    assert "Confirm" in pin2.message
    card = ussd.handle(request("s1", "254712345678", "1*2468*2468"))
    assert "Price" in card.message
    assert len(card.message) <= 160


def test_ussd_multiple_cards_and_navigation():
    store.save_card("AA", "Jane", "0712345678", 20)
    store.save_card("BB", "Tom", "0712345678", 20)
    menu = ussd.handle(request("s2", "254712345678", ""))
    assert "Choose card" in menu.message
    main = ussd.handle(request("s2", "254712345678", "2"))
    assert "Hydra Pay - Tom" in main.message
    again = ussd.handle(request("s2", "254712345678", "2*00"))
    assert "Choose card" in again.message


def test_unregistered_menu_is_safe():
    reply = ussd.handle(request("s3", "254700000000", ""))
    assert "no card" in reply.message.lower()
    assert "254700000000" not in reply.message


class FakeSms(SmsProvider):
    name = "fake"
    def __init__(self): self.sent = []
    def send(self, phone, text):
        self.sent.append((phone, text))
        return SmsResult(True, "message-1", "KES 0.70")


def test_sms_logs_and_strips_emoji(monkeypatch):
    provider = FakeSms()
    monkeypatch.setattr(telco, "get_sms", lambda: provider)
    row = sms.send("0712345678", "Hydra 💳 *Pay* received", "payment", background=False)
    assert provider.sent == [("254712345678", "Hydra Pay received")]
    logged = store.recent_sms(1)[0]
    assert logged["status"] == "SENT" and logged["message_id"] == "message-1"


def test_africastalking_adapter_parse_and_render(monkeypatch):
    from flask import Flask
    from telco.africastalking import AfricaTalkingUssd
    app = Flask(__name__)
    with app.test_request_context("/", method="POST", data={"sessionId":"x", "serviceCode":"*1#", "phoneNumber":"0712345678", "text":"1", "networkCode":"63902"}):
        provider = AfricaTalkingUssd()
        parsed = provider.parse(__import__("flask").request)
        response = provider.render(ussd.UssdReply("Hello", False))
    assert parsed.phone == "254712345678" and parsed.text == "1"
    assert response.get_data(as_text=True) == "CON Hello"


def test_thrivevas_delivery_report_without_content_type(monkeypatch):
    """ThriveVAS posts JSON with no Content-Type; reports can arrive as PENDING after DELIVERED."""
    from flask import Flask
    from telco.thrivevas import ThriveVasSms

    monkeypatch.setattr(telco, "get_sms", lambda: ThriveVasSms())
    store.add_sms("0712345678", "payment", "Receipt", "thrivevas", status="SENT", message_id="30840")
    app = Flask(__name__)

    def report(status, description):
        body = '{"transaction_id":30840,"msisdn":"+254712345678","status":%d,"description":"%s"}' % (status, description)
        with app.test_request_context("/sms/delivery/x", method="POST", data=body):
            from flask import request as req
            assert sms.delivery(req)
        return store.recent_sms(1)[0]

    assert report(3, "DeliveredToTerminal")["status"] == "DELIVERED"
    assert report(2, "SUCCESS")["status"] == "DELIVERED"          # late pending must not undo delivered
    store.add_sms("0712345678", "payment", "Receipt", "thrivevas", status="SENT", message_id="30841")
    body = '{"transaction_id":30841,"msisdn":"+254712345678","status":0,"description":"Insufficient credit"}'
    with app.test_request_context("/sms/delivery/x", method="POST", data=body):
        from flask import request as req
        sms.delivery(req)
    row = store.recent_sms(1)[0]
    assert row["status"] == "FAILED_BILLING" and row["error"] == "Insufficient credit"
