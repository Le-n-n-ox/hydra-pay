"""Transactional SMS, delivery reporting, inbound keywords, and retry handling."""
import re
import threading
import time

import store
import telco


GSM = set("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ !\"#¤%&'()*+,-./0123456789:;<=>?" +
          "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§abcdefghijklmnopqrstuvwxyzäöñüà")


def plain(text, limit=160):
    """One affordable GSM-7 SMS segment; remove markup, emoji and non-GSM text."""
    text = re.sub(r"[*_]", "", str(text or ""))
    text = "".join(c for c in text if c in GSM)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def enabled():
    return telco.get_sms().name != "none"


def send(phone, text, kind="notice", transactional=True, background=True):
    """Queue a logged SMS. Network failures retry twice; provider rejection does not."""
    phone, message, provider = store.to_254(phone), plain(text), telco.get_sms()
    user = store.get_ussd_user(phone)
    if provider.name == "none" or not phone or not message:
        return None
    if user and user.get("sms_opt_out") and not transactional:
        return store.add_sms(phone, kind, message, provider.name, "OPTED_OUT")
    row = store.add_sms(phone, kind, message, provider.name)

    def work():
        result = None
        for attempt in range(3):
            result = provider.send(phone, message)
            if result.ok or not result.error:
                break
            # Only network/temporary failures retry. Provider 4xx errors return a message and stop.
            if any(word in result.error.lower() for word in ("missing", "invalid", "forbidden", "rejected", "disabled")):
                break
            if attempt < 2:
                time.sleep(2 ** attempt)
        if result and result.ok:
            store.update_sms(row["id"], status="SENT", message_id=result.message_id, cost=result.cost, error="")
        else:
            store.update_sms(row["id"], status="FAILED", error=(result.error if result else "send failed"))

    if background:
        threading.Thread(target=work, daemon=True).start()
    else:
        work()
    return row


def delivery(req):
    report = telco.get_sms().parse_delivery(req)
    if not report:
        return False
    return store.update_sms_delivery(report.message_id, report.phone, report.status, report.detail)


def inbound(req):
    message = telco.get_sms().parse_inbound(req)
    if not message or not message.phone:
        return ""
    word = message.text.strip().upper()
    if word == "STOP":
        store.save_ussd_user(message.phone, sms_opt_out=1)
        return "Hydra Pay: SMS alerts stopped. Reply START to resume."
    if word == "START":
        store.save_ussd_user(message.phone, sms_opt_out=0)
        return "Hydra Pay: SMS alerts resumed."
    cards = store.cards_for_phone(message.phone)
    if word == "HELP":
        return "Hydra Pay: BAL for card status, STMT for recent payments, STOP to opt out."
    if not cards:
        return "Hydra Pay: this number has no linked card. Visit the desk for help."
    card = cards[0]
    if word == "BAL":
        if card.get("blocked"):
            return f"Hydra Pay: {card['name']} is blocked."
        return (f"Hydra Pay: {card['name']} balance KSh {card['balance']}." if card else "Hydra Pay: card not found.")
    if word == "STMT":
        rows = store.payments_for_uid(card["uid"], 5)
        summary = "; ".join(f"{p['time'][5:16]} KSh {p['amount']} {p['status'].split(':')[0]}" for p in rows)
        return "Hydra Pay: " + (summary or "no payments yet.")
    return "Hydra Pay: reply BAL, STMT, HELP, STOP or START."


def send_admin(text, kind="admin"):
    try:
        import wallet
        if not wallet.settings().get("sms_admin_alerts", True):
            return None
        phone = store.to_254(wallet.settings().get("admin_phone", ""))
    except Exception:
        phone = ""
    return send(phone, text, kind=kind, transactional=True) if phone else None
