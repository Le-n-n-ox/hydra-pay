// ESP32 + RC522 RFID reader
// Prints "UID:XX XX XX XX" when a tag is placed and "REMOVED:..." when it leaves.
// The laptop dashboard (dashboard.py) reads these lines.

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  5   // RC522 SDA/SS
#define RST_PIN 22  // RC522 RST
#define LED_PIN 2   // ESP32 on-board LED (blinks on each scan)

MFRC522 rfid(SS_PIN, RST_PIN);
String activeUid = "";
unsigned long missingSince = 0;
const unsigned long REMOVE_DEBOUNCE_MS = 500;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  SPI.begin(18, 19, 23, SS_PIN);  // SCK, MISO, MOSI, SS
  rfid.PCD_Init();
  rfid.PCD_SetAntennaGain(rfid.RxGain_max);  // improves range on common RC522 clone boards
  delay(50);

  byte v = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (v == 0x00 || v == 0xFF) {
    Serial.println("ERROR: RC522 not found - check wiring");
  } else {
    Serial.print("READY: RC522 firmware 0x");
    Serial.println(v, HEX);
  }
}

void loop() {
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String uid = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
      if (rfid.uid.uidByte[i] < 0x10) uid += "0";
      uid += String(rfid.uid.uidByte[i], HEX);
      if (i < rfid.uid.size - 1) uid += " ";
    }
    uid.toUpperCase();

    // A card held on the reader is one presence, not repeated IN taps.
    if (uid != activeUid) {
      Serial.print("UID:");
      Serial.println(uid);
      digitalWrite(LED_PIN, HIGH);
      delay(150);
      digitalWrite(LED_PIN, LOW);
    }
    activeUid = uid;
    missingSince = 0;
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    return;
  }

  // Brief missed reads are common with RC522 clones; debounce removal so the
  // dashboard only receives OUT when the tag has really been removed.
  if (activeUid.length()) {
    if (!missingSince) missingSince = millis();
    if (millis() - missingSince >= REMOVE_DEBOUNCE_MS) {
      Serial.print("REMOVED:");
      Serial.println(activeUid);
      activeUid = "";
      missingSince = 0;
    }
  }
}
