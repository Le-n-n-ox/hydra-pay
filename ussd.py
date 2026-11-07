"""Provider-neutral Hydra Pay USSD menu."""
import base64
import hashlib
import json
import os
import re
from copy import deepcopy
from datetime import datetime, timedelta

import sms
import store
import wallet
from telco.base import UssdReply

MAX_SCREEN = int(os.getenv("USSD_MAX_SCREEN", "160"))
STRINGS = {
    "en": {"choose": "Choose card:", "main": "Hydra Pay - {name}\n1. My card\n2. My payments\n3. {pay}\n4. Get statement by SMS\n5. Lost card / block\n6. Change PIN\n7. Lugha / Language", "pay": "Pay / Top up (M-Pesa)", "card": "{name}\nPrice: KSh {price}\nStatus: {status}{balance}", "back": "\n0 Back  00 Main", "invalid": "Invalid choice.\n", "pin": "Enter your 4-digit PIN:", "setpin": "Set a new 4-digit PIN:", "confirm_pin": "Confirm your new PIN:"},
    "sw": {"choose": "Chagua kadi:", "main": "Hydra Pay - {name}\n1. Kadi yangu\n2. Malipo yangu\n3. {pay}\n4. Tuma taarifa kwa SMS\n5. Poteza / zuia kadi\n6. Badili PIN\n7. Lugha / Language", "pay": "Lipa / Ongeza pesa (M-Pesa)", "card": "{name}\nBei: KSh {price}\nHali: {status}{balance}", "back": "\n0 Nyuma  00 Mwanzo", "invalid": "Chaguo si sahihi.\n", "pin": "Weka PIN ya tarakimu 4:", "setpin": "Weka PIN mpya ya tarakimu 4:", "confirm_pin": "Thibitisha PIN mpya:"},
}


def fit(text):
    text = re.sub(r"\s+\n", "\n", str(text or "")).strip()
    return text if len(text) <= MAX_SCREEN else text[:MAX_SCREEN - 3].rstrip() + "..."


def _settings(): return wallet.settings()
def _lang(phone): return (store.get_ussd_user(phone) or {}).get("lang") or _settings().get("ussd_language_default", "en")
def _t(state, key): return STRINGS.get(state.get("lang"), STRINGS["en"])[key]
def _card(state): return store.get_card(state.get("uid", ""))


def _root(phone):
    cards = store.cards_for_phone(phone)
    state = {"history": [], "stack": [], "lang": _lang(phone), "cards": [c["uid"] for c in cards]}
    if not cards: state["screen"] = "unregistered"
    elif len(cards) == 1: state.update(screen="main", uid=cards[0]["uid"])
    else: state.update(screen="choose", page=0)
    return state


def _push(state, screen, **updates):
    state.setdefault("stack", []).append({k: deepcopy(v) for k, v in state.items() if k not in ("stack", "history")})
    state["stack"] = state["stack"][-12:]
    state.update(updates); state["screen"] = screen


def _back(state, phone):
    if state.get("stack"):
        old = state["stack"].pop(); history, stack = state["history"], state["stack"]
        state.clear(); state.update(old); state["history"], state["stack"] = history, stack
    else: state.clear(); state.update(_root(phone))


def _home(state, phone): state.clear(); state.update(_root(phone))


def _valid_pin(pin):
    return bool(re.fullmatch(r"\d{4}", pin or "")) and pin not in ("0000", "1234") and len(set(pin)) > 1


def _hash_pin(pin):
    salt = os.urandom(16); digest = hashlib.scrypt(pin.encode(), salt=salt, n=2**14, r=8, p=1)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def _matches(pin, saved):
    try:
        salt, digest = (base64.b64decode(x) for x in saved.split("$", 1))
        return hashlib.scrypt(pin.encode(), salt=salt, n=2**14, r=8, p=1) == digest
    except Exception: return False


def _locked(user):
    try: return bool(user.get("locked_until")) and datetime.fromisoformat(user["locked_until"]) > datetime.now()
    except ValueError: return False


def _perform(state, phone, action):
    card = _card(state)
    if action in ("card", "payments"): state["screen"] = action
    elif action == "statement":
        rows = store.payments_for_uid(card["uid"], 5)
        text = "; ".join(f"{p['time'][5:16]} KSh {p['amount']} {p['status'].split(':')[0]}" for p in rows)
        sms.send(phone, f"Hydra Pay statement: {text or 'No payments yet.'}", "statement")
        state.update(screen="end", end_message="Statement sent by SMS.")
    elif action == "block":
        store.set_card_blocked(card["uid"], True)
        sms.send(phone, f"Hydra Pay: {card['name']} is blocked. Contact the desk to unblock it.", "security")
        sms.send_admin(f"Hydra Pay: {card['name']} was blocked by USSD.", "security")
        state.update(screen="end", end_message="Card blocked. Contact the desk to unblock it.")
    elif action == "pay":
        if store.pending_payment(card["uid"]): state.update(screen="end", end_message="A payment prompt is already waiting. Check your phone.")
        elif store.ussd_prompt_count(phone) >= int(_settings().get("ussd_max_prompts_per_hour", 5)): state.update(screen="end", end_message="Prompt limit reached. Try again later.")
        else:
            ok, message = wallet.start_mpesa_topup(card["uid"], state["amount"], source="ussd", phone=state["pay_phone"])
            state.update(screen="end", end_message="Check your phone for the M-Pesa prompt." if ok else message)


