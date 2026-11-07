"""SQLite storage for cards, taps, wallet transactions and M-Pesa payments (rfid.db)."""
import csv
import io
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

import config

HERE = Path(__file__).parent
DB_PATH = config.DATA_DIR / "rfid.db"

_lock = threading.RLock()
_db = sqlite3.connect(DB_PATH, check_same_thread=False)
_db.row_factory = sqlite3.Row

KIND_LABELS = {
    "TOPUP_MPESA": "M-Pesa top-up",
    "TOPUP_CASH": "Cash top-up",
    "TAP": "Tap charge",
    "REVERSAL": "Reversal",
}


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def use_database(path):
    """Switch storage for tests. Production never calls this helper."""
    global DB_PATH, _db
    with _lock:
        _db.close()
        DB_PATH = Path(path)
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db.row_factory = sqlite3.Row


def init(default_price=1):
    with _lock:
        _db.executescript("""
        CREATE TABLE IF NOT EXISTS cards (
            uid TEXT PRIMARY KEY, name TEXT, phone TEXT, price INTEGER, balance INTEGER DEFAULT 0,
            status TEXT DEFAULT 'OUT', created TEXT);
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, uid TEXT, direction TEXT,
            result TEXT, amount INTEGER DEFAULT 0, balance INTEGER);
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, uid TEXT, kind TEXT, amount INTEGER,
            balance_after INTEGER, note TEXT, reversed INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, uid TEXT, phone TEXT, amount INTEGER,
            source TEXT, status TEXT, checkout_id TEXT, tx_id INTEGER);
        CREATE TABLE IF NOT EXISTS sms_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, phone TEXT, kind TEXT, text TEXT,
            provider TEXT, message_id TEXT, status TEXT, cost TEXT DEFAULT '', error TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS ussd_users (
            phone TEXT PRIMARY KEY, pin_hash TEXT DEFAULT '', lang TEXT DEFAULT 'en', failed INTEGER DEFAULT 0,
            locked_until TEXT DEFAULT '', created TEXT, sms_opt_out INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS ussd_sessions (
            session_id TEXT PRIMARY KEY, phone TEXT, service_code TEXT, provider TEXT, started TEXT,
            last_seen TEXT, steps TEXT DEFAULT '', last_screen TEXT DEFAULT '', ended INTEGER DEFAULT 0);
        CREATE INDEX IF NOT EXISTS idx_payments_uid_time ON payments(uid, id DESC);
        CREATE INDEX IF NOT EXISTS idx_sms_message_id ON sms_log(message_id);
        """)
        card_cols = {r[1] for r in _db.execute("PRAGMA table_info(cards)")}
        if "blocked" not in card_cols:
            _db.execute("ALTER TABLE cards ADD COLUMN blocked INTEGER DEFAULT 0")
        cols = {r[1] for r in _db.execute("PRAGMA table_info(payments)")}
        for col in ("name", "mpesa_receipt"):
            if col not in cols:
                _db.execute(f"ALTER TABLE payments ADD COLUMN {col} TEXT DEFAULT ''")
        _db.execute("UPDATE payments SET name=(SELECT name FROM cards WHERE cards.uid=payments.uid) "
                    "WHERE name IS NULL OR name=''")
        _db.commit()
        if not _db.execute("SELECT 1 FROM cards LIMIT 1").fetchone():
            _migrate_old_files(default_price)


def _migrate_old_files(default_price):
    """Bring in cards/scans from the first version (names.json, phones.json, rfid_log.csv)."""
    def load(name):
        try:
            return json.loads((HERE / name).read_text(encoding="utf-8"))
        except Exception:
            return {}

    names, phones = load("names.json"), load("phones.json")
    for uid in set(names) | set(phones):
        if uid in ("AA BB CC DD", "11 22 33 44"):
            continue
        _db.execute("INSERT OR IGNORE INTO cards (uid, name, phone, price, balance, created) VALUES (?,?,?,?,0,?)",
                    (uid, names.get(uid, uid), phones.get(uid, ""), default_price, now()))
    log = HERE / "rfid_log.csv"
    if log.exists():
        with log.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                _db.execute("INSERT INTO scans (time, uid, direction, result) VALUES (?,?,?,?)",
                            (row["time"], row["uid"], row["direction"], "old log"))
    _db.commit()


