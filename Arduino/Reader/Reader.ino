// Copyright (c) 2016 William Connolly, Tyler Rocha, Justin Baiko

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights to
// use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
// the Software, and to permit persons to whom the Software is furnished to do so,
// subject to the following conditions:

// The above copyright notice and this permission notice shall be included in all copies
// or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
// PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
// FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
// ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

/* Arduino Reader Code */


#include <EEPROM.h>     // We are going to read and write PICC's UIDs from/to EEPROM
#include <SPI.h>        // RC522 Module uses SPI protocol
#include <MFRC522.h>    // Library for Mifare RC522 Devices
#include <AES.h>
#include <Wire.h>

#define COMMON_ANODE

#ifdef COMMON_ANODE
#define LED_ON LOW
#define LED_OFF HIGH
#else
#define LED_ON HIGH
#define LED_OFF LOW
#endif

#define RED_LED 7
#define BLUE_LED 6
#define GREEN_LED 5

#define TAMPER_PIN 2
int tamperState = 0;
unsigned long lastTamperMessage = 0;

#define relay 4     // Set Relay Pin
#define reset 3     // Button pin for reset button

#define MAGIC_NUMBER_LOCATION 0
#define SLAVE_ADDRESS_LOCATION 1
#define MAGIC_NUMBER 31
#define DEFAULT_SLAVE_ADDRESS 0x05

#define PIEZO_PIN 8

boolean sendSlaveAddressMessage = false;
boolean resetSlaveAddress = false;

int successRead;    // Variable integer to keep if we have Successful Read from Reader

byte storedCard[4];   // Stores an ID read from EEPROM
byte readCard[4];     // Stores scanned ID read from RFID Module
byte masterCard[4];   // Stores master card's ID read from EEPROM

/*
  We need to define MFRC522's pins and create instance
  Pin layout should be as follows (on Arduino Uno):
  MOSI: Pin 11 / ICSP-4
  MISO: Pin 12 / ICSP-1
  SCK : Pin 13 / ICSP-3
  SS : Pin 10 (Configurable)
  RST : Pin 9 (Configurable)
  look MFRC522 Library for
  other Arduinos' pin configuration 
 */

#define SS_PIN 10
#define RST_PIN 9
MFRC522 mfrc522(SS_PIN, RST_PIN); // Create MFRC522 instance.

AES aes;

enum SendMessageTypes{
  SendCardsRead = 0,
  DetectedTamper,
  AttemptedTamperResetFailed,
  EverythingOK,
  SlaveAddress
};

enum IncomingMessageStatus{
  Waiting = 0,
  NeedToProcess,
  Finished
};

enum LedSequences{
  Wait = 0,
  Red,
  Green,
  Blue,
  Yellow,
  Off
};

enum ToneSequences{
  No = 10,
  A,
  B,
  C,
  D,
};

int ledSeq[21];
int ledSeqIndex = 0;
unsigned long ledSeqMillis = 0;

int toneSeq[21];
int toneSeqIndex = 0;
unsigned long toneSeqMillis = 0;

bool tamper = false;

char messageToSend[32];
bool messageReady = false;

char messageToDecrypt[32];
int incomingMessageStatus = Waiting;

#define MAX_MESSAGE_QUEUE_LENGTH 5
char *messageQueue;
int messageQueueLength;

char *decryptQueue;
int decryptQueueLength;

boolean queueMessage(int messageType, byte *arguments, int argumentByteCount){
  char message[32];
  switch(messageType){
    case SendCardsRead:
      message[0] = 'S';
      message[1] = 'C';
      break;
    case DetectedTamper:
      message[0] = 'D';
      message[1] = 'T';
      break;
    case AttemptedTamperResetFailed:
      message[0] = 'R';
      message[1] = 'F';
      break;
    case EverythingOK:
      message[0] = 'O';
      message[1] = 'K';
      break;
    case SlaveAddress:
      message[0] = 'S';
      message[1] = 'A';
      break;
    default:
      return false;
  }

  for(int i = 0; i < 16; i++){
    if(i < argumentByteCount)
      message[i + 2] = arguments[i];
    else
      message[i + 2] = '0';
  }

  if(messageQueueLength <= 5){
    for(int i = 0; i < 32; i++){
      messageQueue[messageQueueLength * 32 + i] = message[i];
    }
    messageQueueLength++;

    return true;
  }else{
    return false;
  }
}

