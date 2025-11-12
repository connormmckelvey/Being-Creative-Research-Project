//----- Libraries -----
#include <Servo.h>
#include <Arduino.h>
#include <LiquidCrystal.h>

//------- inits ----------

#define BUFFER_SIZE 10
#define BUFFER_LOW_THRESHOLD 3

// --- ADDED: PHYSICAL SERVO LIMITS ---
// CALIBRATE THESE: Find the angles where your servo stops
// without straining, and add a small safety margin.
#define SHOULDER_MIN_ANGLE -180
#define SHOULDER_MAX_ANGLE 270
#define ELBOW_MIN_ANGLE -65
#define ELBOW_MAX_ANGLE 245
// --- END OF ADD ---

// --- NEW: SHOULDER SERVO PULSE WIDTH CALIBRATION ---
// Adjust these microsecond (us) values to stop the over-rotation of your 20kg shoulder servo.
// We start with the Arduino library's defaults (544us to 2400us), but you MUST find the
// actual pulse width that makes the servo stop safely at its 0 and 180 degree points.
const int SHOULDER_MIN_US = 800;  // <-- STARTING TEST VALUE
const int SHOULDER_MAX_US = 2200; // <-- STARTING TEST VALUE
// --- END OF NEW ---

// Servo definitions
Servo shoulder_servo; // Miuezi 20kg (Pin 9) - WILL USE WRITE MICROSECONDS
Servo elbow_servo;    // SG90 (Pin 10) - REMAINS WITH WRITE()
Servo penup_servo;    // Analog Micro (Pin 11) - REMAINS WITH WRITE()

// --- FIX: Initialize angles to the home position ---
float shoulder_currentAngle = 90.0;
float elbow_currentAngle = 90.0;

int SS_PIN = 9;  // Shoulder Servo Pin
int ES_PIN = 10; // Elbow Servo Pin
int PS_PIN = 11; // Pen-Up Servo Pin

// LCD pins: RS, E, D4, D5, D6, D7
LiquidCrystal lcd(7, 8, 4, 5, 6, 3); // Adjust to your wiring

// Command buffer
String commandBuffer[BUFFER_SIZE];
int head = 0;  
int tail = 0;  
bool active = false; // Flag to show if arm is busy moving

// Line reader
char lineBuf[128];
size_t lineIdx = 0;

// Request throttling
unsigned long lastRequestMillis = 0;
const unsigned long REQUEST_INTERVAL_MS = 300; // ms between "REQUEST" signals

// ----- Helper Functions -----

// --- NEW HELPER: Angle to Microseconds for the Shoulder ---
// Maps a desired angle (0-180) to the shoulder servo's calibrated pulse width range.
int angle_to_us(float angle, int min_us, int max_us) {
  // We constrain the input angle to 0-180 before mapping to prevent overflow errors.
  int constrained_angle = constrain((int)round(angle), 0, 180);
  // map converts the 0-180 angle range to the custom microsecond range
  return map(constrained_angle, 0, 180, min_us, max_us);
}
// --- END OF NEW HELPER ---

int buffer_count() {
  return (head - tail + BUFFER_SIZE) % BUFFER_SIZE;
}

bool buffer_is_empty() { return head == tail; }
bool buffer_is_full() { return ((head + 1) % BUFFER_SIZE) == tail; }
bool buffer_is_low() { return buffer_count() <= BUFFER_LOW_THRESHOLD; }

// Adds a command to the circular buffer
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

// Retrieves a command from the circular buffer
String buffer_pop() {
  String cmd = "";
  if (!buffer_is_empty()) {
    cmd = commandBuffer[tail];
    tail = (tail + 1) % BUFFER_SIZE;
  }
  return cmd;
}

// Asks the host for more commands if the buffer is running low
void request_more_if_low() {
  if (buffer_is_low() && (millis() - lastRequestMillis) > REQUEST_INTERVAL_MS) {
    Serial.println("REQUEST");
    lcd.setCursor(0, 1);
    lcd.print("Buffer Low...   ");
    lastRequestMillis = millis();
  }
}

// Non-blocking serial line processor
// Reads characters from serial and builds a command string
void processSerialInput() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\r') continue; // Ignore carriage return
    
    if (c == '\n') { // Newline indicates end of command
      if (lineIdx > 0) {
        lineBuf[lineIdx] = '\0'; // Null-terminate the string
        String s = String(lineBuf);
        s.trim(); // Remove leading/trailing whitespace
        if (s.length() > 0) buffer_push(s);
        lineIdx = 0; // Reset for next line
      }
    } else {
      if (lineIdx < sizeof(lineBuf) - 1) {
        lineBuf[lineIdx++] = c; // Add char to buffer
      } else {
         // Buffer overflow, discard this line
        lineIdx = 0;
      }
    }
  }
}

// ----- Motion Functions -----
void pen_up() {
  // Safe "up" position for the micro servo at 5V
  // (Adjust 0 if your servo needs a different 'up' angle)
  penup_servo.write(180); 
  delay(200); // Give servo time to move
  
  // --- UPDATED: Delay for pen to settle (2 seconds) ---
  delay(2000); // Wait for vibrations to stop
  
  lcd.setCursor(0, 0);
  lcd.print("Pen Up          ");
}

void pen_down() {
  // Safe "down" position for the micro servo at 5V
  // (Adjust 180 if your servo needs a different 'down' angle)
  penup_servo.write(0); 
  delay(200); // Give servo time to move
  
  // --- UPDATED: Delay for pen to settle (2 seconds) ---
  delay(2000); // Wait for vibrations to stop
  
  lcd.setCursor(0, 0);
  lcd.print("Pen Down        ");
}

