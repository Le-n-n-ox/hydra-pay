# Runs on the ESP32 at boot. Prints "UID:XX XX XX XX" for each card tap.
# Wiring: SDA->5  SCK->18  MOSI->23  MISO->19  RST->22  3.3V->3V3  GND->GND
import time
from machine import Pin, SPI
from mfrc522 import MFRC522

led = Pin(2, Pin.OUT, value=0)
spi = SPI(2, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))

while True:
    rdr = MFRC522(spi, cs=5, rst=22)
    v = rdr.version()
    if v not in (0x00, 0xFF):
        print("READY: RC522 firmware 0x%02X" % v)
        break
    print("ERROR: RC522 not found - check wiring")
    time.sleep(3)

last_uid = None
last_seen = 0

while True:
    uid = rdr.read_uid()
    now = time.ticks_ms()
    if uid:
        # holding a card on the reader counts as one tap
        if uid != last_uid or time.ticks_diff(now, last_seen) > 1500:
            print("UID:" + uid)
            led.value(1)
            time.sleep_ms(150)
            led.value(0)
        last_uid = uid
        last_seen = time.ticks_ms()
    time.sleep_ms(50)
