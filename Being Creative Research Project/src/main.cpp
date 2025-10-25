#include <Servo.h>
#include <Arduino.h>
#include <LiquidCrystal.h>

//------- inits ----------

#define BUFFER_SIZE 10
#define BUFFER_LOW_THRESHOLD 3

// Servo definitions
Servo shoulder_servo;
Servo elbow_servo;
Servo penup_servo;

float shoulder_currentAngle = 0;
float elbow_currentAngle = 0;

int SS_PIN = 9;
int ES_PIN = 10;
int PS_PIN = 11;

// LCD pins: RS, E, D4, D5, D6, D7
LiquidCrystal lcd(7, 8, 4, 5, 6, 3); // Adjust to your wiring

// Command buffer
String commandBuffer[BUFFER_SIZE];
int head = 0;  
int tail = 0;  
bool active = false;

// Line reader
char lineBuf[64];
size_t lineIdx = 0;

// Request throttling
unsigned long lastRequestMillis = 0;
const unsigned long REQUEST_INTERVAL_MS = 300;

// ----- Helper Functions -----
int buffer_count() {
  return (head - tail + BUFFER_SIZE) % BUFFER_SIZE;
}

bool buffer_is_empty() { return head == tail; }
bool buffer_is_full() { return ((head + 1) % BUFFER_SIZE) == tail; }
bool buffer_is_low() { return buffer_count() <= BUFFER_LOW_THRESHOLD; }

void buffer_push(const String &cmd) {
  if (!buffer_is_full()) {
    commandBuffer[head] = cmd;
    head = (head + 1) % BUFFER_SIZE;
  } else {
    Serial.println("BUFFER FULL");
    lcd.setCursor(0, 0);
    lcd.print("BUFFER FULL!    ");
  }
}

String buffer_pop() {
  String cmd = "";
  if (!buffer_is_empty()) {
    cmd = commandBuffer[tail];
    tail = (tail + 1) % BUFFER_SIZE;
  }
  return cmd;
}

void request_more_if_low() {
  if (buffer_is_low() && (millis() - lastRequestMillis) > REQUEST_INTERVAL_MS) {
    Serial.println("REQUEST");
    lcd.setCursor(0, 1);
    lcd.print("Buffer Low...   ");
    lastRequestMillis = millis();
  }
}

// Non-blocking serial line processor
void processSerialInput() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      if (lineIdx > 0) {
        lineBuf[lineIdx] = '\0';
        String s = String(lineBuf);
        s.trim();
        if (s.length() > 0) buffer_push(s);
        lineIdx = 0;
      }
    } else {
      if (lineIdx < sizeof(lineBuf) - 1) lineBuf[lineIdx++] = c;
      else lineIdx = 0; // overflow reset
    }
  }
}

// ----- Motion Functions -----
void pen_up() {
  penup_servo.write(0);
  delay(200);
  lcd.setCursor(0, 0);
  lcd.print("Pen Up          ");
}

void pen_down() {
  penup_servo.write(90);
  delay(200);
  lcd.setCursor(0, 0);
  lcd.print("Pen Down        ");
}

void move_to(float shoulder_dest, float elbow_dest) {
  shoulder_dest = constrain(shoulder_dest, 0, 180);
  elbow_dest = constrain(elbow_dest, 0, 180);

  float shoulder_start = shoulder_currentAngle;
  float elbow_start = elbow_currentAngle;

  float shoulder_dist = shoulder_dest - shoulder_start;
  float elbow_dist = elbow_dest - elbow_start;

  int steps = max(abs(shoulder_dist), abs(elbow_dist));
  if (steps == 0) return;

  float shoulder_step = shoulder_dist / steps;
  float elbow_step = elbow_dist / steps;

  for (int i = 1; i <= steps; i++) {
    shoulder_servo.write(shoulder_start + shoulder_step * i);
    elbow_servo.write(elbow_start + elbow_step * i);
    
    processSerialInput();
    request_more_if_low();
    delay(10);
  }

  shoulder_currentAngle = shoulder_dest;
  elbow_currentAngle = elbow_dest;

  lcd.setCursor(0, 0);
  lcd.print("Move Done       ");
}

// ----- Setup -----
void setup() {
  shoulder_servo.attach(SS_PIN);
  elbow_servo.attach(ES_PIN);
  penup_servo.attach(PS_PIN);

  Serial.begin(9600);
  lcd.begin(16, 2);
  lcd.setCursor(0, 0);
  lcd.print("Drawing Robot Ready");
  request_more_if_low();
}

// ----- Main Loop -----
void loop() {
  processSerialInput();
  request_more_if_low();

  if (!active && !buffer_is_empty()) {
    active = true;
    String cmd = buffer_pop();

    // Display command on LCD
    lcd.setCursor(0, 1);
    if (cmd.length() > 16) lcd.print(cmd.substring(0, 16));
    else lcd.print(cmd + "                "); // pad to clear old text

    if (cmd == "PEN UP") pen_up();
    else if (cmd == "PEN DOWN") pen_down();
    else if (cmd == "END") pen_up();
    else {
      int open = cmd.indexOf('(');
      int comma = cmd.indexOf(',');
      int close = cmd.indexOf(')');
      if (open >= 0 && comma > open && close > comma) {
        String sx = cmd.substring(open + 1, comma);
        String sy = cmd.substring(comma + 1, close);
        sx.trim(); sy.trim();
        float s = sx.toFloat();
        float e = sy.toFloat();
        if (!isnan(s) && !isnan(e)) move_to(s, e);
        else {
          Serial.println("Invalid numbers");
          lcd.setCursor(0, 0);
          lcd.print("Invalid numbers ");
        }
      } 
      else {
        Serial.println("Invalid format");
        lcd.setCursor(0, 0);
        lcd.print("Invalid format  ");
      }
    }
    active = false;
  }
}
