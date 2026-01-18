#include <ArduinoBLE.h>
#include <Arduino_BMI270_BMM150.h>

// BLE UART Service
BLEService uartService("6E400001-B5A3-F393-E0A9-E50E24DCCA9E");

// BLE Characteristics
BLECharacteristic txCharacteristic("6E400003-B5A3-F393-E0A9-E50E24DCCA9E", BLERead | BLENotify, 20);
BLECharacteristic rxCharacteristic("6E400002-B5A3-F393-E0A9-E50E24DCCA9E", BLEWrite, 20);

// Kick Detection Parameters
const float KICK_ACCEL_THRESHOLD = 1.5;  // Forward acceleration for kick
const float KICK_RETRACT_THRESHOLD = -0.6;  // Leg pulling back
unsigned long lastKickTime = 0;  
const unsigned long KICK_DEBOUNCE = 400;  // Slightly longer than punch
bool kickInProgress = false;

// Stomp Detection Parameters
const float STOMP_ACCEL_THRESHOLD = 1.8;  // Strong downward acceleration
const float STOMP_RECOVERY_THRESHOLD = 0.8;  // Return to baseline
unsigned long lastStompTime = 0;  
const unsigned long STOMP_DEBOUNCE = 500;  // Prevent rapid re-triggering
bool stompInProgress = false;

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);
  
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
  
  if (!BLE.begin()) {
    Serial.println("Failed to initialize BLE!");
    while (1);
  }
  
  // Set up BLE
  BLE.setLocalName("Leg");
  BLE.setDeviceName("Leg");
  
  uartService.addCharacteristic(txCharacteristic);
  uartService.addCharacteristic(rxCharacteristic);
  
  BLE.addService(uartService);
  BLE.setAdvertisedService(uartService);
  
  BLE.advertise();
  
  Serial.println("Right Leg ready! Kick & Stomp mode.");
  
  // Calibration - leg hanging naturally
  Serial.println("Calibration - let leg hang naturally:");
  for(int i = 0; i < 30; i++) {
    float xA, yA, zA;
    if (IMU.accelerationAvailable()) {
      IMU.readAcceleration(xA, yA, zA);
      Serial.print("X:"); Serial.print(xA); 
      Serial.print(" Y:"); Serial.print(yA); 
      Serial.print(" Z:"); Serial.println(zA);
    }
    delay(100);
  }
}

void loop() {
  BLEDevice central = BLE.central();
  
  if (central) {
    Serial.print("Connected to: ");
    Serial.println(central.address());
    
    while (central.connected()) {
      float xA, yA, zA;
      unsigned long currentTime = millis();
      
      if (IMU.accelerationAvailable()) {
        IMU.readAcceleration(xA, yA, zA);
        
        // DEBUG - uncomment to see live values
        // Serial.print("X:"); Serial.print(xA); 
        // Serial.print(" Y:"); Serial.print(yA); 
        // Serial.print(" Z:"); Serial.print(zA); 
        // Serial.print(" Kick:"); Serial.print(kickInProgress);
        // Serial.print(" Stomp:"); Serial.println(stompInProgress);
        
        // === KICK DETECTION ===
        // Assumes X-axis aligns with forward leg extension
        float kickForce = xA;
        
        if (kickForce > KICK_ACCEL_THRESHOLD && !kickInProgress && !stompInProgress) {
          if (currentTime - lastKickTime > KICK_DEBOUNCE) {
            String message = "Movement:KickR\n";
            Serial.print("KICK! Force: ");
            Serial.println(kickForce);
            
            txCharacteristic.writeValue(message.c_str());
            
            lastKickTime = currentTime;
            kickInProgress = true;
          }
        }
        
        // Reset kick when leg retracts
        if ((kickForce < KICK_RETRACT_THRESHOLD || kickForce < 0.7) && kickInProgress) {
          kickInProgress = false;
          Serial.println("Kick reset");
        }
        
        // === STOMP DETECTION ===
        // Assumes Z-axis points downward when leg raised
        float stompForce = zA;
        
        if (stompForce > STOMP_ACCEL_THRESHOLD && !stompInProgress && !kickInProgress) {
          if (currentTime - lastStompTime > STOMP_DEBOUNCE) {
            String message = "Movement:StompR\n";
            Serial.print("STOMP! Force: ");
            Serial.println(stompForce);
            
            txCharacteristic.writeValue(message.c_str());
            
            lastStompTime = currentTime;
            stompInProgress = true;
          }
        }
        
        // Reset stomp when leg returns to resting position
        if (stompForce < STOMP_RECOVERY_THRESHOLD && stompInProgress) {
          stompInProgress = false;
          Serial.println("Stomp reset");
        }
      }
      
      delay(10);
    }
    
    Serial.println("Disconnected from central");
  }
}
