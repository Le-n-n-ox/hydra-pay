"""Solana wallet that sends USDT (or test USDT on devnet) to customers.

Usage:  python wallet.py new                     create the wallet (asks for a password) -> wallet.key
        python wallet.py balance                 address, SOL and USDT balance
        python wallet.py setup-test              devnet only: free test SOL + 1,000 test USDT
        python wallet.py send ADDRESS AMOUNT     send USDT by hand
Settings are under "solana" in config.json. The private key never leaves wallet.key,
and wallet.key is encrypted with your password.
"""
import base64
import getpass
import json
import os
import struct
import sys
import time
from pathlib import Path

import requests
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.system_program import ID as SYSTEM_PROGRAM, CreateAccountParams, create_account
from solders.transaction import Transaction

HERE = Path(__file__).parent
CONFIG_PATH = HERE / "config.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
SOL = CONFIG["solana"]
NETWORK = SOL["network"]                    # "devnet" (test money) or "mainnet" (real money)
RPC = "https://api.devnet.solana.com" if NETWORK == "devnet" else "https://api.mainnet-beta.solana.com"
MAINNET_USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
KEY_FILE = HERE / SOL.get("wallet_file", "wallet.key")
TOKEN_PROGRAM = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ATA_PROGRAM = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
DECIMALS = 6                                # USDT has 6 decimal places
MIN_SOL = 0.003                             # fees + opening a USDT account for a new customer


class WalletError(Exception):
    pass


# ---------- Solana network ----------

def rpc(method, *params):
    try:
        r = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)},
                          timeout=30).json()
    except (requests.RequestException, ValueError) as e:
        raise WalletError(f"Can't reach Solana ({e.__class__.__name__}) - check the internet")
    if "error" in r:
        raise WalletError(f"Solana said: {r['error'].get('message', r['error'])}")
    return r["result"]


def explorer(sig):
    return f"https://explorer.solana.com/tx/{sig}" + ("?cluster=devnet" if NETWORK == "devnet" else "")


def send_tx(instructions, signers):
    """Sign, send and wait for confirmation. Returns the transaction signature."""
    blockhash = Hash.from_string(rpc("getLatestBlockhash", {"commitment": "confirmed"})["value"]["blockhash"])
    tx = Transaction(signers, Message(instructions, signers[0].pubkey()), blockhash)
    sig = rpc("sendTransaction", base64.b64encode(bytes(tx)).decode(), {"encoding": "base64"})
    for _ in range(30):
        time.sleep(2)
        status = rpc("getSignatureStatuses", [sig])["value"][0]
        if status and status.get("err"):
            raise WalletError(f"Transaction failed: {status['err']}")
        if status and status.get("confirmationStatus") in ("confirmed", "finalized"):
            return sig
    # Not confirmed yet does NOT mean it failed - never just resend, check first.
    raise WalletError(f"Not confirmed after 60s. Check before resending: {explorer(sig)}")


# ---------- USDT (SPL token) ----------

def usdt_mint():
    mint = SOL.get("usdt_mint") or (MAINNET_USDT if NETWORK == "mainnet" else "")
    if not mint:
        raise WalletError("No test USDT yet - choose 5 in Prompt.bat (or run: python wallet.py setup-test)")
    return Pubkey.from_string(mint)


def token_account(owner, mint):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN_PROGRAM), bytes(mint)], ATA_PROGRAM)[0]


def ix_open_account(payer, owner, mint):
    """Open owner's USDT account if it doesn't exist yet (does nothing if it does)."""
    return Instruction(ATA_PROGRAM, bytes([1]), [
        AccountMeta(payer, True, True), AccountMeta(token_account(owner, mint), False, True),
        AccountMeta(owner, False, False), AccountMeta(mint, False, False),
        AccountMeta(SYSTEM_PROGRAM, False, False), AccountMeta(TOKEN_PROGRAM, False, False)])


def ix_transfer(owner, dest_owner, mint, units):
    return Instruction(TOKEN_PROGRAM, struct.pack("<BQB", 12, units, DECIMALS), [
        AccountMeta(token_account(owner, mint), False, True), AccountMeta(mint, False, False),
        AccountMeta(token_account(dest_owner, mint), False, True), AccountMeta(owner, True, False)])


def ix_mint_to(mint, dest_owner, authority, units):
    return Instruction(TOKEN_PROGRAM, struct.pack("<BQ", 7, units), [
        AccountMeta(mint, False, True), AccountMeta(token_account(dest_owner, mint), False, True),
        AccountMeta(authority, True, False)])


def balances(address):
    sol = rpc("getBalance", str(address))["value"] / 1e9
    try:
        usdt = int(rpc("getTokenAccountBalance", str(token_account(address, usdt_mint())))["value"]["amount"])
    except WalletError:             # no USDT account yet
        usdt = 0
    return sol, usdt / 10 ** DECIMALS


def check_address(text):
    """Customer's Solana wallet address -> Pubkey, or WalletError if it's not one."""
    try:
        pk = Pubkey.from_string(text.strip())
    except ValueError:
        raise WalletError(f"'{text}' is not a Solana address (TRON/BNB/ETH addresses won't work)")
    if not pk.is_on_curve():
        raise WalletError("That's a Solana token/program account, not a wallet address - ask for their wallet address")
    return pk