boolean dequeueMessageIfAvailable(){
  if(messageReady){
    //Serial.println(F("Message is still waiting to be sent. Can't dequeue new one."));
    return false;
  }else{
    if(messageQueueLength > 0){
      messageQueueLength--;

      // Dequeue message in slot 0
      unsigned char *message = (unsigned char *)malloc(16 * sizeof(unsigned char));
      for(int i = 0; i < 16; i++){
        message[i] = (unsigned char)messageQueue[i];
        Serial.print(message[i], HEX);
        Serial.print(" ");
      }

      Serial.println(" ");

      byte random_iv [N_BLOCK]; // maintain a copy that won't be altered by cbc_encrypt
      byte iv [N_BLOCK];
      byte cipher [4*N_BLOCK];
      
      for (byte i = 0 ; i < 16 ; i++){
        random_iv[i] = random(0, 255); // Generate a random byte for the Initialization Vector
        iv[i] = random_iv[i];
      }

      aes.cbc_encrypt(message, cipher, 1, iv); 

      for(int i = 0; i < 32; i++){
        if(i < 16){
          messageToSend[i] = (char)cipher[i];
        }else{
          messageToSend[i] = (char)random_iv[i - 16]; // copy the IV into the message
        }
      }

      // Move all messages down one slot
      for(int i = 0; i < 32 * messageQueueLength; i++){
        messageQueue[i] = messageQueue[i + 32];
      }

      messageReady = true;
      free(message);
      return true;
    }else{
      return false;
    }
  }
}

boolean decryptAndProcessMessage(){
  if(incomingMessageStatus == NeedToProcess){
    unsigned char *decrypt = (unsigned char *)malloc(16 * sizeof(unsigned char));
    for(int i = 1; i < 17; i++){
      decrypt[i-1] = (unsigned char)messageToDecrypt[i];
    }

    char new_iv[16];
    for(int i = 17; i < 32; i++){
      new_iv[i - 17] = (char)messageToDecrypt[i];
    }
    new_iv[15] = 'X';
    
    byte iv [N_BLOCK];
    byte plain [4*N_BLOCK];
    
    for (byte i = 0 ; i < 16 ; i++)
      iv[i] = new_iv[i];

    aes.cbc_decrypt(decrypt, plain, 1, iv); 
    Serial.println(" ");
    Serial.println("-- DECRYPTED MESSAGE:");
    char decryptedMessage[16];
    for(int i = 0; i < 16; i++){
      decryptedMessage[i] = (char)plain[i];
      Serial.print(plain[i], HEX);
      Serial.print(" ");
    }
    Serial.println(" ");

    if(decryptedMessage[0] == 'T' && decryptedMessage[1] == 'R'){
      Serial.println("Reset tamper status");
    }else if(decryptedMessage[0] == 'L' && decryptedMessage[1] == 'M'){
      Serial.println("Last message received correctly.");
    }else if(decryptedMessage[0] == 'R' && decryptedMessage[1] == 'S'){
      char status[2];
      status[0] = decryptedMessage[2];
      status[1] = decryptedMessage[3];
      Serial.print("Setting reader status: ");
    }else if(decryptedMessage[0] == 'C' && decryptedMessage[1] == 'M'){
      char messageType[2];
      messageType[0] = decryptedMessage[2];
      messageType[1] = decryptedMessage[3]; 

      Serial.print("Please resend message: ");
      Serial.print(messageType[0], HEX);
      Serial.println(messageType[1], HEX);
    }else if(decryptedMessage[0] == 'U' && decryptedMessage[1] == 'S'){
      Serial.println("Successfully signed in user.");
      int seq[] = {Green, Wait, Green, Wait, Green, Wait, Green, Wait, Green, Off};
      setLedSequence(seq, sizeof(seq) / sizeof(int));
      int tseq[] = {A, B, C, D, Off, Off, D, Off, Off, D, Off};
      setToneSequence(tseq, 11);
    }else if(decryptedMessage[0] == 'U' && decryptedMessage[1] == 'F'){
      Serial.println("Failed to sign in user.");
      int seq[] = {Red, Wait, Red, Wait, Red, Wait, Red, Wait, Red, Off};
      setLedSequence(seq, sizeof(seq) / sizeof(int));
      int tseq[] = {No, Off, Off, No, Off, Off, No, Off, Off, No, Off, Off, No, Off};
      setToneSequence(tseq, 14);    
    }else if(decryptedMessage[0] == 'S' && decryptedMessage[1] == 'A'){
      Serial.println("Set slave address.");
      unsigned char slaveAddress;
      slaveAddress = decryptedMessage[2];
      slaveAddress = slaveAddress - 48; // convert from char number to actual hex number

      if(slaveAddress > 4 && slaveAddress < 15){ // double check that the message is formed properly
        EEPROM.write(MAGIC_NUMBER_LOCATION, MAGIC_NUMBER);
        EEPROM.write(SLAVE_ADDRESS_LOCATION, slaveAddress);

        messageQueueLength = 0;
        queueMessage(SlaveAddress, &slaveAddress, 1);
        incomingMessageStatus = Finished;
        sendSlaveAddressMessage = true;
        free(decrypt);
        return true;
      }else{
        Serial.print("Given slave address is invalid. Slave address is: ");
        Serial.println(slaveAddress, HEX);
      }
    }

    if(messageQueueLength == 0)
      queueMessage(EverythingOK, NULL, 0);
      
    incomingMessageStatus = Finished;
    free(decrypt);
    return true;
  }else{
    return false;
  }
}