def _rows(sql, args=()):
    with _lock:
        return [dict(r) for r in _db.execute(sql, args).fetchall()]


def _one(sql, args=()):
    with _lock:
        r = _db.execute(sql, args).fetchone()
        return dict(r) if r else None


# ---------- cards ----------

def get_card(uid):
    return _one("SELECT * FROM cards WHERE uid=?", (uid,))


def list_cards():
    return _rows("SELECT * FROM cards ORDER BY name")


def cards_for_phone(phone254):
    return [c for c in list_cards() if to_254(c["phone"]) == phone254]


def save_card(uid, name, phone, price):
    with _lock:
        if get_card(uid):
            _db.execute("UPDATE cards SET name=?, phone=?, price=? WHERE uid=?", (name, phone, price, uid))
        else:
            _db.execute("INSERT INTO cards (uid, name, phone, price, balance, created) VALUES (?,?,?,?,0,?)",
                        (uid, name, phone, price, now()))
        _db.commit()
    return get_card(uid)


def move_card(old_uid, new_uid):
    """Give a person a new card (lost card, wristband...): keeps name, phone, price, balance and history."""
    with _lock:
        if not get_card(old_uid) or get_card(new_uid):
            return None
        for table in ("cards", "scans", "transactions", "payments"):
            _db.execute(f"UPDATE {table} SET uid=? WHERE uid=?", (new_uid, old_uid))
        _db.commit()
    return get_card(new_uid)


def set_card_blocked(uid, blocked=True):
    with _lock:
        _db.execute("UPDATE cards SET blocked=? WHERE uid=?", (1 if blocked else 0, uid))
        _db.commit()
    return get_card(uid)


def to_254(phone):
    p = "".join(c for c in str(phone or "") if c.isdigit())
    if p.startswith("0"):
        p = "254" + p[1:]
    elif len(p) == 9:
        p = "254" + p
    return p


# ---------- taps ----------

def tap(uid):
    """Handle one card tap. IN costs the card's price (from balance), OUT is free.
    Returns a dict describing what happened."""
    with _lock:
        card = get_card(uid)
        t = now()
        if not card:
            _db.execute("INSERT INTO scans (time, uid, direction, result) VALUES (?,?,?,?)",
                        (t, uid, "-", "unregistered"))
            _db.commit()
            return {"time": t, "uid": uid, "card": None, "result": "unregistered"}

        if card.get("blocked"):
            _db.execute("INSERT INTO scans (time, uid, direction, result, amount, balance) VALUES (?,?,?,?,?,?)",
                        (t, uid, card["status"], "blocked", 0, card["balance"]))
            _db.commit()
            return {"time": t, "uid": uid, "card": card, "direction": card["status"], "result": "blocked",
                    "balance": card["balance"], "price": card["price"], "tx_id": None}

        price = int(card["price"] or 0)
        tx_id = None
        if card["status"] == "IN":
            direction, result, charged = "OUT", "free (out)", 0
        elif card["balance"] >= price:
            direction, result, charged = "IN", "paid" if price else "free", price
        else:
            direction, result, charged = "IN", "low balance", 0

        balance = card["balance"] - charged
        if result != "low balance":
            _db.execute("UPDATE cards SET status=?, balance=? WHERE uid=?", (direction, balance, uid))
        if charged:
            cur = _db.execute(
                "INSERT INTO transactions (time, uid, kind, amount, balance_after, note) VALUES (?,?,?,?,?,?)",
                (t, uid, "TAP", -charged, balance, "Tap IN"))
            tx_id = cur.lastrowid
        _db.execute("INSERT INTO scans (time, uid, direction, result, amount, balance) VALUES (?,?,?,?,?,?)",
                    (t, uid, direction, result, charged, balance))
        _db.commit()
        return {"time": t, "uid": uid, "card": get_card(uid), "direction": direction,
                "result": result, "charged": charged, "price": price, "balance": balance, "tx_id": tx_id}


