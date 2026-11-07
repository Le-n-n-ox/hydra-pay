"""Dump a MIFARE tag from a pristine board state.
Moves main.py aside, soft-resets (bare REPL), reads the tag, then always restores main.py.
Usage: python tools/dump_clean.py COM7
"""
import sys, time, serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM7"

READER = r'''
import time
from machine import Pin, SPI
from mfrc522 import MFRC522
spi = SPI(2, baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
r = MFRC522(spi, cs=5, rst=22)
KEYS = [b"\xff"*6, bytes((0xA0,0xA1,0xA2,0xA3,0xA4,0xA5)), bytes((0xD3,0xF7,0xD3,0xF7,0xD3,0xF7)), b"\x00"*6]
def crc(d):
    r._cflags(0x05,0x04); r._wreg(0x0A,0x80)
    for c in d: r._wreg(0x09,c)
    r._wreg(0x01,0x03)
    for _ in range(255):
        if r._rreg(0x05)&0x04: break
    return [r._rreg(0x22), r._rreg(0x21)]
def select():
    r._cflags(0x08,0x08)
    if r.request(r.REQALL)[0]!=r.OK: return None
    st,raw=r.anticoll()
    if st!=r.OK: return None
    r._wreg(0x0D,0x00); sel=[0x93,0x70]+list(raw)
    st,resp,_=r._tocard(0x0C, sel+crc(sel))
    return raw[:4], (resp[0] if resp else 0)
def auth(b,k,u):
    r._tocard(0x0E,[0x60,b]+list(k)+list(u)); return bool(r._rreg(0x08)&0x08)
def rdblk(b):
    st,rc,_=r._tocard(0x0C,[0x30,b]+crc([0x30,b]))
    return rc[:16] if st==r.OK and len(rc)>=16 else None
print("GO")
sel=None
for _ in range(400):
    sel=select()
    if sel: break
    time.sleep_ms(100)
if not sel:
    print("NOTAG")
else:
    uid,sak=sel
    print("UID "+" ".join("%02X"%b for b in uid))
    print("SAK %02X"%sak)
    for blk in range(64):
        got=None; uk=None
        for k in KEYS:
            s=select()
            if not s: continue
            if auth(blk,k,s[0]):
                got=rdblk(blk)
                if got is not None: uk=k; break
        if got is None:
            print("B%02d LOCKED"%blk)
        else:
            hx=" ".join("%02X"%b for b in got)
            asc="".join((chr(b) if 32<=b<127 else ".") for b in got)
            print("B%02d %s |%s| key=%s"%(blk,hx,asc," ".join("%02X"%b for b in uk)))
    r._cflags(0x08,0x08)
print("DONE")
'''


def raw_enter(s):
    s.write(b"\x03\x03"); time.sleep(0.2); s.reset_input_buffer()
    s.write(b"\x01"); time.sleep(0.2); s.read(s.in_waiting or 1)


def raw_exec(s, code, wait_token=b"OK", timeout=6):
    s.write(code.encode() + b"\x04")
    end = time.time() + timeout
    buf = bytearray()
    while time.time() < end:
        c = s.read(s.in_waiting or 1)
        if c:
            buf += c
            if b"\x04>" in buf:
                break
        else:
            time.sleep(0.03)
    return buf.decode("utf-8", "replace")


def main():
    s = serial.Serial(PORT, 115200, timeout=1)
    time.sleep(0.3)
    raw_enter(s)
    # 1. move main.py aside
    raw_exec(s, "import os\ntry:\n os.rename('main.py','main.off')\n print('MOVED')\nexcept Exception as e:\n print('MV',e)")
    # 2. soft reset -> pristine board, no firmware loop
    s.write(b"\x04")              # Ctrl-D in raw REPL soft-reboots
    time.sleep(1.5)
    s.reset_input_buffer()
    try:
        # 3. pristine state: enter raw REPL and run the reader
        raw_enter(s)
        s.write(READER.encode() + b"\x04")
        time.sleep(0.3)
        out = bytearray(); end = time.time() + 60
        while time.time() < end and b"DONE" not in out:
            c = s.read(s.in_waiting or 1)
            out += c if c else b""
            if not c: time.sleep(0.05)
        print("----- TAG DUMP -----")
        for ln in out.decode("utf-8", "replace").splitlines():
            ln = ln.strip()
            if ln and ln not in ("OK", ">") and not ln.startswith("\x04"):
                print(ln)
    finally:
        # 4. always restore main.py
        raw_enter(s)
        r = raw_exec(s, "import os\ntry:\n os.rename('main.off','main.py')\n print('RESTORED')\nexcept Exception as e:\n print('RS',e)")
        print("restore:", "RESTORED" if "RESTORED" in r else r.strip()[-60:])
        s.write(b"\x02"); s.close()


if __name__ == "__main__":
    main()