///////////////////////////////////////// Setup ///////////////////////////////////
void setup() {
  messageQueueLength = 0;
  decryptQueueLength = 0;
  messageQueue = (char *)malloc(sizeof(char) * 32 * MAX_MESSAGE_QUEUE_LENGTH);
  decryptQueue = (char *)malloc(sizeof(char) * 32 * MAX_MESSAGE_QUEUE_LENGTH);

  randomSeed(millis() % 512); // seed random with millis value, so that no two random patterns are repeated

  for(int i = 0; i < 32 * MAX_MESSAGE_QUEUE_LENGTH; i++){
    messageQueue[i] = '0';
    decryptQueue[i] = '0';
  }

  for(int i = 0; i < 21; i++){
    ledSeq[i] = -1;
    toneSeq[i] = -1;
  }

  //Arduino Pin Configuration
  pinMode(reset, INPUT_PULLUP);   // Enable pin's pull up resistor
  pinMode(relay, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);
  pinMode(TAMPER_PIN, INPUT);
  //Be careful how relay circuit behave on while resetting or power-cycling your Arduino
  digitalWrite(relay, HIGH);    // Make sure door is locked

  int slaveAddress = DEFAULT_SLAVE_ADDRESS;
  if(EEPROM.read(MAGIC_NUMBER_LOCATION) == MAGIC_NUMBER){
    slaveAddress = EEPROM.read(SLAVE_ADDRESS_LOCATION);
  }

  //Protocol Configuration
  Serial.begin(9600);  // Initialize serial communications with PC
  SPI.begin();           // MFRC522 Hardware uses SPI protocol
  mfrc522.PCD_Init();    // Initialize MFRC522 Hardware
  
  //If you set Antenna Gain to Max it will increase reading distance

  unsigned char facility_temp[20];

  unsigned char* password = (unsigned char *)"passwordpasswordpasswordpassword";
  aes.set_key(password, 256);
  
  Serial.println(F("Access Control v3.3"));   // For debugging purposes
  showReaderDetails();  // Show details of PCD - MFRC522 Card Reader details

  //Reset if Button Pressed while setup run (powered on) it wipes EEPROM
  if(digitalRead(reset) == LOW){  // when button pressed pin should get low, button connected to ground
    Serial.println(F("Reset Button Pressed"));
    Serial.println(F("You have 3 seconds to Cancel"));
    Serial.println(F("This will be remove all records and cannot be undone"));
    delay(3000);                        // Give user enough time to cancel operation
    if (digitalRead(reset) == LOW) {    // If button still be pressed, wipe EEPROM
      Serial.println(F("Starting Wiping EEPROM"));
      for (int x = 0; x < EEPROM.length(); x = x + 1) {    //Loop end of EEPROM address
        if (EEPROM.read(x) == 0) {              //If EEPROM address 0
          // do nothing, already clear, go to the next address in order to save time and reduce writes to EEPROM
        }
        else {
          EEPROM.write(x, 0);       // if not write 0 to clear, it takes 3.3mS
        }
      }
      Serial.println(F("EEPROM Successfully Wiped"));
    }
    else {
      Serial.println(F("Wiping Cancelled"));
    }
  }

  
  queueMessage(EverythingOK, NULL, 0);
  dequeueMessageIfAvailable();

  Wire.begin(slaveAddress);
  Wire.onReceive(receiveData);
  Wire.onRequest(sendData);
}