def _require_pin(state, phone, after):
    if not _settings().get("ussd_pin_required", True): return _perform(state, phone, after)
    user = store.get_ussd_user(phone) or {}; state["after"] = after
    if _locked(user): state["screen"] = "locked"
    elif user.get("pin_hash"): _push(state, "pin_verify")
    else: _push(state, "pin_set1")


def _handle(state, phone, value):
    screen = state.get("screen")
    if screen == "unregistered":
        if value == "1": state.update(screen="end", end_message="Visit the Hydra Pay desk with your phone number to get a card.")
        elif value == "2": state.update(screen="end", end_message="Please contact the Hydra Pay desk for help.")
        else: state["invalid"] = True
    elif screen == "choose":
        cards, page = state.get("cards", []), int(state.get("page", 0)); choices = cards[page * 5:(page + 1) * 5]
        if value == "9" and (page + 1) * 5 < len(cards): state["page"] = page + 1
        elif value.isdigit() and 1 <= int(value) <= len(choices): state.update(uid=choices[int(value)-1], screen="main", stack=[])
        else: state["invalid"] = True
    elif screen == "main":
        routes = {"1": "card", "2": "payments", "4": "statement"}
        if value in routes: _require_pin(state, phone, routes[value])
        elif value == "3":
            card = _card(state)
            if card.get("blocked"): state.update(screen="end", end_message="This card is blocked. Contact the desk.")
            elif wallet.prompt_mode(): state["amount"] = int(card["price"] or 0); _push(state, "pay_phone")
            else: _push(state, "amount")
        elif value == "5": _push(state, "block_confirm")
        elif value == "6": _push(state, "change_old" if (store.get_ussd_user(phone) or {}).get("pin_hash") else "pin_set1", change=True)
        elif value == "7": _push(state, "language")
        else: state["invalid"] = True
    elif screen == "amount":
        raw = value.replace(",", "")
        error = "Enter whole KSh amount." if not raw.isdigit() else wallet.check_amount(int(raw))
        if error: state["invalid"] = True; state["amount_error"] = error
        else: state["amount"] = int(raw); _push(state, "pay_phone")
    elif screen == "pay_phone":
        if value == "1": state["pay_phone"] = phone; _push(state, "pay_confirm")
        elif value == "2": _push(state, "other_phone")
        else: state["invalid"] = True
    elif screen == "other_phone":
        candidate = store.to_254(value)
        if re.fullmatch(r"254[17]\d{8}", candidate): state["pay_phone"] = candidate; _push(state, "pay_confirm")
        else: state["invalid"] = True; state["amount_error"] = "Enter valid 07... or 01... number."
    elif screen == "pay_confirm":
        if value == "1": _require_pin(state, phone, "pay")
        elif value == "2": _home(state, phone)
        else: state["invalid"] = True
    elif screen == "block_confirm":
        if value == "1": _require_pin(state, phone, "block")
        elif value == "2": _home(state, phone)
        else: state["invalid"] = True
    elif screen == "pin_verify":
        user = store.get_ussd_user(phone) or {}
        if _matches(value, user.get("pin_hash", "")):
            store.save_ussd_user(phone, failed=0, locked_until=""); _perform(state, phone, state.get("after", "card"))
        else:
            failed = int(user.get("failed", 0)) + 1; fields = {"failed": failed}
            if failed >= 3:
                fields["locked_until"] = (datetime.now() + timedelta(minutes=30)).isoformat(timespec="seconds")
                sms.send(phone, "Hydra Pay: your USSD PIN is locked for 30 minutes.", "security")
            store.save_ussd_user(phone, **fields); state["invalid"] = True
    elif screen == "pin_set1":
        if not _valid_pin(value): state["invalid"] = True; state["amount_error"] = "Use a safe 4-digit PIN."
        else: state["new_pin"] = value; _push(state, "pin_set2")
    elif screen == "pin_set2":
        if value != state.get("new_pin"): state["invalid"] = True; state["amount_error"] = "PINs do not match."
        else:
            store.save_ussd_user(phone, pin_hash=_hash_pin(value), failed=0, locked_until="")
            if state.get("change"):
                sms.send(phone, "Hydra Pay: your USSD PIN was changed.", "security"); state.update(screen="end", end_message="PIN changed.")
            else: _perform(state, phone, state.get("after", "card"))
    elif screen == "change_old":
        if _matches(value, (store.get_ussd_user(phone) or {}).get("pin_hash", "")): _push(state, "pin_set1", change=True)
        else: state["invalid"] = True
    elif screen == "language":
        if value in ("1", "2"):
            store.save_ussd_user(phone, lang="en" if value == "1" else "sw"); _home(state, phone)
        else: state["invalid"] = True


