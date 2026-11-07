"""Change a magic MIFARE Classic's UID (block 0). User's own dev cards.
Reads + backs up the old block 0, writes the new one, verifies. Non-magic cards reject the
write and are left untouched. Restores main.py on exit.
Usage: python tools/setuid.py COM7 2C890270
"""
import sys, time, serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM7"
TARGET_HEX = (sys.argv[2] if len(sys.argv) > 2 else "2C890270").replace(" ", "")
TARGET = [int(TARGET_HEX[i:i+2], 16) for i in range(0, 8, 2)]
BCC = TARGET[0] ^ TARGET[1] ^ TARGET[2] ^ TARGET[3]

DEVICE = r'''
import time
from machine import Pin, SPI
from mfrc522 import MFRC522
spi = SPI(2, baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
r = MFRC522(spi, cs=5, rst=22)
OK = r.OK
TARGET = __TARGET__
BCC = __BCC__

def crc(d):
    r._cflags(0x05, 0x04); r._wreg(0x0A, 0x80)
    for c in d: r._wreg(0x09, c)
    r._wreg(0x01, 0x03)
    for _ in range(255):
        if r._rreg(0x05) & 0x04: break
    return [r._rreg(0x22), r._rreg(0x21)]

def tx(data, bits=0):
    r._wreg(0x0D, bits)
    return r._tocard(0x0C, data)

def halt():
    tx([0x50, 0x00] + crc([0x50, 0x00]))

def select():
    r._cflags(0x08, 0x08); halt()
    if r.request(r.REQALL)[0] != OK: return None
    st, raw = r.anticoll()
    if st != OK: return None
    sel = [0x93, 0x70] + list(raw)
    st, resp, _ = tx(sel + crc(sel))
    return raw[:4], (resp[0] if resp else 0)

def auth(block, uid, key=b"\xff"*6):
    r._tocard(0x0E, [0x60, block] + list(key) + list(uid))
    return bool(r._rreg(0x08) & 0x08)

def read_block(block):
    for _ in range(12):               # beat the clone-chip read glitch
        if not select(): continue
        if auth(block, select_uid):
            st, rc, _ = tx([0x30, block] + crc([0x30, block]))
            if st == OK and len(rc) >= 16: return rc[:16]
    return None

def ack(res):
    st, rc, bits = res
    return st == OK and bits == 4 and (rc[0] & 0x0F) == 0x0A

def write_gen2(block, data):          # normal auth + write (gen2 / CUID magic)
    if not select(): return False
    if not auth(0, select_uid): return False
    if not ack(tx([0xA0, block] + crc([0xA0, block]))): return False
    return ack(tx(list(data) + crc(list(data))))

def write_gen1a(block, data):         # backdoor unlock, no auth (gen1a magic)
    r._cflags(0x08, 0x08); halt()
    if not ack(tx([0x40], 7)): return False      # 7-bit 0x40
    if not ack(tx([0x43])): return False         # 0x43
    if not ack(tx([0xA0, block] + crc([0xA0, block]))): return False
    return ack(tx(list(data) + crc(list(data))))

print("GO")
sel = None
for _ in range(400):
    sel = select()
    if sel: break
    time.sleep_ms(100)
if not sel:
    print("NOTAG"); print("DONE")
else:
    select_uid, sak = sel
    print("OLD_UID " + " ".join("%02X" % b for b in select_uid))
    old0 = read_block(0)
    if old0 is None:
        print("READ0_FAIL")
    else:
        print("OLD_B0 " + " ".join("%02X" % b for b in old0))
    tail = old0[5:16] if old0 else [0x08, 0x04, 0x00, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69]
    newb0 = TARGET + [BCC] + list(tail)
    print("NEW_B0 " + " ".join("%02X" % b for b in newb0))
    ok = write_gen2(0, newb0)
    mode = "gen2"
    if not ok:
        ok = write_gen1a(0, newb0)
        mode = "gen1a"
    print("WRITE %s %s" % (mode, "OK" if ok else "FAIL"))
    time.sleep_ms(200)
    v = select()
    print("VERIFY " + (" ".join("%02X" % b for b in v[0]) if v else "NONE"))
    print("DONE")
'''
DEVICE = DEVICE.replace("__TARGET__", repr(TARGET)).replace("__BCC__", str(BCC))


def raw_enter(s):
    s.write(b"\x03\x03"); time.sleep(0.2); s.reset_input_buffer()
    s.write(b"\x01"); time.sleep(0.2); s.read(s.in_waiting or 1)


def raw_exec(s, code, timeout=6):
    s.write(code.encode() + b"\x04")
    end = time.time() + timeout; buf = bytearray()
    while time.time() < end:
        c = s.read(s.in_waiting or 1)
        if c:
            buf += c
            if b"\x04>" in buf: break
        else:
            time.sleep(0.03)
    return buf.decode("utf-8", "replace")


def main():
    s = serial.Serial(PORT, 115200, timeout=1); time.sleep(0.3)
    raw_enter(s)
    raw_exec(s, "import os\ntry:\n os.rename('main.py','main.off')\nexcept Exception as e:\n print(e)")
    s.write(b"\x04"); time.sleep(1.5); s.reset_input_buffer()
    try:
        raw_enter(s)
        s.write(DEVICE.encode() + b"\x04"); time.sleep(0.3)
        out = bytearray(); end = time.time() + 60
        while time.time() < end and b"DONE" not in out:
            c = s.read(s.in_waiting or 1)
            out += c if c else b""
            if not c: time.sleep(0.05)
        print("----- SET UID -----")
        for ln in out.decode("utf-8", "replace").splitlines():
            ln = ln.strip()
            if ln and ln not in ("OK", ">") and not ln.startswith("\x04"):
                print(ln)
    finally:
        raw_enter(s)
        raw_exec(s, "import os\ntry:\n os.rename('main.off','main.py')\n print('RESTORED')\nexcept Exception as e:\n print(e)")
        s.write(b"\x02"); s.close()


if __name__ == "__main__":
    main()