void receiveData(int byteCount){
  int i = 0;

  while(Wire.available() > 0){
    char c = Wire.read();
     messageToDecrypt[i++] = c;
  }
  
  if(i == 32){
    incomingMessageStatus = NeedToProcess;
  }
}

void sendData(){
  // Any call to delay(X) or aes.encrypt causes an IOError on the python side of things
  // I think there may be an issue with taking too much time to compute inside this callback. Or transferring control using the delay() method. 
  // Our workaround sets these flags, does the computation inside loop(), and continually sends the errorRetry message when the encryption hasn't yet been computed. 
  if(messageReady){
    Wire.write(messageToSend, 32);
    messageReady = false;
    //Serial.println("Incoming message status: Waiting");
    incomingMessageStatus = Waiting;

    if(sendSlaveAddressMessage == true){
      resetSlaveAddress = true;
      sendSlaveAddressMessage = false;
    }
  }else{
    //Serial.println("sending error retry");
    char errorRetry[] = {'1', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '1'};
    Wire.write(errorRetry, 32); 
    queueMessage(EverythingOK, NULL, 0);
  }
}

/* Led sequence: Array is size 21 to ensure even if we have a sequence of length 20, there is a -1 at the end.
 *  Sequence consists of a color or a wait command, Off is used to signify that we want the Led off at the end of the 
 *  sequence. Any sequence that doesn't end in Off will leave the last color on. For example, if we just want to set
 *  the Led to a color: setLedSequence({Yellow}, 1)
 *  or if we want to flash a color: setLedSequence({Red, Off}, 2)
 */

void setLedSequence(int sequence[], int count){
  if(count <= 20){
    ledSeqMillis = millis();
    ledSeqIndex = 0;
    for(int i = 0; i < 21; i++){
      if(i < count)
        ledSeq[i] = sequence[i];
      else
        ledSeq[i] = -1;
    }
  }else{
    Serial.println("Led sequence too long.");
  }
}

void executeLedSequence(){
  if(millis() - ledSeqMillis > 100){
    ledSeqMillis = millis();
    int which = ledSeq[ledSeqIndex];
    if(which != -1){ // -1 means stop sequence
      switch(which){
        case Wait:
          analogWrite(RED_LED, 0);
          analogWrite(GREEN_LED, 0);
          analogWrite(BLUE_LED, 0);
          break;
        case Red:
          analogWrite(RED_LED, 255);
          analogWrite(GREEN_LED, 0);
          analogWrite(BLUE_LED, 0);
          break;
        case Green:
          analogWrite(RED_LED, 0);
          analogWrite(GREEN_LED, 255);
          analogWrite(BLUE_LED, 0);
          break;
        case Blue:
          analogWrite(RED_LED, 0);
          analogWrite(GREEN_LED, 0);
          analogWrite(BLUE_LED, 255);
          break;
        case Yellow:
          analogWrite(RED_LED, 128);
          analogWrite(GREEN_LED, 128);
          analogWrite(BLUE_LED, 0);
          break;
        case Off:
          analogWrite(RED_LED, 0);
          analogWrite(GREEN_LED, 0);
          analogWrite(BLUE_LED, 0);
          break;
      }
      ledSeqIndex++;
    }
  }
}

void setToneSequence(int sequence[], int count){
  if(count <= 20){
    toneSeqMillis = millis();
    toneSeqIndex = 0;
    for(int i = 0; i < 21; i++){
      if(i < count)
        toneSeq[i] = sequence[i];
      else
        toneSeq[i] = -1;
    }
  }else{
    Serial.println("Tone sequence too long.");
  }
}