def log_swipe(uid, direction, result, amount=0):
    """Pay-per-swipe mode: record the swipe and the card's IN/OUT state (no balance)."""
    with _lock:
        t = now()
        _db.execute("UPDATE cards SET status=? WHERE uid=?", (direction, uid))
        _db.execute("INSERT INTO scans (time, uid, direction, result, amount) VALUES (?,?,?,?,?)",
                    (t, uid, direction, result, amount))
        _db.commit()
        return {"time": t, "uid": uid, "card": get_card(uid), "direction": direction, "result": result}


# ---------- money ----------

def add_money(uid, amount, kind, note=""):
    """Credit a card. Returns the transaction row."""
    with _lock:
        card = get_card(uid)
        balance = card["balance"] + amount
        _db.execute("UPDATE cards SET balance=? WHERE uid=?", (balance, uid))
        cur = _db.execute(
            "INSERT INTO transactions (time, uid, kind, amount, balance_after, note) VALUES (?,?,?,?,?,?)",
            (now(), uid, kind, amount, balance, note))
        _db.commit()
        return get_tx(cur.lastrowid)


def get_tx(tx_id):
    return _one("SELECT * FROM transactions WHERE id=?", (tx_id,))


def reverse(tx_id, note=""):
    """Undo a top-up (logged as a separate REVERSAL so nothing disappears)."""
    with _lock:
        tx = get_tx(tx_id)
        if not tx or tx["reversed"] or tx["kind"] not in ("TOPUP_CASH", "TOPUP_MPESA"):
            return None
        card = get_card(tx["uid"])
        balance = card["balance"] - tx["amount"]
        _db.execute("UPDATE cards SET balance=? WHERE uid=?", (balance, tx["uid"]))
        _db.execute("UPDATE transactions SET reversed=1 WHERE id=?", (tx_id,))
        cur = _db.execute(
            "INSERT INTO transactions (time, uid, kind, amount, balance_after, note) VALUES (?,?,?,?,?,?)",
            (now(), tx["uid"], "REVERSAL", -tx["amount"], balance, note or f"Undo {receipt_ref(tx_id)}"))
        _db.commit()
        return get_tx(cur.lastrowid)


def receipt_ref(tx_id):
    return f"RF{tx_id:05d}"


