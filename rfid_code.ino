#include <SPI.h>
#include <RFID.h>

int green_LED = 5;
int yellow_LED = 3;
int sda_pin = 10;
int rst_pin = 9;
RFID rfid(sda_pin, rst_pin);

// store value for previous read to check if card has been removed
bool prev_read = false;
int prev_read_val = -1;

unsigned char status;
unsigned char card_data[MAX_LEN]; // MAX_LEN is 16
bool green_on = false;
// variable to update yellow LED from python script
int yellow_on = 0;

void setup() {
  // Initialization
  Serial.begin(9600);
  SPI.begin();
  rfid.init();
  pinMode(green_LED, OUTPUT); // set LED to output mode
  pinMode(yellow_LED, OUTPUT);
}

void loop() {
  // Search for card and return number
  delay(100);
  if (prev_read == false) {
    if (rfid.findCard(PICC_REQIDL, card_data) == MI_OK) {
      // turn on LED when card is in range
      prev_read = true;
      if (green_on == false) {
        digitalWrite(green_LED, HIGH);
        green_on = true;
      }
      // read card number
      if ((rfid.anticoll(card_data) == MI_OK) && (prev_read_val != 1)) {
        for (int i = 0; i < 4; i++) {
          Serial.print(0x0F & (card_data[i] >> 4), HEX);
          Serial.print(0x0F & card_data[i], HEX);
        }
        Serial.println("");
        prev_read_val = 1;
      }
      rfid.selectTag(card_data);
      // check yellow led status
      while (Serial.available()) {
        yellow_on = Serial.read();
        if (yellow_on == 49) { // 49 is the encoding for "1"
          digitalWrite(yellow_LED, HIGH);
        }
        else {
          digitalWrite(yellow_LED, LOW);
        }
      }
    }
    else if (prev_read_val != 0) {
      Serial.println("No card in range");
      // turn off LED when card is not in range
      if (green_on == true) {
        digitalWrite(green_LED, LOW);
        digitalWrite(yellow_LED, LOW);
        green_on = false;
      }
      prev_read_val = 0;
    }
  }
  else {
    // second read always misses the card, even when it's there
    // so ignore that read here
    rfid.findCard(PICC_REQIDL, card_data);
    prev_read = false;
  } 
}
  
