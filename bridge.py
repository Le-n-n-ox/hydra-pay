"""Laptop bridge: reads card taps from the ESP32 over USB and sends them to the Hydra Pay cloud server.

Use this when the dashboard runs in the cloud (READER=bridge). The laptop only needs this script,
the ESP32 on USB and an internet connection.

Settings (in .env next to this file, or as environment variables):
  CLOUD_URL=https://your-app.example.com     the cloud server's address
  BRIDGE_TOKEN=...                           the same secret as BRIDGE_TOKEN on the server

Usage:  python bridge.py          (auto-detects the ESP32 port)
        python bridge.py COM6     (force a port)
"""
import os
import queue
import sys
import threading
import time
import uuid
from pathlib import Path

import requests
import serial
from serial.tools import list_ports

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env", override=False)
except ImportError:
    pass

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLOUD_URL = (os.getenv("CLOUD_URL") or "").strip().rstrip("/")
TOKEN = (os.getenv("BRIDGE_TOKEN") or "").strip()
BAUD = 115200
GIVE_UP_AFTER = 20      # seconds: a tap older than this is dropped, so nobody gets a late M-Pesa prompt
HEARTBEAT_EVERY = 10    # seconds

state = {"port": None, "connected": False, "message": "Searching for ESP32..."}
taps = queue.Queue()
http = requests.Session()
http.headers["Authorization"] = f"Bearer {TOKEN}"


def find_port():
    forced = [a for a in sys.argv[1:] if not a.startswith("--")]
    if forced:
        return forced[0]
    keys = ("cp210", "ch340", "ch910", "wch", "silicon labs", "usb serial", "usb-serial", "uart")
    for p in list_ports.comports():
        if any(k in f"{p.description} {p.manufacturer or ''}".lower() for k in keys):
            return p.device
    return None


def post(path, data, timeout=8):
    r = http.post(CLOUD_URL + path, json=data, timeout=timeout)
    if r.status_code == 403:
        raise PermissionError("the server rejected BRIDGE_TOKEN (check it matches the server)")
    r.raise_for_status()
    return r.json()


def sender():
    """Send taps in order; retry briefly on network errors, then give up."""
    while True:
        uid, tap_id, at = taps.get()
        while True:
            age = time.time() - at
            if age > GIVE_UP_AFTER:
                print(f"[TAP] {uid} dropped: could not reach the server for {GIVE_UP_AFTER}s")
                break
            try:
                post("/bridge/tap", {"uid": uid, "id": tap_id})
                print(f"[TAP] {uid} -> sent ({age:.1f}s)")
                break
            except PermissionError as e:
                print(f"[TAP] {uid} rejected: {e}")
                break
            except Exception as e:
                print(f"[TAP] {uid} retrying: {e.__class__.__name__}")
                time.sleep(1.5)


def heartbeat():
    """Tells the dashboard the reader is online, every few seconds."""
    warned = False
    while True:
        try:
            post("/bridge/status", state, timeout=6)
            if warned:
                print("Server reachable again")
            warned = False
        except Exception as e:
            if not warned:
                print(f"Can't reach {CLOUD_URL}: {e}")
            warned = True
        time.sleep(HEARTBEAT_EVERY)


def reader_loop():
    while True:
        port = find_port()
        if not port:
            state.update(port=None, connected=False, message="No ESP32 found - plug it in via USB")
            time.sleep(2)
            continue
        try:
            with serial.Serial(port, BAUD, timeout=1) as s:
                state.update(port=port, connected=True, message=f"Connected on {port} (laptop bridge)")
                print(f"Connected to ESP32 on {port}")
                while True:
                    line = s.readline().decode(errors="ignore").strip()
                    if line.startswith("UID:"):
                        uid = line[4:].strip().upper()
                        taps.put((uid, uuid.uuid4().hex, time.time()))
                    elif line:
                        print(f"[ESP32] {line}")
                        if line.startswith(("READY", "ERROR")):
                            state["message"] = f"{port}: {line}"
        except serial.SerialException as e:
            state.update(connected=False, message=f"Can't use {port} (close Arduino Serial Monitor?)")
            print(f"Serial problem on {port}: {e} - retrying...")
            time.sleep(2)


if __name__ == "__main__":
    if not CLOUD_URL or not TOKEN:
        print("Set CLOUD_URL and BRIDGE_TOKEN in .env (see docs/CLOUD_DEPLOY.md).")
        sys.exit(1)
    print(f"Hydra Pay bridge -> {CLOUD_URL}")
    threading.Thread(target=sender, daemon=True).start()
    threading.Thread(target=heartbeat, daemon=True).start()
    reader_loop()
