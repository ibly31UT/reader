#include "SoftwareSerial.h"

//SoftwareSerial rfid = SoftwareSerial(5, 4);

typedef struct {
  long facility;
  long card;
  int bits;
} credential_t;

const int authorized[][2] = {
  {3, 1337}
};

credential_t credential;

int wiegand[64];
int wiegand_idx, waiting;

void decode35() {
  int i;
  long facility = 0, card = 0;
  
  for (i = 2; i < 14; i++) {
    facility |= (wiegand[i] << (13-i));
  }
  
  for (i = 14; i < 34; i++) {
    card |= ((long)wiegand[i] << (33-i));
  }
  
  credential.facility = facility;
  credential.card = card;
  credential.bits = 35;
}

void decode26() {
  int i;
  long facility = 0, card = 0;
  
  for (i = 1; i < 9; i++) {
    facility |= (wiegand[i] << (8-i));
  }
  
  for (i = 9; i < 25; i++) {
    card |= ((long)wiegand[i] << (24-i));
  }
  
  credential.facility = facility;
  credential.card = card;
  credential.bits = 26;
}

void decode(int len) {
  switch(len) {
    case 26: decode26(); break;
    case 35: decode35(); break;
  } 
}

void data0() {
  cli();
  wiegand[wiegand_idx++] = 0;
  waiting = 10000;
  //Serial.print("0");

  sei();
}

void data1() {
  cli();
  wiegand[wiegand_idx++] = 1;
  waiting = 10000;
  //Serial.print("1");

  sei();
}

void setup() {
  wiegand_idx = 0;

  pinMode(2, INPUT);
  pinMode(3, INPUT);
  
  Serial.begin(9600);
  Serial.write(0x16);
  Serial.write(0x11);
  Serial.write(0x0C);
  delay(5);
  Serial.print("Initialzing..");

  Serial.write(0x16);
  Serial.write(0x11);
  Serial.write(0x0C);
  
  Serial.println("Scan card..."); 
  delay(1000);

  attachInterrupt(digitalPinToInterrupt(3), data0, LOW);
  attachInterrupt(digitalPinToInterrupt(2), data1, LOW);
}

void loop() {
  // put your main code here, to run repeatedly:
  if(!waiting && wiegand_idx){
    decode(wiegand_idx);
    wiegand_idx = 0;
    Serial.write(0x0C);
    Serial.print("Found card!");
    delay(1000);
  }else if (waiting) {
    waiting--;
  }
  
}
