#include <Arduino_BMI270_BMM150.h>

float accelThreshold = 0.5;
unsigned long lastMovementTime = 0;
const unsigned long debounceDelay = 500;

void setup() {
  Serial.begin(9600);
  
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
  
  Serial.println("Movement Keyboard ready!");
}

void loop() {
  float x, y, z;
  
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(x, y, z);
    float totalAccel = sqrt(x*x + y*y + z*z);
    
    if (abs(totalAccel - 1.0) > accelThreshold) {
      unsigned long currentTime = millis();
      if (currentTime - lastMovementTime > debounceDelay) {
        Serial.println("Movement detected! Sending 'a'");
        lastMovementTime = currentTime;
      }
    }
  }
  delay(50);
}