void executeToneSequence(){
  if(millis() - toneSeqMillis > 100){
    toneSeqMillis = millis();
    int which = toneSeq[toneSeqIndex];
    if(which != -1){ // -1 means stop sequence
      switch(which){
        case Wait:
          noTone(PIEZO_PIN);
          break;
        case No:
          tone(PIEZO_PIN, 100);
          break;
        case A:
          tone(PIEZO_PIN, 262);
          break;
        case B:
          tone(PIEZO_PIN, 294); //294
          break;
        case C:
          tone(PIEZO_PIN, 330); //330
          break;
        case D:
          tone(PIEZO_PIN, 349); //349
          break;
        case Off:
          noTone(PIEZO_PIN);
          break;
      }
      toneSeqIndex++;
    }
  }
}

///////////////////////////////////////// Main Loop ///////////////////////////////////
void loop () {
  if(resetSlaveAddress){
    if(EEPROM.read(MAGIC_NUMBER_LOCATION) == MAGIC_NUMBER){
      int slaveAddress = EEPROM.read(SLAVE_ADDRESS_LOCATION);
      Wire.begin(slaveAddress);
      resetSlaveAddress = false;
    }
  }
  executeLedSequence();
  executeToneSequence();
  tamperState = digitalRead(TAMPER_PIN);
  if(tamperState == LOW && millis() - lastTamperMessage > 5000){
    lastTamperMessage = millis();
    queueMessage(DetectedTamper, NULL, 0);
    int seq[] = {Red, Wait, Red, Wait, Red, Wait, Red, Wait, Red, Off};
    setLedSequence(seq, 10);
    Serial.println("Detected tamper!");
    int tseq[] = {No, Off, Off, No, Off, Off, No, Off, Off, No, Off, Off, No, Off};
    setToneSequence(tseq, 14);    
  }
  
  if(incomingMessageStatus == Finished)
    dequeueMessageIfAvailable();
  else if(incomingMessageStatus == NeedToProcess)
    decryptAndProcessMessage();
  
  successRead = getID();  // sets successRead to 1 when we get read from reader otherwise 0
  normalModeOn();
  
  if(successRead){  
    int seq[] = {Yellow};
    setLedSequence(seq, 1);
    int tseq[] = {C, D, Off};
    setToneSequence(tseq, 3);
    // This sequence should never actually complete, generally by the time a success or failure has been returned it will be overwritten.
    queueMessage(SendCardsRead, &readCard[0], 4);  
  }
}

///////////////////////////////////////// Get PICC's UID ///////////////////////////////////
int getID() {
  // Getting ready for Reading PICCs
  if ( ! mfrc522.PICC_IsNewCardPresent()) { //If a new PICC placed to RFID reader continue
    return 0;
  }
  if ( ! mfrc522.PICC_ReadCardSerial()) {   //Since a PICC placed get Serial and continue
    return 0;
  }
  // There are Mifare PICCs which have 4 byte or 7 byte UID care if you use 7 byte PICC
  // I think we should assume every PICC as they have 4 byte UID
  // Until we support 7 byte PICCs
  Serial.println(F("Scanned PICC's UID:"));
  for (int i = 0; i < 4; i++) {  //
    readCard[i] = mfrc522.uid.uidByte[i];
    Serial.print(readCard[i], HEX);
  }
  Serial.println("");
  mfrc522.PICC_HaltA(); // Stop reading
  return 1;
}

void showReaderDetails() {
  // Get the MFRC522 software version
  byte v = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
  Serial.print(F("MFRC522 Software Version: 0x"));
  Serial.print(v, HEX);
  if (v == 0x91)
    Serial.print(F(" = v1.0"));
  else if (v == 0x92)
    Serial.print(F(" = v2.0"));
  else
    Serial.print(F(" (unknown)"));
  Serial.println("");
  // When 0x00 or 0xFF is returned, communication probably failed
  if ((v == 0x00) || (v == 0xFF)) {
    Serial.println(F("WARNING: Communication failure, is the MFRC522 properly connected?"));
    while(true);  // do not go further
  }
}