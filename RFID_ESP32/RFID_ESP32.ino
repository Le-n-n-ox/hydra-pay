// ESP32 + RC522 RFID reader
// Prints "UID:XX XX XX XX" over USB serial each time a card/tag is tapped.
// The laptop dashboard (dashboard.py) reads these lines.

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  5   // RC522 SDA/SS
#define RST_PIN 22  // RC522 RST
#define LED_PIN 2   // ESP32 on-board LED (blinks on each scan)

MFRC522 rfid(SS_PIN, RST_PIN);
String lastUid = "";
unsigned long lastTime = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  SPI.begin(18, 19, 23, SS_PIN);  // SCK, MISO, MOSI, SS
  rfid.PCD_Init();
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
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;

  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1) uid += " ";
  }
  uid.toUpperCase();

  // ignore the same card re-read within 2 seconds
  if (uid != lastUid || millis() - lastTime > 2000) {
    Serial.print("UID:");
    Serial.println(uid);
    digitalWrite(LED_PIN, HIGH);
    delay(150);
    digitalWrite(LED_PIN, LOW);
  }
  lastUid = uid;
  lastTime = millis();

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}
