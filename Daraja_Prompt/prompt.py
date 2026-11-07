"""Send an M-Pesa STK push (PIN prompt) to any number and wait for the result.
Amounts can be in KSh or crypto - crypto is priced in KSh live from CoinGecko.

Usage:  python prompt.py                           (asks for everything)
        python prompt.py 0712345678 5000           (charge KSh 5,000)
        python prompt.py 0712345678 5000 usdt      (charge KSh 5,000, customer buys that much USDT)
        python prompt.py 0712345678 0.001btc       (charge the KSh price of 0.001 BTC)
        python prompt.py quote 0.001btc            (buy/sell prices, no prompt sent)
        python prompt.py quote 5000                (what KSh 5,000 is worth in every coin)
USDT is sent automatically from the Solana wallet (see wallet.py) once M-Pesa says PAID;
the customer's Solana address can go last, e.g. python prompt.py 0712345678 10usdt ADDRESS
Keys and settings come from config.json next to this file.
"""
import base64
import csv
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

CONFIG = json.loads((Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
HOST = "https://sandbox.safaricom.co.ke" if CONFIG["environment"] == "sandbox" else "https://api.safaricom.co.ke"
PENDING = {"4999", "500.001.1001"}
COINS = CONFIG.get("coins", {"btc": "bitcoin", "eth": "ethereum", "usdt": "tether"})
SELL_MARGIN = CONFIG.get("sell_margin_percent", 0) / 100   # added when the customer buys crypto from you
BUY_MARGIN = CONFIG.get("buy_margin_percent", 0) / 100     # taken off when the customer sells crypto to you
MAX_KSH = 250000                                            # M-Pesa per-transaction limit


def token():
    r = requests.get(f"{HOST}/oauth/v1/generate?grant_type=client_credentials",
                     auth=(CONFIG["consumer_key"], CONFIG["consumer_secret"]), timeout=30)
    if "access_token" not in r.text:
        sys.exit(f"Daraja login failed (HTTP {r.status_code}) - check consumer key/secret in config.json")
    return r.json()["access_token"]


def password():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return base64.b64encode(f"{CONFIG['shortcode']}{CONFIG['passkey']}{ts}".encode()).decode(), ts


def post(tok, path, data):
    r = requests.post(HOST + path, json=data, headers={"Authorization": "Bearer " + tok}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"errorMessage": f"HTTP {r.status_code}: {r.text[:200]}"}


def to_254(phone):
    p = "".join(c for c in phone if c.isdigit())
    if p.startswith("0"):
        p = "254" + p[1:]
    elif len(p) == 9:
        p = "254" + p
    return p


def prices(coins):
    """Market price of 1 coin in KSh for each coin, from CoinGecko."""
    ids = ",".join(COINS[c] for c in coins)
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                         params={"ids": ids, "vs_currencies": "kes"}, timeout=30)
        data = r.json()
        return {c: float(data[COINS[c]]["kes"]) for c in coins}
    except (requests.RequestException, ValueError, KeyError, TypeError):
        sys.exit("Couldn't get prices from CoinGecko - try again in a minute")


def rates(coin):
    """(we sell at, we buy at) for 1 coin in KSh, margins included."""
    p = prices([coin])[coin]
    return p * (1 + SELL_MARGIN), p * (1 - BUY_MARGIN)


def parse_amount(text):
    """'5000', '5,000 ksh', '0.001 btc', '10usdt' -> (number, coin or None for KSh)."""
    t = text.lower().replace(",", "").replace(" ", "")
    unit = t.lstrip("0123456789.")
    num = t[:len(t) - len(unit)]
    if not num.strip("."):
        sys.exit(f"'{text}' isn't an amount (try 5000 or 0.001 btc)")
    if unit in ("", "ksh", "kes", "sh", "/="):
        unit = None
    elif unit not in COINS:
        sys.exit(f"Unknown currency '{unit}' - use KSh or one of: {', '.join(COINS)}")
    try:
        return float(num), unit
    except ValueError:
        sys.exit(f"'{text}' isn't an amount (try 5000 or 0.001 btc)")


def fmt(x, up=False):
    """Crypto amount to 8 decimals, rounded down (or up), without trailing zeros."""
    x = (math.ceil if up else math.floor)(round(x * 1e8, 6)) / 1e8
    return f"{x:.8f}".rstrip("0").rstrip(".")


def quote(text):
    value, coin = parse_amount(text)
    coins = [coin] if coin else list(COINS)
    for c, p in prices(coins).items():
        sell, buy = p * (1 + SELL_MARGIN), p * (1 - BUY_MARGIN)
        print(f"{c.upper()}: market KSh {p:,.2f} | we sell at KSh {sell:,.2f} | we buy at KSh {buy:,.2f}")
        if coin:
            print(f"  {fmt(value)} {c.upper()}: customer pays KSh {math.ceil(value * sell):,} to buy it"
                  f" | we pay KSh {math.floor(value * buy):,} to buy it from them")
        else:
            print(f"  KSh {value:,.0f}: customer gets {fmt(value / sell)} {c.upper()}"
                  f" | customer must send {fmt(value / buy, up=True)} {c.upper()} to get it from us")


def log(*row):
    """Append one finished payment to trades.csv (open it in Excel)."""
    path = Path(__file__).parent / "trades.csv"
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "phone", "ksh", "coin", "coin_amount", "sent_to", "checkout_id", "mpesa",
                        "crypto_proof"])
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), *row])


