"""WhatsApp bot with a numbered menu.

Any message shows the menu. Card owners can see their card and payments, change their
own phone number, chat with the AI assistant, or get help. Voice notes are understood
with Gemini and answered with an ElevenLabs voice note."""
import json
import re
import threading
from collections import defaultdict

import store
import wallet
import whatsapp

sessions = {}                      # phone -> {"state": ..., "new_phone": ...}
histories = defaultdict(list)      # phone -> recent AI chat turns
phone_locks = defaultdict(threading.Lock)
seen_ids = set()

MENU_WORDS = {"hi", "hii", "hello", "hey", "menu", "start", "habari", "mambo", "niaje", "sasa", "jambo", "0",
              "back", "rudi", "cancel"}
LINE = "━━━━━━━━━━━━━━"

SYSTEM_PROMPT = """You are the friendly WhatsApp assistant for {business}, a tap-card (RFID) payment system in Kenya.
How it works: each person has a card. Swiping the card IN on the reader sends an M-Pesa prompt (STK push)
to their phone for the card's price; they enter their PIN and get a receipt on WhatsApp. Swiping OUT is free.
People can change their own phone number from the WhatsApp menu (option 3).

What you know about this person (live data, trust it):
{info}

How you talk:
- WhatsApp style: short, warm, 1-3 sentences, plain text, at most one emoji.
- Mirror their language: English, Kiswahili or Sheng.
- Never invent payments, prices or rules. Use only the data above. If you don't know, say so.
- Remind them they can send *0* for the menu when it helps.

Answer with ONLY JSON: {{"reply": "<message>"}}"""


def business():
    return wallet.settings().get("business_name", "RFID Pay")


def local(phone254):
    """2547XXXXXXXX -> 07XXXXXXXX for display."""
    p = store.to_254(phone254)
    return "0" + p[3:] if p.startswith("254") else p


# ---------- menu texts ----------

def menu_text(cards):
    if not cards:
        return (f"👋 Welcome to *{business()}*!\n"
                "This WhatsApp number isn't linked to a card yet.\n"
                f"{LINE}\n"
                "1️⃣ How it works / get a card\n"
                "2️⃣ Talk to the assistant 🤖\n"
                f"{LINE}\n"
                "Reply with a number.")
    names = ", ".join(c["name"] for c in cards)
    return (f"👋 Hi *{names}*! Welcome to *{business()}*\n"
            f"{LINE}\n"
            "1️⃣ My card\n"
            "2️⃣ My payments\n"
            "3️⃣ Change my phone number\n"
            "4️⃣ Talk to the assistant 🤖\n"
            "5️⃣ Help\n"
            f"{LINE}\n"
            "Reply with a number. Send *0* anytime for this menu.\n"
            "🎤 You can also send a voice note.")


def card_text(cards):
    lines = ["💳 *My card*"]
    for c in cards:
        lines.append(f"\n*{c['name']}*\n"
                     f"Price per swipe IN: KSh {c['price']}\n"
                     f"M-Pesa / WhatsApp number: {local(c['phone'])}\n"
                     f"Right now: {'IN ✅' if c['status'] == 'IN' else 'OUT'}")
    lines.append("\nSend *3* to change the number, *0* for the menu.")
    return "\n".join(lines)


def payments_text(cards):
    uids = {c["uid"] for c in cards}
    pays = [p for p in store.recent_payments(200) if p["uid"] in uids][:5]
    if not pays:
        return "🧾 *My payments*\nNo payments yet. Swipe your card to pay.\n\nSend *0* for the menu."
    icon = lambda s: "✅" if s == "PAID" else ("⏳" if s.startswith(("Sending", "Prompt")) else "❌")
    rows = [f"{icon(p['status'])} {p['time'][5:16]}  KSh {p['amount']}"
            + (f"  {p['mpesa_receipt']}" if p.get("mpesa_receipt") else "") for p in pays]
    paid = sum(p["amount"] for p in pays if p["status"] == "PAID")
    return "🧾 *My last payments*\n" + "\n".join(rows) + f"\n\nPaid in these: KSh {paid}\nSend *0* for the menu."


