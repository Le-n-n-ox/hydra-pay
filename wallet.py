"""Wallet actions: M-Pesa and cash top-ups, tap handling, WhatsApp receipts."""
import json
import threading
from pathlib import Path

import mpesa
import sms
import store
import whatsapp

SETTINGS = Path(__file__).parent / "settings.json"


def settings():
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def update_settings(values):
    """Persist only dashboard-safe settings; provider secrets stay in .env."""
    allowed = {"ussd_code", "ussd_language_default", "ussd_pin_required", "ussd_max_prompts_per_hour",
               "sms_receipts", "sms_when_whatsapp_fails", "sms_low_balance", "sms_admin_alerts", "admin_phone"}
    current = settings()
    for key, value in values.items():
        if key in allowed:
            current[key] = value
    SETTINGS.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return current


def _async(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()


def _send_customer(phone, text, sms_text=None, kind="notice", force_sms=False):
    """WhatsApp first; SMS is a configured fallback or explicit receipt."""
    delivered = whatsapp.send_text(phone, text)
    if force_sms or (not delivered and settings().get("sms_when_whatsapp_fails", True)):
        sms.send(phone, sms_text or text, kind=kind)


def notify(card, text, sms_text=None, kind="notice", force_sms=False):
    """Notify the owner and keep the existing optional WhatsApp admin copy."""
    phone = store.to_254(card["phone"])
    if phone:
        _async(_send_customer, phone, text, sms_text, kind, force_sms)
    admin = store.to_254(settings().get("admin_whatsapp", ""))
    if admin and admin != phone:
        _async(whatsapp.send_text, admin, f"[Copy for admin]\n{text}")


def voice_thanks(card, amount, balance=None):
    """About 30 seconds of spoken thanks, sent to the card owner after a confirmed payment."""
    s = settings()
    phone = store.to_254(card["phone"])
    if not phone or not s.get("voice_receipts", True):
        return
    biz = s.get("business_name", "Hydra Pay")
    first = (card["name"] or "").split()[0] if card["name"] else "there"
    balance_line = f" Your new balance is {balance} shillings." if balance is not None else ""
    text = (f"Hi {first}! Welcome to {biz}. Your payment of {abs(amount)} shillings has been received "
            f"and confirmed by Safaricom, so you're all set.{balance_line} Your M-Pesa code is in the "
            f"receipt we've just sent you. With {biz} there's no cash, no change and no fake messages. "
            f"Just tap your card and enter your PIN. If you ever want to check your card or your recent "
            f"payments, reply menu here on WhatsApp, or send us a voice note. "
            f"Thank you for paying with {biz}. Have a great day!")
    _async(whatsapp.send_voice, phone, text)


def receipt(card, tx, extra=""):
    s = settings()
    lines = [
        f"🧾 *{s.get('business_name', 'RFID Wallet')} Receipt*",
        f"Ref: {store.receipt_ref(tx['id'])}",
        f"Date: {tx['time']}",
        f"Card: {card['name']}",
        f"Type: {store.KIND_LABELS.get(tx['kind'], tx['kind'])}",
        f"Amount: KSh {abs(tx['amount'])}",
        f"New balance: KSh {tx['balance_after']}",
    ]
    if extra:
        lines.append(extra)
    lines.append("\nReply *menu* for options.")
    return "\n".join(lines)


# ---------- top-ups ----------

def check_amount(amount):
    s = settings()
    lo, hi = int(s.get("min_topup", 1)), int(s.get("max_topup", 10000))
    if not (lo <= amount <= hi):
        return f"Amount must be between KSh {lo} and KSh {hi}"
    return None


def prompt_mode():
    """'prompt' = every swipe IN sends an M-Pesa prompt. 'wallet' = swipes use a prepaid balance."""
    return settings().get("mode", "prompt") != "wallet"


def payment_receipt(card, pay, mpesa_desc=""):
    s = settings()
    return "\n".join(line for line in [
        f"🧾 *{s.get('business_name', 'RFID Wallet')} Receipt*",
        f"Ref: RFP{pay['id']:05d}",
        f"Date: {store.now()}",
        f"Card: {card['name']}",
        f"Paid: KSh {pay['amount']} via M-Pesa ({pay['phone']})",
        f"M-Pesa code: {pay['mpesa_receipt']}" if pay.get("mpesa_receipt") else "",
        "✅ Tapped IN" if pay["source"] == "tap" else "",
        "\nThank you! Reply *menu* for options.",
    ] if line)


def start_mpesa_topup(uid, amount, source="dashboard", phone=None):
    """Send an M-Pesa prompt. In wallet mode the card is credited once the person enters
    their PIN; for swipe payments (source='tap') nothing is credited, it's just paid.
    Returns (ok, message)."""
    card = store.get_card(uid)
    if not card:
        return False, "Unknown card"
    err = check_amount(amount)
    if err:
        return False, err
    phone = store.to_254(phone or card["phone"])
    if not phone:
        return False, f"{card['name']} has no phone number"
    if not mpesa.config().get("consumer_key"):
        return False, "M-Pesa keys missing in mpesa_config.json"
    if store.pending_payment(uid):
        return False, f"A prompt is already waiting on {card['name']}'s phone"
    pid = store.new_payment(uid, phone, amount, source, card["name"])
    _async(_run_payment, pid, uid, phone, amount)
    return True, f"M-Pesa prompt for KSh {amount} sent to {phone}"


_finish_lock = threading.Lock()


def _is_open(pid):
    status = store.get_payment(pid)["status"]
    return status.startswith(("Sending", "Prompt sent")) or "still under processing" in status


def _run_payment(pid, uid, phone, amount):
    card = store.get_card(uid)
    base = whatsapp.public_url()
    try:
        ok, result = mpesa.stk_push(phone, amount, reference=card["name"].replace(" ", "")[:12] or "RFID",
                                    desc="RFID payment",
                                    callback_url=f"{base}/mpesa/callback" if base else None)
        if not ok:
            finish_payment(pid, False, result, failed=True)
            return
        store.update_payment(pid, status="Prompt sent - waiting for PIN", checkout_id=result)
        print(f"  M-Pesa prompt sent to {phone} (KSh {amount}) for {card['name']}")
        outcome = mpesa.wait_for_result(result, done=lambda: not _is_open(pid))
    except Exception as e:
        finish_payment(pid, False, str(e), failed=True)
        return
    if outcome:
        finish_payment(pid, *outcome)


def finish_payment(pid, paid, desc, mpesa_receipt="", failed=False):
    """Record the result of an M-Pesa prompt (from polling or Safaricom's callback). Runs once per payment."""
    with _finish_lock:
        if not _is_open(pid):
            if mpesa_receipt:   # callback arrived after polling already marked it paid: just add the code
                store.update_payment(pid, mpesa_receipt=mpesa_receipt)
            return
        pay = store.get_payment(pid)
        card = store.get_card(pay["uid"])
        if mpesa_receipt:
            store.update_payment(pid, mpesa_receipt=mpesa_receipt)
        if paid and pay["source"] == "tap":
            store.update_payment(pid, status="PAID")
            print(f"  M-Pesa {card['name']}: PAID KSh {pay['amount']} {mpesa_receipt}")
            notify(card, payment_receipt(card, store.get_payment(pid)),
                   f"{settings().get('business_name', 'Hydra Pay')}: KSh {pay['amount']} received from {card['name']}. Ref RFP{pay['id']:05d}.",
                   "payment", settings().get("sms_receipts", True))
            voice_thanks(card, pay["amount"])
        elif paid:
            tx = store.add_money(pay["uid"], pay["amount"], "TOPUP_MPESA", f"M-Pesa from {pay['phone']}")
            store.update_payment(pid, status="PAID", tx_id=tx["id"])
            print(f"  M-Pesa top-up {card['name']}: PAID KSh {pay['amount']}, balance {tx['balance_after']}")
            notify(store.get_card(pay["uid"]), receipt(card, tx),
                   f"{settings().get('business_name', 'Hydra Pay')}: KSh {pay['amount']} top-up received. Ref {store.receipt_ref(tx['id'])}.",
                   "payment", settings().get("sms_receipts", True))
            voice_thanks(card, pay["amount"], tx["balance_after"])
        else:
            store.update_payment(pid, status=f"{'FAILED' if failed else 'NOT PAID'}: {desc}")
            print(f"  M-Pesa {card['name']}: {'FAILED' if failed else 'NOT PAID'} ({desc})")
            if not failed:
                notify(card, f"❌ Payment of KSh {pay['amount']} was not completed ({desc}).",
                       f"{settings().get('business_name', 'Hydra Pay')}: payment of KSh {pay['amount']} was not completed.",
                       "payment", settings().get("sms_receipts", True))


def recheck_stuck():
    """Fix payments the old version wrongly marked NOT PAID while M-Pesa was still processing."""
    for p in store.stuck_payments():
        result = mpesa.query(p["checkout_id"])
        if result:
            finish_payment(p["id"], *result)
            print(f"  Re-checked M-Pesa payment #{p['id']} ({p['name']}): {'PAID' if result[0] else result[1]}")


def cash_topup(uid, amount):
    card = store.get_card(uid)
    if not card:
        return None, "Unknown card"
    err = check_amount(amount)
    if err:
        return None, err
    tx = store.add_money(uid, amount, "TOPUP_CASH", "Cash at desk")
    print(f"  Cash top-up {card['name']}: KSh {amount}, balance {tx['balance_after']}")
    notify(card, receipt(card, tx))
    return tx, f"KSh {amount} cash added to {card['name']}"


def undo(tx_id):
    tx = store.reverse(tx_id)
    if not tx:
        return None, "That top-up can't be undone"
    card = store.get_card(tx["uid"])
    notify(card, receipt(card, tx, "A top-up was reversed by the admin."))
    return tx, f"Reversed. {card['name']} balance is now KSh {tx['balance_after']}"


# ---------- taps ----------

def on_tap(uid):
    if prompt_mode():
        return on_tap_prompt(uid)
    ev = store.tap(uid)
    card = ev["card"]
    if not card:
        print(f"{ev['time']}  NEW CARD  {uid}  (register it on the dashboard)")
        return ev
    if ev["result"] == "blocked":
        notify(card, f"{card['name']}: a blocked card was tapped. Contact the desk.",
               f"{settings().get('business_name', 'Hydra Pay')}: your blocked card was tapped. Contact the desk.",
               "security", True)
        sms.send_admin(f"Hydra Pay: blocked card {card['name']} was tapped.", "security")
        return ev
    print(f"{ev['time']}  {ev['direction']:<3}  {uid}  {card['name']}  {ev['result']}  balance KSh {card['balance']}")

    s = settings()
    if ev["result"] == "low balance":
        msg = (f"⚠️ {card['name']}: not enough balance to tap IN.\n"
               f"Price KSh {ev['price']}, balance KSh {card['balance']}.\nReply *2* to top up with M-Pesa.")
        notify(card, msg, f"{settings().get('business_name', 'Hydra Pay')}: low balance. Price KSh {ev['price']}, balance KSh {card['balance']}.",
               "low_balance", s.get("sms_low_balance", True))
        auto = int(s.get("auto_topup_amount", 0) or 0)
        if auto > 0:
            start_mpesa_topup(uid, auto, source="auto (low balance)")
    elif s.get("notify_taps", True):
        if ev["result"] == "paid":
            tx = store.get_tx(ev["tx_id"])
            notify(card, receipt(card, tx, "✅ Tapped IN"))
        elif ev["direction"] == "OUT":
            notify(card, f"👋 {card['name']} tapped OUT at {ev['time'][11:16]}. Balance KSh {card['balance']}.")
        else:
            notify(card, f"✅ {card['name']} tapped IN at {ev['time'][11:16]} (free). Balance KSh {card['balance']}.")
    return ev


def on_tap_prompt(uid):
    """Pay-per-swipe: swipe IN sends one M-Pesa prompt for the card's price, OUT is free."""
    card = store.get_card(uid)
    if not card:
        ev = store.tap(uid)   # logs the unregistered scan
        print(f"{ev['time']}  NEW CARD  {uid}  (register it on the dashboard)")
        return ev
    if card.get("blocked"):
        ev = store.log_swipe(uid, card["status"], "blocked")
        notify(card, f"{card['name']}: a blocked card was tapped. Contact the desk.",
               f"{settings().get('business_name', 'Hydra Pay')}: your blocked card was tapped. Contact the desk.",
               "security", True)
        sms.send_admin(f"Hydra Pay: blocked card {card['name']} was tapped.", "security")
        return ev
    price = int(card["price"] or 0)
    if card["status"] == "IN":
        direction, result = "OUT", "free (out)"
    elif price <= 0:
        direction, result = "IN", "free"
    else:
        direction = "IN"
        ok, msg = start_mpesa_topup(uid, price, source="tap")
        result = "M-Pesa prompt sent" if ok else f"prompt not sent: {msg}"
    ev = store.log_swipe(uid, direction, result, price if direction == "IN" else 0)
    print(f"{ev['time']}  {direction:<3}  {uid}  {card['name']}  {result}")
    return ev
