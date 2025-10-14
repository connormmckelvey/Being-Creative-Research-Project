#include <Servo.h>
#include <Arduino.h>

// Servo definitions
Servo shoulder_servo;
float shoulder_currentAngle = 0;
int SS_PIN = 9;

Servo elbow_servo;
float elbow_currentAngle = 0;
int ES_PIN = 10;

Servo penup_servo;
int PS_PIN = 11;

// ----- Function Definitions -----
void pen_up() {
  penup_servo.write(0);
  delay(500);
}

void pen_down() {
  penup_servo.write(90);
  delay(500);
}

void moveSmooth(Servo &servo, float startAngle, float endAngle, int stepDelay) {
  float step = 1.0;
  if (startAngle < endAngle) {
    for (float a = startAngle; a <= endAngle; a += step) {
      servo.write(a);
      delay(stepDelay);
    }
  } else {
    for (float a = startAngle; a >= endAngle; a -= step) {
      servo.write(a);
      delay(stepDelay);
    }
  }
}

void move_to(float shoulder_angle, float elbow_angle) {
  if (shoulder_angle >= 0 && shoulder_angle <= 180) {
    moveSmooth(shoulder_servo, shoulder_currentAngle, shoulder_angle, 5);
    shoulder_currentAngle = shoulder_angle;
  }
  if (elbow_angle >= 0 && elbow_angle <= 180) {
    moveSmooth(elbow_servo, elbow_currentAngle, elbow_angle, 5);
    elbow_currentAngle = elbow_angle;
  }
}

// ----- Setup -----
void setup() {
  shoulder_servo.attach(SS_PIN);
  shoulder_servo.write(shoulder_currentAngle); 

  elbow_servo.attach(ES_PIN);
  elbow_servo.write(elbow_currentAngle); 

  penup_servo.attach(PS_PIN);
  penup_servo.write(0);

  Serial.begin(9600);
  Serial.println("Ready for commands...");
}

// ----- Main Loop -----
void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.length() == 0) return;
    else if (input == "START") return;
    else if (input == "PEN UP") pen_up();
    else if (input == "PEN DOWN") pen_down();
    else if (input == "END") pen_up();
    else {
      float shoulder_angle, elbow_angle;
      if (sscanf(input.c_str(), "(%f, %f)", &shoulder_angle, &elbow_angle) == 2) {
        move_to(shoulder_angle, elbow_angle);
      } else {
        Serial.println("Invalid input format!");
      }
    }
  }
}