def _render(state):
    card, screen = _card(state), state.get("screen"); prefix = _t(state, "invalid") if state.pop("invalid", False) else ""; back = _t(state, "back")
    if screen == "end": return UssdReply(fit(state.get("end_message", "Done.")), True)
    if screen == "unregistered": return UssdReply(fit(prefix + "Hydra Pay\nThis number has no card.\n1. How to get a card\n2. Contact the desk"))
    if screen == "choose":
        cards, page = state.get("cards", []), int(state.get("page", 0)); visible = cards[page * 5:(page + 1) * 5]
        rows = [_t(state, "choose")] + [f"{i}. {store.get_card(uid)['name'][:22]}" for i, uid in enumerate(visible, 1)]
        if (page + 1) * 5 < len(cards): rows.append("9. More")
        return UssdReply(fit(prefix + "\n".join(rows) + back))
    if screen == "main": return UssdReply(fit(prefix + _t(state, "main").format(name=card["name"].split()[0][:20], pay=_t(state, "pay")) + back))
    if screen == "card":
        balance = f"\nBalance: KSh {card['balance']}" if not wallet.prompt_mode() else ""
        return UssdReply(fit(_t(state, "card").format(name=card["name"][:28], price=card["price"], status=card["status"], balance=balance) + back))
    if screen == "payments":
        rows = ["Recent payments:"] + [f"{p['time'][5:16]} KSh {p['amount']} {p['status'].split(':')[0][:7]}" for p in store.payments_for_uid(card["uid"], 3)]
        return UssdReply(fit("\n".join(rows) if len(rows) > 1 else "No payments yet."))
    if screen == "amount": return UssdReply(fit(prefix + state.get("amount_error", "Enter amount in KSh:") + back))
    if screen == "pay_phone": return UssdReply(fit(prefix + "Pay to:\n1. This number\n2. Another M-Pesa number" + back))
    if screen == "other_phone": return UssdReply(fit(prefix + state.get("amount_error", "Enter M-Pesa number:") + back))
    if screen == "pay_confirm": return UssdReply(fit(f"Send M-Pesa prompt KSh {state['amount']} to 0{state['pay_phone'][3:]} for {card['name'][:18]}?\n1. Yes\n2. No" + back))
    if screen == "block_confirm": return UssdReply(fit("Block " + card["name"][:24] + "?\n1. Yes\n2. No" + back))
    if screen == "locked": return UssdReply("PIN locked. Try again in 30 minutes.", True)
    if screen in ("pin_verify", "change_old"): return UssdReply(fit(prefix + _t(state, "pin") + back))
    if screen == "pin_set1": return UssdReply(fit(prefix + _t(state, "setpin") + back))
    if screen == "pin_set2": return UssdReply(fit(prefix + _t(state, "confirm_pin") + back))
    if screen == "language": return UssdReply(fit("1. English\n2. Kiswahili" + back))
    return UssdReply("Sorry, try again later.", True)


def handle(request):
    if not request.phone or not request.session_id: return UssdReply("Sorry, try again later.", True)
    saved = store.get_ussd_session(request.session_id)
    try: state = json.loads(saved.get("steps") or "{}") if saved else _root(request.phone)
    except (TypeError, ValueError): state = _root(request.phone)
    if not saved and state.get("screen") == "unregistered" and not store.ussd_sessions_today(request.phone):
        sms.send_admin(f"Hydra Pay: unregistered USSD caller {request.phone}.", "unregistered_ussd")
    incoming, old = [s for s in (request.text or "").split("*") if s != ""], state.get("history", [])
    if incoming[:len(old)] == old: new = incoming[len(old):]
    else: state, new = _root(request.phone), incoming
    for value in new:
        state["history"].append(value)
        if value == "00": _home(state, request.phone)
        elif value == "0": _back(state, request.phone)
        elif state.get("screen") != "end": _handle(state, request.phone, value)
    reply = _render(state)
    store.save_ussd_session(request.session_id, request.phone, request.service_code, getattr(request, "provider", ""), json.dumps(state), state.get("screen", ""), reply.end)
    return reply