def main():
    args = sys.argv[1:]
    if args and args[0].lower() == "quote":
        return quote("".join(args[1:]) or input("Amount - KSh or crypto, e.g. 5000 or 0.001 btc: "))

    phone = to_254(args[0] if args else input("Phone number (e.g. 0712345678): "))
    if len(phone) != 12 or not phone.startswith("254"):
        sys.exit(f"'{phone}' doesn't look like a Kenyan number")
    value, coin = parse_amount(args[1] if len(args) > 1 else
                               (input("Amount - KSh or crypto, e.g. 5000 or 0.001 btc [1]: ") or "1"))
    if coin:                         # crypto amount given: charge its KSh price, rounded up
        coin_amount = value
        rate = rates(coin)[0]
        amount = math.ceil(coin_amount * rate)
        address_arg = 2
    else:                            # KSh amount given: optionally work out how much crypto it buys
        amount = int(value)
        address_arg = 3
        coin = (args[2] if len(args) > 2 else
                "" if args else input(f"Coin they're buying ({'/'.join(COINS)}, blank = none): ")).strip().lower()
        if coin and coin not in COINS:
            sys.exit(f"Unknown coin '{coin}' - use one of: {', '.join(COINS)}")
        if coin:
            rate = rates(coin)[0]
            coin_amount = amount / rate
    if amount < 1:
        sys.exit("Amount must be at least KSh 1")
    if amount > MAX_KSH:
        sys.exit(f"KSh {amount:,} is over the M-Pesa limit of KSh {MAX_KSH:,} per transaction")

    auto_send = coin == "usdt" and "solana" in CONFIG
    if auto_send:                    # check address, password and stock BEFORE the customer pays
        import wallet
        if CONFIG["environment"] == "sandbox" and wallet.NETWORK != "devnet":
            sys.exit("M-Pesa is in sandbox (fake money) but Solana is on mainnet (real money) - refusing")
        coin_amount = math.floor(round(coin_amount * 1e6, 3)) / 1e6
        try:
            dest = wallet.check_address(args[address_arg] if len(args) > address_arg else
                                        input("Customer's Solana wallet address: "))
            kp = wallet.load()
            wallet.check_funds(kp, coin_amount)
        except wallet.WalletError as e:
            sys.exit(str(e))

    party_b = CONFIG["shortcode"]
    if CONFIG["transaction_type"] == "CustomerBuyGoodsOnline":
        party_b = CONFIG.get("till_number") or sys.exit("Set till_number in config.json for Buy Goods (Till)")

    tok = token()
    pw, ts = password()
    r = post(tok, "/mpesa/stkpush/v1/processrequest", {
        "BusinessShortCode": CONFIG["shortcode"], "Password": pw, "Timestamp": ts,
        "TransactionType": CONFIG["transaction_type"], "Amount": amount,
        "PartyA": phone, "PartyB": party_b, "PhoneNumber": phone,
        "CallBackURL": CONFIG["callback_url"],
        "AccountReference": CONFIG["account_reference"][:12], "TransactionDesc": "Payment",
    })
    if str(r.get("ResponseCode")) != "0":
        sys.exit(f"Prompt NOT sent: {r.get('errorMessage') or r.get('ResponseDescription') or r}")
    cid = r["CheckoutRequestID"]
    if coin:
        print(f"Price locked: {fmt(coin_amount)} {coin.upper()} at KSh {rate:,.2f} per {coin.upper()}")
    print(f"Prompt for KSh {amount:,} sent to {phone}. Check the phone and enter the PIN...")

    for _ in range(18):              # about 3 minutes, slow enough to stay under Daraja's rate limit
        time.sleep(10)
        pw, ts = password()
        q = post(tok, "/mpesa/stkpushquery/v1/query",
                 {"BusinessShortCode": CONFIG["shortcode"], "Password": pw, "Timestamp": ts,
                  "CheckoutRequestID": cid})
        code = str(q.get("ResultCode", ""))
        if "ResultCode" not in q or code in PENDING:
            print("  still waiting...")
            continue
        print(("PAID: " if code == "0" else "NOT PAID: ") + q.get("ResultDesc", ""))
        sig = ""
        if code == "0" and auto_send:
            print(f"  Sending {fmt(coin_amount)} USDT to {dest}...")
            try:
                sig = wallet.send_usdt(kp, dest, coin_amount)
                print(f"  SENT. Proof: {wallet.explorer(sig)}")
            except wallet.WalletError as e:
                print(f"  !! USDT NOT SENT: {e}")
                print(f"  The customer HAS paid - send {fmt(coin_amount)} USDT to {dest} by hand.")
        elif code == "0" and coin:
            print(f"  -> Send {fmt(coin_amount)} {coin.upper()} to the customer ({phone})")
        log(phone, amount, coin, fmt(coin_amount) if coin else "", dest if auto_send else "",
            cid, "PAID" if code == "0" else "NOT PAID", sig)
        return
    print("No answer from the phone after 3 minutes.")


if __name__ == "__main__":
    main()