HELP_TEXT = ("ℹ️ *Help*\n"
             "• Swipe your card IN on the reader, an M-Pesa prompt pops up on your phone, enter your PIN.\n"
             "• You get a receipt here on WhatsApp after paying.\n"
             "• Swiping OUT is free.\n"
             "• New number? Just send it here (e.g. *0712345678*) and confirm.\n"
             "• Lost your card or need help? Talk to the admin at the desk.\n\n"
             "Send *0* for the menu.")

HOW_IT_WORKS = ("ℹ️ *How it works*\n"
                "Each person gets an RFID card linked to their phone number. Swipe it on the reader and you "
                "pay with an M-Pesa prompt on your phone, then get a receipt here.\n\n"
                "To get a card, visit the admin at the desk and give them this WhatsApp number.\n\n"
                "Send *0* for the menu.")


# ---------- phone number change ----------

def parse_phone(text):
    digits = re.sub(r"\D", "", text)
    p = store.to_254(digits)
    return p if re.fullmatch(r"254[17]\d{8}", p) else None


def change_phone(phone, cards, new254):
    for c in cards:
        store.save_card(c["uid"], c["name"], local(new254), c["price"])
    names = ", ".join(c["name"] for c in cards)
    print(f"  {names}: phone changed by owner from {local(phone)} to {local(new254)}")
    if new254 != phone:
        whatsapp.send_text(new254, f"✅ This number is now linked to card *{names}* on {business()}.\n"
                                   "M-Pesa prompts and receipts will come here. Send *hi* for the menu.")
    admin = store.to_254(wallet.settings().get("admin_whatsapp", ""))
    if admin:
        whatsapp.send_text(admin, f"[Admin] {names} changed their number from {local(phone)} to {local(new254)}")
    return (f"✅ Done! *{names}* is now linked to *{local(new254)}*.\n"
            "M-Pesa prompts and receipts will go to that number."
            + ("\n\nFrom now on, message me from the new number." if new254 != phone else ""))


# ---------- AI ----------

def ask_ai(phone, cards, text):
    uids = {c["uid"] for c in cards}
    info = {
        "cards": [{"name": c["name"], "price_per_swipe_ksh": c["price"], "status": c["status"],
                   "phone": local(c["phone"])} for c in cards],
        "recent_payments": [{"time": p["time"], "amount": p["amount"], "status": p["status"]}
                            for p in store.recent_payments(200) if p["uid"] in uids][:5],
    } if cards else "This WhatsApp number is not linked to any card."
    system = SYSTEM_PROMPT.format(business=business(), info=json.dumps(info))
    hist = histories[phone]
    hist.append({"role": "user", "parts": [{"text": text}]})
    del hist[:-10]
    while hist and hist[0]["role"] != "user":
        hist.pop(0)
    raw = whatsapp.gemini(hist, system=system, json_mode=True)
    hist.append({"role": "model", "parts": [{"text": raw}]})
    try:
        return str(json.loads(raw[raw.find("{"): raw.rfind("}") + 1]).get("reply", "")).strip() or raw
    except ValueError:
        return raw


# ---------- message flow ----------

def reply(phone, text, voice):
    whatsapp.send_text(phone, text)
    if voice and wallet.settings().get("voice_replies", True):
        spoken = re.sub(r"[*━]", "", text)
        for n in range(6):
            spoken = spoken.replace(f"{n}️⃣", f"{n},")
        whatsapp.send_voice(phone, spoken)


