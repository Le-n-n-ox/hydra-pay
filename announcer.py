"""Native counter announcements made by the computer running dashboard.py.

This deliberately does not use browser speech: browsers require a user gesture
before they are allowed to play sound.  On Windows, PowerShell's built-in SAPI
voice speaks from a background worker as soon as a payment is confirmed.
"""
import base64
import os
import queue
import subprocess
import threading


_messages = queue.Queue()
_started = False
_start_lock = threading.Lock()


def _enabled():
    """Allow a headless/cloud deployment to explicitly turn local speech off."""
    return os.getenv("COUNTER_VOICE_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _worker():
    while True:
        text = _messages.get()
        try:
            # Base64 keeps customer names out of a shell command and handles quotes safely.
            encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
            command = (
                "$text = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + encoded + "')); "
                "Add-Type -AssemblyName System.Speech; "
                "$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$voice.Rate = -1; $voice.Speak($text)"
            )
            subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except FileNotFoundError:
            # Cloud/Linux hosts have no Windows voice. Keep the payment flow unaffected.
            print("Counter voice is unavailable on this computer.")
        except Exception as exc:
            print(f"Counter voice error: {exc}")


def speak_payment_received(name, amount):
    """Queue one automatic announcement for a confirmed payment."""
    if not _enabled():
        return
    customer = " ".join(str(name or "a customer").split())
    try:
        value = int(round(float(amount)))
    except (TypeError, ValueError):
        value = 0
    unit = "shilling" if value == 1 else "shillings"

    global _started
    with _start_lock:
        if not _started:
            threading.Thread(target=_worker, name="counter-voice", daemon=True).start()
            _started = True
    _messages.put(f"Payment received from {customer}. {value:,} {unit}.")
