"""Diagnostic: reset RC522 cleanly and show request/anticoll status. python tools/probe.py COM7"""
import sys, time, serial
PORT = sys.argv[1] if len(sys.argv) > 1 else "COM7"
DEVICE = r'''
import time
from machine import Pin, SPI
from mfrc522 import MFRC522
spi = SPI(2, baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
r = MFRC522(spi, cs=5, rst=22)
r.init()
r._sflags(0x14, 0x03)          # force antenna ON
print("VER %02X  TXCTRL %02X" % (r.version(), r._rreg(0x14)))
print("WAITING")
done = False
for _ in range(300):
    stat, bits = r.request(r.REQALL)
    if stat == r.OK:
        s2, raw = r.anticoll()
        print("REQ ok bits=%d  ANTICOLL stat=%d  raw=%s" % (bits, s2, " ".join("%02X" % b for b in raw)))
        done = True
        break
    time.sleep_ms(100)
if not done:
    print("NOREQ last_stat=%d bits=%d" % (stat, bits))
print("DONE")
'''
s = serial.Serial(PORT, 115200, timeout=1)
time.sleep(0.3); s.write(b"\x03\x03"); time.sleep(0.3); s.reset_input_buffer()
s.write(b"\x01"); time.sleep(0.3); s.read(s.in_waiting or 1)
s.write(DEVICE.encode() + b"\x04"); time.sleep(0.3)
out = bytearray(); end = time.time() + 35
while time.time() < end and b"DONE" not in out:
    c = s.read(s.in_waiting or 1)
    out += c if c else b""
    if not c: time.sleep(0.05)
s.write(b"\x02"); s.close()
print(out.decode("utf-8", "replace").strip())