def recent_transactions(uid=None, limit=50):
    if uid:
        return _rows("SELECT * FROM transactions WHERE uid=? ORDER BY id DESC LIMIT ?", (uid, limit))
    return _rows("SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,))


def recent_scans(limit=100):
    return _rows("SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,))


# ---------- M-Pesa payments ----------

def new_payment(uid, phone, amount, source, name=""):
    with _lock:
        cur = _db.execute("INSERT INTO payments (time, uid, phone, amount, source, status, name) VALUES (?,?,?,?,?,?,?)",
                          (now(), uid, phone, amount, source, "Sending prompt...", name))
        _db.commit()
        return cur.lastrowid


def payment_by_checkout(checkout_id):
    return _one("SELECT * FROM payments WHERE checkout_id=?", (checkout_id,))


def stuck_payments():
    """Payments wrongly marked NOT PAID by the old version while M-Pesa was still processing."""
    return _rows("SELECT * FROM payments WHERE status LIKE '%still under processing%' AND checkout_id IS NOT NULL")


def update_payment(pid, **fields):
    with _lock:
        sets = ", ".join(f"{k}=?" for k in fields)
        _db.execute(f"UPDATE payments SET {sets} WHERE id=?", (*fields.values(), pid))
        _db.commit()


def get_payment(pid):
    return _one("SELECT * FROM payments WHERE id=?", (pid,))


def recent_payments(limit=30):
    return _rows("SELECT * FROM payments ORDER BY id DESC LIMIT ?", (limit,))


def payments_for_uid(uid, limit=5):
    return _rows("SELECT * FROM payments WHERE uid=? ORDER BY id DESC LIMIT ?", (uid, limit))


def pending_payment(uid):
    return _one("SELECT * FROM payments WHERE uid=? AND status IN ('Sending prompt...', 'Prompt sent - waiting for PIN')"
                " AND time >= datetime('now', 'localtime', '-3 minutes')", (uid,))


# ---------- SMS / USSD ----------

def add_sms(phone, kind, text, provider, status="QUEUED", message_id="", cost="", error=""):
    with _lock:
        cur = _db.execute("INSERT INTO sms_log (time, phone, kind, text, provider, message_id, status, cost, error) "
                          "VALUES (?,?,?,?,?,?,?,?,?)", (now(), to_254(phone), kind, text, provider, message_id,
                                                           status, cost, error))
        _db.commit()
        return _one("SELECT * FROM sms_log WHERE id=?", (cur.lastrowid,))


def update_sms(sms_id, **fields):
    if not fields:
        return
    with _lock:
        sets = ", ".join(f"{key}=?" for key in fields)
        _db.execute(f"UPDATE sms_log SET {sets} WHERE id=?", (*fields.values(), sms_id))
        _db.commit()


def update_sms_delivery(message_id, phone, status, error=""):
    with _lock:
        row = _db.execute("SELECT id FROM sms_log WHERE message_id=? ORDER BY id DESC LIMIT 1", (str(message_id),)).fetchone()
        if row:
            _db.execute("UPDATE sms_log SET status=?, error=? WHERE id=?", (status, error, row[0]))
            _db.commit()
            return True
    return False


def recent_sms(limit=20):
    return _rows("SELECT * FROM sms_log ORDER BY id DESC LIMIT ?", (limit,))


def get_ussd_user(phone):
    return _one("SELECT * FROM ussd_users WHERE phone=?", (to_254(phone),))


def save_ussd_user(phone, **fields):
    phone = to_254(phone)
    with _lock:
        if not get_ussd_user(phone):
            _db.execute("INSERT INTO ussd_users (phone, created) VALUES (?,?)", (phone, now()))
        if fields:
            sets = ", ".join(f"{key}=?" for key in fields)
            _db.execute(f"UPDATE ussd_users SET {sets} WHERE phone=?", (*fields.values(), phone))
        _db.commit()
    return get_ussd_user(phone)


def get_ussd_session(session_id):
    return _one("SELECT * FROM ussd_sessions WHERE session_id=?", (session_id,))


def save_ussd_session(session_id, phone, service_code, provider, steps, last_screen, ended=False):
    with _lock:
        existing = get_ussd_session(session_id)
        if existing:
            _db.execute("UPDATE ussd_sessions SET last_seen=?, steps=?, last_screen=?, ended=? WHERE session_id=?",
                        (now(), steps, last_screen, int(ended), session_id))
        else:
            _db.execute("INSERT INTO ussd_sessions (session_id, phone, service_code, provider, started, last_seen, steps, "
                        "last_screen, ended) VALUES (?,?,?,?,?,?,?,?,?)", (session_id, to_254(phone), service_code,
                                                                           provider, now(), now(), steps, last_screen,
                                                                           int(ended)))
        _db.commit()
    return get_ussd_session(session_id)


def recent_ussd_sessions(limit=20):
    return _rows("SELECT * FROM ussd_sessions ORDER BY last_seen DESC LIMIT ?", (limit,))


def ussd_sessions_today(phone):
    return _one("SELECT COUNT(*) AS count FROM ussd_sessions WHERE phone=? AND started LIKE ?",
                (to_254(phone), datetime.now().strftime("%Y-%m-%d") + "%"))["count"]


def append_ussd_step(session_id, step):
    session = get_ussd_session(session_id)
    try:
        data = json.loads(session.get("steps") or "{}") if session else {}
    except (TypeError, ValueError):
        data = {}
    history = data.get("history", [])
    history.append(str(step))
    return "*".join(history)


def ussd_prompt_count(phone, hours=1):
    return _one("SELECT COUNT(*) AS count FROM payments WHERE phone=? AND source='ussd' AND "
                "time >= datetime('now', 'localtime', ?)", (to_254(phone), f"-{int(hours)} hours"))["count"]


# ---------- reports ----------

def daily_summary(day):
    like = day + "%"
    tx = _rows("SELECT * FROM transactions WHERE time LIKE ?", (like,))
    scans = _rows("SELECT * FROM scans WHERE time LIKE ?", (like,))
    pays = _rows("SELECT * FROM payments WHERE time LIKE ?", (like,))
    total = lambda kind: sum(t["amount"] for t in tx if t["kind"] == kind and not t["reversed"])
    swipe_pays = [p for p in pays if p["source"] == "tap"]
    per_card = []
    for c in list_cards():
        cs = [s for s in scans if s["uid"] == c["uid"]]
        ct = [t for t in tx if t["uid"] == c["uid"] and not t["reversed"]]
        cp = [p for p in swipe_pays if p["uid"] == c["uid"]]
        paid_swipes = [p for p in cp if p["status"] == "PAID"]
        per_card.append({
            "uid": c["uid"], "name": c["name"], "phone": c["phone"], "balance": c["balance"],
            "taps": len(cs),
            "paid_taps": sum(s["result"] == "paid" for s in cs) + len(paid_swipes),
            "denied": sum(s["result"] == "low balance" for s in cs)
                      + sum(p["status"].startswith(("NOT PAID", "FAILED")) for p in cp),
            "spent": -sum(t["amount"] for t in ct if t["kind"] == "TAP") + sum(p["amount"] for p in paid_swipes),
            "topped_up": sum(t["amount"] for t in ct if t["kind"].startswith("TOPUP")),
        })
    return {
        "date": day,
        "mpesa": sum(p["amount"] for p in pays if p["status"] == "PAID"),
        "swipe_paid": sum(p["amount"] for p in swipe_pays if p["status"] == "PAID"),
        "swipe_unpaid": sum(p["status"].startswith(("NOT PAID", "FAILED")) for p in swipe_pays),
        "cash": total("TOPUP_CASH"),
        "tap_revenue": -total("TAP"),
        "taps": len(scans),
        "denied": sum(s["result"] == "low balance" for s in scans),
        "per_card": per_card,
    }


def export_csv(what, day):
    names = {c["uid"]: c["name"] for c in list_cards()}
    if what == "summary":
        rows = daily_summary(day)["per_card"]
    elif what == "payments":
        rows = _rows("SELECT time, name, uid, phone, amount, status, mpesa_receipt FROM payments "
                     "WHERE time LIKE ? ORDER BY id", (day + "%",))
    elif what == "scans":
        rows = _rows("SELECT time, uid, direction, result, amount, balance FROM scans WHERE time LIKE ? ORDER BY id",
                     (day + "%",))
    else:
        rows = [dict(t, ref=receipt_ref(t["id"]), kind=KIND_LABELS.get(t["kind"], t["kind"]))
                for t in _rows("SELECT * FROM transactions WHERE time LIKE ? ORDER BY id", (day + "%",))]
    for r in rows:
        r["name"] = names.get(r["uid"], r.get("name", ""))
    out = io.StringIO()
    if rows:
        writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return "﻿" + out.getvalue()  # BOM so Excel shows it correctly
