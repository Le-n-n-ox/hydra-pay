"""Host-side: push a MIFARE reader into the ESP32 REPL over serial and dump a tag's blocks.
Usage: python tools/dump_tag.py COM7
Reuses the mfrc522 driver already on the board; adds authenticate + read-block on top.
"""
import sys
import time
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM7"

# Program that runs ON the ESP32. Reads a MIFARE Classic 1K/4K tag (default keys).
DEVICE = r'''
import time
from machine import Pin, SPI
from mfrc522 import MFRC522
spi = SPI(2, baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
r = MFRC522(spi, cs=5, rst=22)
KEYS = [b"\xff"*6, bytes((0xA0,0xA1,0xA2,0xA3,0xA4,0xA5)), bytes((0xD3,0xF7,0xD3,0xF7,0xD3,0xF7)), b"\x00"*6]

def crc(data):
    r._cflags(0x05, 0x04)
    r._wreg(0x0A, 0x80)
    for c in data:
        r._wreg(0x09, c)
    r._wreg(0x01, 0x03)
    for _ in range(255):
        if r._rreg(0x05) & 0x04:
            break
    return [r._rreg(0x22), r._rreg(0x21)]

def select():
    r._cflags(0x08, 0x08)
    if r.request(r.REQALL)[0] != r.OK:
        return None
    stat, raw = r.anticoll()
    if stat != r.OK:
        return None
    r._wreg(0x0D, 0x00)
    sel = [0x93, 0x70] + list(raw)
    stat, resp, _ = r._tocard(0x0C, sel + crc(sel))
    sak = resp[0] if resp else None
    return raw[:4], sak

def auth(block, key, uid):
    stat, _, _ = r._tocard(0x0E, [0x60, block] + list(key) + list(uid))
    return bool(r._rreg(0x08) & 0x08)

def read_block(block):
    stat, recv, _ = r._tocard(0x0C, [0x30, block] + crc([0x30, block]))
    return recv[:16] if stat == r.OK and len(recv) >= 16 else None

print("GO")
sel = None
for _ in range(400):          # wait ~40 s for a tag to appear
    sel = select()
    if sel:
        break
    time.sleep_ms(100)
if not sel:
    print("NOTAG")
else:
    uid, sak = sel
    print("UID " + " ".join("%02X" % b for b in uid))
    print("SAK %02X" % (sak if sak is not None else 0))
    for blk in range(64):
        got = None
        usedkey = None
        for k in KEYS:
            s = select()
            if not s:
                continue
            if auth(blk, k, s[0]):
                got = read_block(blk)
                if got is not None:
                    usedkey = k
                    break
        if got is None:
            print("B%02d LOCKED" % blk)
        else:
            hx = " ".join("%02X" % b for b in got)
            asc = "".join((chr(b) if 32 <= b < 127 else ".") for b in got)
            print("B%02d %s |%s| key=%s" % (blk, hx, asc, " ".join("%02X" % b for b in usedkey)))
    r._cflags(0x08, 0x08)
print("DONE")
'''


def main():
    s = serial.Serial(PORT, 115200, timeout=1)
    time.sleep(0.3)
    s.write(b"\x03\x03")          # Ctrl-C twice: stop whatever is running
    time.sleep(0.3)
    s.reset_input_buffer()
    s.write(b"\x01")              # Ctrl-A: enter raw REPL
    time.sleep(0.3)
    s.read(s.in_waiting or 1)
    s.write(DEVICE.encode() + b"\x04")   # program + Ctrl-D to execute
    time.sleep(0.3)

    out = bytearray()
    deadline = time.time() + 120     # up to 2 min: you have time to place the tag
    saw_done = False
    while time.time() < deadline and not saw_done:
        chunk = s.read(s.in_waiting or 1)
        if chunk:
            out += chunk
            if b"DONE" in out:
                saw_done = True
        else:
            time.sleep(0.05)
    s.write(b"\x02")             # Ctrl-B: back to normal REPL
    s.close()

    text = out.decode("utf-8", "replace")
    for line in text.splitlines():
        line = line.strip()
        if line and line not in ("OK", ">", "GO") and not line.startswith("\x04"):
            print(line)


if __name__ == "__main__":
    main()