// Smoothly moves both servos from current to destination angles
void move_to(float shoulder_destination, float elbow_destination) {
  // --- UPDATED: Constrain to physical limits ---
  // float shoulder_dest = constrain(shoulder_destination, SHOULDER_MIN_ANGLE, SHOULDER_MAX_ANGLE);
  // float elbow_dest = constrain(elbow_destination, ELBOW_MIN_ANGLE, ELBOW_MAX_ANGLE);
  // if (shoulder_dest != shoulder_destination || elbow_dest != elbow_destination)
  // {
  //   Serial.println("Warning: Commanded angles out of bounds, constrained.");
  //   lcd.setCursor(0, 0);
  //   lcd.print("Angle Constrained");
  // }
  float shoulder_dest = shoulder_destination;
  float elbow_dest = elbow_destination;

  float shoulder_start = shoulder_currentAngle;
  float elbow_start = elbow_currentAngle;

  float shoulder_dist = shoulder_dest - shoulder_start;
  float elbow_dist = elbow_dest - elbow_start;

  // --- FIX 1: Use fabs() for floats instead of abs() ---
  int steps = max(fabs(shoulder_dist), fabs(elbow_dist));
  
  // --- FIX 2: Reduced minimum steps for stability on small servos ---
  // The minimum movement duration is now 10 steps * 8ms = 80ms.
  if (steps < 10) steps = 10; // Reduced from 20 to 10
  
  float shoulder_step = shoulder_dist / steps;
  float elbow_step = elbow_dist / steps;

  for (int i = 1; i <= steps; i++) {
    float shoulder_angle = shoulder_start + shoulder_step * i;
    float elbow_angle = elbow_start + elbow_step * i;

    // *** SHOULDER SERVO (20kg): Use calibrated writeMicroseconds ***
    int shoulder_us = angle_to_us(shoulder_angle, SHOULDER_MIN_US, SHOULDER_MAX_US);
    shoulder_servo.writeMicroseconds(shoulder_us);
    
    // *** ELBOW SERVO (SG90): Continue to use standard write() ***
    elbow_servo.write(round(elbow_angle));
    
    // Check for new commands while moving (non-blocking)
    processSerialInput();
    request_more_if_low();
    
    // --- RESTORED: Faster movement speed (8ms delay) ---
    delay(8); // Restored from 12ms to 8ms for stability.
  }

  // Update current angles
  shoulder_currentAngle = shoulder_dest;
  elbow_currentAngle = elbow_dest;

  // --- ADDED: 1-second pause after the move is complete ---
  delay(1000); 

  lcd.setCursor(0, 0);
  lcd.print("Move Done       ");
}

// ----- Setup -----
void setup() {
  // Attach all servos to their respective pins
  shoulder_servo.attach(SS_PIN);
  elbow_servo.attach(ES_PIN);
  penup_servo.attach(PS_PIN);

  // --- HOMING SEQUENCE ---
  // 1. Move the pen up first
  pen_up(); 
  
  // 2. Define your home position (e.g., 90, 90)
  float homeShoulder = 90.0;
  float homeElbow = 90.0;
  
  // 3. Set the current angle variables to match the home position
  shoulder_currentAngle = homeShoulder;
  elbow_currentAngle = homeElbow;
  
  // 4. Physically move the arm to this position
  // Shoulder uses calibrated microsecond value
  int home_shoulder_us = angle_to_us(homeShoulder, SHOULDER_MIN_US, SHOULDER_MAX_US);
  shoulder_servo.writeMicroseconds(home_shoulder_us);
  
  // Elbow uses standard angle value
  elbow_servo.write(round(homeElbow));
  // --- END OF HOMING ---

  Serial.begin(9600);
  lcd.begin(16, 2); // Initialize the 16x2 LCD
  lcd.setCursor(0, 0);
  lcd.print("Drawing Robot Ready");
  
  request_more_if_low(); // Request first batch of commands
}

// ----- Main Loop -----
void loop() {
  // Always check for new commands
  processSerialInput();
  request_more_if_low();

  // Only process a command if the arm is not active
  if (!active && !buffer_is_empty()) {
    active = true; // Mark arm as busy
    String cmd = buffer_pop();
    Serial.print("Processing command: ");
    Serial.println(cmd);

    // Display command on LCD
    lcd.setCursor(0, 1);
    if (cmd.length() > 16) {
      lcd.print(cmd.substring(0, 16)); // Truncate long commands
    } else {
      lcd.print(cmd + "                "); // Pad to clear old text
    }

    // --- Command Parser ---
    if (cmd == "PEN UP") {
      pen_up();
    }
    else if (cmd == "PEN DOWN") {
      pen_down();
    }
    else if (cmd == "END") {
      pen_up(); // Lift pen at the end of the file
    }
    else if (cmd == "START") {
      lcd.setCursor(0, 0);
      lcd.print("File Started    ");
      // This command is just acknowledged; no action needed.
    }
    else {
      // Try to parse as a coordinate command: (S, E)
      int open = cmd.indexOf('(');
      int comma = cmd.indexOf(',');
      int close = cmd.indexOf(')');
      
      if (open >= 0 && comma > open && close > comma) {
        String sx = cmd.substring(open + 1, comma);
        String sy = cmd.substring(comma + 1, close);
        sx.trim(); 
        sy.trim();
        
        float s = sx.toFloat();
        float e = sy.toFloat();
        
        if (!isnan(s) && !isnan(e)) {
          move_to(s, e);
        }
        else {
          Serial.println("Invalid numbers");
          lcd.setCursor(0, 0);
          lcd.print("Invalid numbers ");
        }
      } 
      else {
        Serial.print("Invalid format: ");
        Serial.println(cmd);
        lcd.setCursor(0, 0);
        lcd.print("Invalid format  ");
      }
    }
    active = false; // Mark arm as free for next command
  }
}