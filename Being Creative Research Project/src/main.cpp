#include <Servo.h>
#include <Arduino.h>

//------- inits ----------

#define BUFFER_SIZE 10
#define BUFFER_LOW_THRESHOLD 3

// NOTE: On AVR (Uno) avoid large use of dynamic String objects; this example keeps Strings
// for convenience but if you see memory fragmentation switch to a fixed char queue.

// Servo definitions
Servo shoulder_servo;
Servo elbow_servo;
Servo penup_servo;

float shoulder_currentAngle = 0;
float elbow_currentAngle = 0;

int SS_PIN = 9;
int ES_PIN = 10;
int PS_PIN = 11;

// Command buffer (ring buffer of String - capacity is BUFFER_SIZE-1)
String commandBuffer[BUFFER_SIZE];
int head = 0;  // next write position
int tail = 0;  // next read position
bool active = false;

// Line reader for non-blocking serial input
char lineBuf[64];
size_t lineIdx = 0;

// Request throttling
unsigned long lastRequestMillis = 0;
const unsigned long REQUEST_INTERVAL_MS = 300; // don't spam requests

// ----- Helper Functions -----
int buffer_count() {
  return (head - tail + BUFFER_SIZE) % BUFFER_SIZE;
}

bool buffer_is_empty() {
  return head == tail;
}

bool buffer_is_full() {
  return ((head + 1) % BUFFER_SIZE) == tail;
}

bool buffer_is_low() {
  int count = buffer_count();
  // We consider low when <= threshold so a request will be sent early enough
  return count <= BUFFER_LOW_THRESHOLD;
}

void buffer_push(const String &cmd) {
  if (!buffer_is_full()) {
    commandBuffer[head] = cmd;
    head = (head + 1) % BUFFER_SIZE;
  } else {
    // Buffer full: drop or signal error
    Serial.println("BUFFER FULL");
  }
}

// returns the next command from the buffer if its not empty
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
    lastRequestMillis = millis();
  }
}

// Non-blocking serial line processor: reads available chars and pushes full lines to the buffer
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
    } 
    else {
      if (lineIdx < sizeof(lineBuf) - 1) {
        lineBuf[lineIdx++] = c;
      } 
      else {
        // overflow: reset line buffer
        lineIdx = 0;
      }
    }
  }
}

// ----- Motion Functions -----
void pen_up() {
  penup_servo.write(0);
  delay(200);
}

void pen_down() {
  penup_servo.write(90);
  delay(200);
}


// Suggested replacement for move_to and moveSmooth
void move_to(float shoulder_dest, float elbow_dest) {
  // Constrain angles to valid servo range
  shoulder_dest = constrain(shoulder_dest, 0, 180);
  elbow_dest = constrain(elbow_dest, 0, 180);

  float shoulder_start = shoulder_currentAngle;
  float elbow_start = elbow_currentAngle;

  float shoulder_dist = shoulder_dest - shoulder_start;
  float elbow_dist = elbow_dest - elbow_start;

  // Determine the number of steps by the longest distance
  int steps = max(abs(shoulder_dist), abs(elbow_dist));

  if (steps == 0) return; // No movement needed

  float shoulder_step = shoulder_dist / steps;
  float elbow_step = elbow_dist / steps;

  for (int i = 1; i <= steps; i++) {
    float s_pos = shoulder_start + (shoulder_step * i);
    float e_pos = elbow_start + (elbow_step * i);
    
    shoulder_servo.write(s_pos);
    elbow_servo.write(e_pos);
    
    // You can still process serial and request more data here
    processSerialInput();
    request_more_if_low();
    
    delay(10); // A small delay for smoothness
  }

  // Update final positions
  shoulder_currentAngle = shoulder_dest;
  elbow_currentAngle = elbow_dest;
}

// ----- Setup -----
void setup() {
  shoulder_servo.attach(SS_PIN);
  elbow_servo.attach(ES_PIN);
  penup_servo.attach(PS_PIN);

  Serial.begin(9600);
  Serial.println("Ready");
  // ask for initial batch of commands
  request_more_if_low();
}

// ----- Main Loop -----
void loop() {
  // Process any incoming serial bytes (non-blocking)
  processSerialInput();

  // If buffer low, request more from host
  request_more_if_low();

  // Execute next command if idle and buffer not empty
  if (!active && !buffer_is_empty()) {
    active = true;
    String cmd = buffer_pop();

    if (cmd == "PEN UP") pen_up();
    else if (cmd == "PEN DOWN") pen_down();
    else if (cmd == "END") pen_up();
    else {
      // Expecting input in the form "(x, y)" where x and y are numbers
      int open = cmd.indexOf('(');
      int comma = cmd.indexOf(',');
      int close = cmd.indexOf(')');
      if (open >= 0 && comma > open && close > comma) {
        String sx = cmd.substring(open + 1, comma);
        String sy = cmd.substring(comma + 1, close);
        sx.trim(); sy.trim();
        float s = sx.toFloat();
        float e = sy.toFloat();
        // Basic validation
        if (!isnan(s) && !isnan(e)) {
          move_to(s, e);
        } 
        else {
          Serial.println("Invalid numbers");
        }
      } 
      else {
        Serial.println("Invalid format");
      }
    }
    active = false;
  }
}