def route(phone, text, voice):
    s = sessions.get(phone)
    first_time = s is None
    s = sessions.setdefault(phone, {"state": "menu"})
    cards = store.cards_for_phone(phone)
    low = text.lower().strip(" .!?*")

    if low in MENU_WORDS or (first_time and not voice):
        s["state"] = "menu"
        return reply(phone, menu_text(cards), voice)

    state = s["state"]

    # --- changing phone number ---
    if state == "new_phone":
        new = parse_phone(text)
        if not new:
            return reply(phone, "❌ That doesn't look like a phone number. Send it like *0712345678*, "
                                "or *0* to cancel.", voice)
        s.update(state="confirm_phone", new_phone=new)
        return reply(phone, f"Change your card's number from *{local(phone)}* to *{local(new)}*?\n"
                            "1️⃣ Yes, change it\n2️⃣ No, cancel", voice)
    if state == "confirm_phone":
        if low in ("1", "yes", "y", "ndio", "ndiyo", "sawa"):
            s["state"] = "menu"
            return reply(phone, change_phone(phone, cards, s.pop("new_phone")), voice)
        s["state"] = "menu"
        s.pop("new_phone", None)
        return reply(phone, "👍 Cancelled, your number was not changed.\n\n" + menu_text(cards), voice)

    # --- AI chat ---
    if state == "chat":
        return ai_reply(phone, cards, text, voice)

    # --- quick number change: "3 0712345678", "change 0712345678" or just the new number ---
    quick = re.fullmatch(r"(?:3|change|badilisha)?\s*(\+?[\d][\d\s-]{8,})", low)
    if cards and quick and parse_phone(quick.group(1)):
        new = parse_phone(quick.group(1))
        s.update(state="confirm_phone", new_phone=new)
        return reply(phone, f"Change your card's number from *{local(phone)}* to *{local(new)}*?\n"
                            "1️⃣ Yes, change it\n2️⃣ No, cancel", voice)

    # --- main menu choices ---
    if cards:
        if low == "1":
            return reply(phone, card_text(cards), voice)
        if low == "2":
            return reply(phone, payments_text(cards), voice)
        if low == "3":
            s["state"] = "new_phone"
            return reply(phone, f"📱 Your card's number is *{local(phone)}*.\n"
                                "Send the new M-Pesa number, e.g. *0712345678*\n(or *0* to cancel)", voice)
        if low == "4":
            s["state"] = "chat"
            return reply(phone, "🤖 Ask me anything about your card or payments.\nSend *0* to go back to the menu.", voice)
        if low == "5":
            return reply(phone, HELP_TEXT, voice)
    else:
        if low == "1":
            return reply(phone, HOW_IT_WORKS, voice)
        if low == "2":
            s["state"] = "chat"
            return reply(phone, "🤖 Ask me anything. Send *0* to go back to the menu.", voice)

    # voice notes and questions in plain words: let the assistant answer, then point to the menu
    if voice or len(low) > 12:
        return ai_reply(phone, cards, text, voice)
    return reply(phone, "🤔 I didn't get that. Pick a number from the menu:\n\n" + menu_text(cards), voice)


def ai_reply(phone, cards, text, voice):
    if not whatsapp.GEMINI_KEY:
        return reply(phone, "The assistant is offline right now.\n\n" + menu_text(cards), voice)
    try:
        answer = ask_ai(phone, cards, text)
    except Exception as e:
        print(f"[AI] FAILED: {e}")
        return reply(phone, "Sorry, the assistant is having trouble right now.\n\n" + menu_text(cards), voice)
    reply(phone, answer, voice)


def handle(payload):
    """Called by the /webhook route with the UltraMsg JSON."""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    sender = data.get("from") or ""
    if (data.get("fromMe") or not sender or sender.endswith(("@g.us", "@newsletter", "@broadcast"))
            or payload.get("event_type", "message_received") not in ("message_received", "")):
        return
    msg_id = data.get("id") or ""
    if msg_id:
        if msg_id in seen_ids:
            return
        seen_ids.add(msg_id)
        if len(seen_ids) > 5000:
            seen_ids.clear()
    threading.Thread(target=_handle, args=(sender, data), daemon=True).start()


def _handle(sender, data):
    phone = sender.split("@")[0]
    kind = data.get("type") or "chat"
    try:
        with phone_locks[phone]:
            if kind in ("ptt", "audio") and data.get("media"):
                text = whatsapp.transcribe(data["media"])
                print(f"[IN ] {phone} (voice note): {text}")
                if not text:
                    return whatsapp.send_text(phone, "Sorry, I couldn't hear that voice note. Please type it, "
                                                     "or send *0* for the menu.")
                route(phone, text, voice=True)
            elif kind == "chat" and (data.get("body") or "").strip():
                print(f"[IN ] {phone}: {data['body']}")
                route(phone, data["body"].strip(), voice=False)
            else:
                whatsapp.send_text(phone, "I can read text and voice notes 🎤. Send *0* for the menu.")
    except Exception as e:
        print(f"[BOT] error for {phone}: {e}")
