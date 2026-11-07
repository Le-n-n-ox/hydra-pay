# Minimal MFRC522 (RC522) driver for MicroPython - reads card UIDs.
import time
from machine import Pin


class MFRC522:
    OK = 0
    NOTAGERR = 1
    ERR = 2
    REQIDL = 0x26
    REQALL = 0x52   # also wakes a card left half-read by a failed attempt

    def __init__(self, spi, cs, rst):
        self.spi = spi
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.rst = Pin(rst, Pin.OUT, value=0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(50)
        self.init()

    def _wreg(self, reg, val):
        self.cs.value(0)
        self.spi.write(bytes([(reg << 1) & 0x7E, val]))
        self.cs.value(1)

    def _rreg(self, reg):
        self.cs.value(0)
        self.spi.write(bytes([((reg << 1) & 0x7E) | 0x80]))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def _sflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tocard(self, cmd, send):
        recv = []
        bits = n = 0
        stat = self.ERR
        irq_en, wait_irq = (0x77, 0x30) if cmd == 0x0C else (0x12, 0x10)

        self._wreg(0x02, irq_en | 0x80)
        self._cflags(0x04, 0x80)
        self._sflags(0x0A, 0x80)
        self._wreg(0x01, 0x00)
        for c in send:
            self._wreg(0x09, c)
        self._wreg(0x01, cmd)
        if cmd == 0x0C:
            self._sflags(0x0D, 0x80)

        i = 2000
        while True:
            n = self._rreg(0x04)
            i -= 1
            if i == 0 or (n & 0x01) or (n & wait_irq):
                break
        self._cflags(0x0D, 0x80)

        if i:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                stat = self.OK
                if n & irq_en & 0x01:
                    stat = self.NOTAGERR
                elif cmd == 0x0C:
                    n = self._rreg(0x0A)
                    lbits = self._rreg(0x0C) & 0x07
                    bits = (n - 1) * 8 + lbits if lbits else n * 8
                    n = min(max(n, 1), 16)
                    for _ in range(n):
                        recv.append(self._rreg(0x09))
        return stat, recv, bits

    def init(self):
        self._wreg(0x01, 0x0F)  # soft reset
        time.sleep_ms(50)
        self._wreg(0x2A, 0x8D)
        self._wreg(0x2B, 0x3E)
        self._wreg(0x2D, 30)
        self._wreg(0x2C, 0)
        self._wreg(0x15, 0x40)
        self._wreg(0x11, 0x3D)
        self._wreg(0x26, 0x70)  # max receiver gain (48 dB) - better range, esp. on clone chips
        if not (self._rreg(0x14) & 0x03):
            self._sflags(0x14, 0x03)  # antenna on

    def version(self):
        return self._rreg(0x37)

    def request(self, mode=REQIDL):
        self._wreg(0x0D, 0x07)
        stat, recv, bits = self._tocard(0x0C, [mode])
        if stat != self.OK or bits != 0x10:
            stat = self.ERR
        return stat, bits

    def anticoll(self):
        self._wreg(0x0D, 0x00)
        self._cflags(0x0E, 0x80)  # clear ValuesAfterColl
        stat, recv, bits = self._tocard(0x0C, [0x93, 0x20])
        if stat == self.OK:
            if len(recv) == 5:
                chk = 0
                for i in range(4):
                    chk ^= recv[i]
                if chk != recv[4]:
                    stat = self.ERR
            else:
                stat = self.ERR
        return stat, recv

    def read_uid(self):
        """Return UID as 'XX XX XX XX' or None."""
        for _ in range(3):   # a card is present but the read glitched: retry right away
            stat, _ = self.request(self.REQALL)
            if stat != self.OK:
                return None
            stat, raw = self.anticoll()
            if stat == self.OK:
                return " ".join("%02X" % b for b in raw[:4])
        return None