def check_funds(kp, amount):
    sol, usdt = balances(kp.pubkey())
    if usdt < amount:
        raise WalletError(f"Not enough USDT in the wallet: have {usdt:,.6f}, need {amount:,.6f}")
    if sol < MIN_SOL:
        raise WalletError(f"Not enough SOL for fees: have {sol:.6f}, need at least {MIN_SOL}")


def send_usdt(kp, dest, amount):
    """Send amount USDT to dest wallet. Returns the transaction signature."""
    units = int(round(amount * 10 ** DECIMALS))
    if units <= 0:
        raise WalletError("Amount too small to send")
    mint = usdt_mint()
    return send_tx([ix_open_account(kp.pubkey(), dest, mint), ix_transfer(kp.pubkey(), dest, mint, units)], [kp])


# ---------- wallet file ----------

def _fernet(password, salt):
    key = Scrypt(salt=salt, length=32, n=2 ** 15, r=8, p=1).derive(password.encode())
    return Fernet(base64.urlsafe_b64encode(key))


def address():
    if not KEY_FILE.exists():
        raise WalletError("No wallet yet - choose 4 in Prompt.bat (or run: python wallet.py new)")
    return Pubkey.from_string(json.loads(KEY_FILE.read_text())["address"])


def load():
    """Unlock the wallet with its password."""
    address()                       # stops here if there's no wallet yet
    data = json.loads(KEY_FILE.read_text())
    try:
        secret = _fernet(getpass.getpass("Wallet password: "), base64.b64decode(data["salt"])).decrypt(
            data["key"].encode())
    except InvalidToken:
        raise WalletError("Wrong wallet password")
    return Keypair.from_bytes(secret)


def new():
    if KEY_FILE.exists():
        raise WalletError(f"{KEY_FILE.name} already exists - not overwriting it")
    pw = getpass.getpass("Choose a wallet password (8+ characters): ")
    if len(pw) < 8:
        raise WalletError("Password too short")
    if getpass.getpass("Type it again: ") != pw:
        raise WalletError("Passwords don't match")
    kp, salt = Keypair(), os.urandom(16)
    KEY_FILE.write_text(json.dumps({
        "address": str(kp.pubkey()), "salt": base64.b64encode(salt).decode(),
        "key": _fernet(pw, salt).encrypt(bytes(kp)).decode()}, indent=2))
    print(f"Wallet created: {kp.pubkey()}")
    print(f"Back up {KEY_FILE.name} AND the password. Lose either one and the coins in it are gone.")


def setup_test():
    if NETWORK != "devnet":
        raise WalletError("setup-test only works on devnet (test money)")
    kp = load()
    me = kp.pubkey()
    if balances(me)[0] < 0.05:
        print("Asking the faucet for 1 free test SOL...")
        try:
            rpc("requestAirdrop", str(me), 1_000_000_000)
        except WalletError:
            raise WalletError(f"Get free test SOL first:\n  1. Open https://faucet.solana.com\n"
                              f"  2. Pick Devnet and paste this address: {me}\n"
                              f"  3. Ask for 1 SOL, then run this again.")
        for _ in range(30):
            time.sleep(2)
            if balances(me)[0] >= 0.05:
                break
        else:
            raise WalletError("Test SOL didn't arrive - try again, or use https://faucet.solana.com")
    units = 1000 * 10 ** DECIMALS
    if SOL.get("usdt_mint"):         # test USDT already exists: just print more
        mint = usdt_mint()
        sig = send_tx([ix_open_account(me, me, mint), ix_mint_to(mint, me, me, units)], [kp])
    else:                            # create our own test USDT token, then print 1,000 of it
        mint_kp = Keypair()
        mint = mint_kp.pubkey()
        rent = rpc("getMinimumBalanceForRentExemption", 82)
        sig = send_tx([
            create_account(CreateAccountParams(from_pubkey=me, to_pubkey=mint, lamports=rent, space=82,
                                               owner=TOKEN_PROGRAM)),
            Instruction(TOKEN_PROGRAM, struct.pack("<BB", 20, DECIMALS) + bytes(me) + bytes([0]),
                        [AccountMeta(mint, False, True)]),
            ix_open_account(me, me, mint), ix_mint_to(mint, me, me, units)], [kp, mint_kp])
        CONFIG["solana"]["usdt_mint"] = str(mint)
        CONFIG_PATH.write_text(json.dumps(CONFIG, indent=2), encoding="utf-8")
    print(f"Added 1,000 test USDT. Proof: {explorer(sig)}")


def main():
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else "balance").lower(), sys.argv[2:]
    if cmd == "new":
        new()
    elif cmd == "setup-test":
        setup_test()
    elif cmd == "send" and len(args) == 2:
        dest, amount = check_address(args[0]), float(args[1])
        kp = load()
        check_funds(kp, amount)
        print(f"Sending {amount} USDT to {dest}...")
        print(f"SENT. Proof: {explorer(send_usdt(kp, dest, amount))}")
    elif cmd == "balance":
        me = address()
        sol, usdt = balances(me)
        print(f"Wallet ({NETWORK}): {me}\n  SOL:  {sol:.6f}\n  USDT: {usdt:,.6f}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    try:
        main()
    except WalletError as e:
        sys.exit(str(e))
