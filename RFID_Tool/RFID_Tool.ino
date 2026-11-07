// ============================================================================
//  RFID_Tool - ESP32 + RC522 card reader/writer for the Arduino IDE
// ----------------------------------------------------------------------------
//  Open the Serial Monitor at 115200 baud (set line ending to "Newline").
//  Tap a card, then type a command and press Enter:
//
//     uid            - print just the UID of the card on the reader
//     dump           - print the WHOLE card: UID, type, and every block
//     read <blk>     - read one block (0-63), e.g.  read 1
//     write <blk> <text>  - write text to a data block, e.g.  write 1 HELLO
//     keys           - show the key being used
//     help           - show this list
//
//  Uses the default key FF FF FF FF FF FF (factory cards). Change DEFAULT_KEY
//  below if your cards use a different key.
//
//  Wiring (RC522 -> ESP32):
//     SDA/SS -> 5    SCK -> 18    MOSI -> 23    MISO -> 19    RST -> 22
//     3.3V  -> 3V3 (NOT 5V)       GND -> GND
//
//  Needs the "MFRC522" library (Sketch > Include Library > Manage Libraries).
// ============================================================================

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  5
#define RST_PIN 22
#define LED_PIN 2

MFRC522 rfid(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key DEFAULT_KEY = { {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF} };

String cmd = "";

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  SPI.begin(18, 19, 23, SS_PIN);   // SCK, MISO, MOSI, SS
  rfid.PCD_Init();
  delay(50);
  rfid.PCD_SetAntennaGain(rfid.RxGain_max);   // best range, helps clone chips

  byte v = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (v == 0x00 || v == 0xFF)
    Serial.println("ERROR: RC522 not found - check wiring");
  else {
    Serial.print("READY: RC522 firmware 0x");
    Serial.println(v, HEX);
  }
  printHelp();
}

// ---------------------------------------------------------------------------

void loop() {
  // 1. Auto-print the UID whenever a new card is tapped (like the old sketch).
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    Serial.print("UID:");
    Serial.println(uidString());
    blink();
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }

  // 2. Read a typed command from the Serial Monitor.
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      cmd.trim();
      if (cmd.length()) handleCommand(cmd);
      cmd = "";
    } else {
      cmd += c;
    }
  }
}

// ---------------------------------------------------------------------------
//  Commands
// ---------------------------------------------------------------------------

void handleCommand(String line) {
  String low = line;
  low.toLowerCase();

  if (low == "help") { printHelp(); return; }
  if (low == "keys") {
    Serial.print("Using key: ");
    for (byte i = 0; i < 6; i++) { print2(DEFAULT_KEY.keyByte[i]); Serial.print(' '); }
    Serial.println();
    return;
  }

  // every other command needs a card on the reader
  if (!selectCard()) { Serial.println("No card on the reader - tap one and retry."); return; }

  if (low == "uid") {
    Serial.print("UID: "); Serial.println(uidString());
  }
  else if (low == "dump") {
    rfid.PICC_DumpToSerial(&(rfid.uid));     // full card: UID, type, all blocks
    return;                                   // DumpToSerial already halts the card
  }
  else if (low.startsWith("read ")) {
    int blk = line.substring(5).toInt();
    readBlock(blk);
  }
  else if (low.startsWith("write ")) {
    int sp = line.indexOf(' ', 6);
    if (sp < 0) { Serial.println("Usage: write <block> <text>"); }
    else {
      int blk = line.substring(6, sp).toInt();
      String text = line.substring(sp + 1);
      writeBlock(blk, text);
    }
  }
  else {
    Serial.println("Unknown command. Type 'help'.");
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}

// ---------------------------------------------------------------------------
//  Block read / write (MIFARE Classic, default key A)
// ---------------------------------------------------------------------------

void readBlock(int blk) {
  if (blk < 0 || blk > 63) { Serial.println("Block must be 0-63."); return; }
  if (!authBlock(blk)) { Serial.println("Auth failed (wrong key or locked block)."); return; }

  byte buf[18];
  byte len = sizeof(buf);
  if (rfid.MIFARE_Read((byte)blk, buf, &len) != MFRC522::STATUS_OK) {
    Serial.println("Read failed."); return;
  }
  Serial.print("Block "); Serial.print(blk); Serial.print(": ");
  for (byte i = 0; i < 16; i++) { print2(buf[i]); Serial.print(' '); }
  Serial.print(" |");
  for (byte i = 0; i < 16; i++) Serial.print((buf[i] >= 32 && buf[i] < 127) ? (char)buf[i] : '.');
  Serial.println("|");
}

void writeBlock(int blk, String text) {
  if (blk < 0 || blk > 63) { Serial.println("Block must be 0-63."); return; }
  // guard rails: don't let a typo brick the card
  if (blk == 0) { Serial.println("Refusing: block 0 is the UID/manufacturer block."); return; }
  if ((blk + 1) % 4 == 0) { Serial.println("Refusing: that is a sector trailer (holds the keys)."); return; }

  byte data[16];
  for (byte i = 0; i < 16; i++) data[i] = (i < text.length()) ? text[i] : 0x00;

  if (!authBlock(blk)) { Serial.println("Auth failed (wrong key or locked block)."); return; }
  if (rfid.MIFARE_Write((byte)blk, data, 16) != MFRC522::STATUS_OK) {
    Serial.println("Write failed."); return;
  }
  Serial.print("Wrote block "); Serial.print(blk); Serial.print(": \"");
  Serial.print(text); Serial.println("\"");
  readBlock(blk);   // read it back to prove it stuck
}

bool authBlock(int blk) {
  return rfid.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A,
                               (byte)blk, &DEFAULT_KEY, &(rfid.uid)) == MFRC522::STATUS_OK;
}

// ---------------------------------------------------------------------------
//  Helpers
// ---------------------------------------------------------------------------

bool selectCard() {
  // Wake a card that may already be sitting on the reader.
  return (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) ||
         (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial());
}

String uidString() {
  String s = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) s += "0";
    s += String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1) s += " ";
  }
  s.toUpperCase();
  return s;
}

void print2(byte b) { if (b < 0x10) Serial.print('0'); Serial.print(b, HEX); }

void blink() { digitalWrite(LED_PIN, HIGH); delay(120); digitalWrite(LED_PIN, LOW); }

void printHelp() {
  Serial.println();
  Serial.println("Commands (tap a card first, Serial Monitor set to 'Newline'):");
  Serial.println("  uid                  - print the UID");
  Serial.println("  dump                 - print the whole card (all blocks)");
  Serial.println("  read <blk>           - read one block, e.g. read 1");
  Serial.println("  write <blk> <text>   - write text to a block, e.g. write 1 HELLO");
  Serial.println("  keys                 - show the key in use");
  Serial.println("  help                 - this list");
  Serial.println();
}
