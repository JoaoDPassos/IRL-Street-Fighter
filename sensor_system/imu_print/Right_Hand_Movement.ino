#include <ArduinoBLE.h>
#include <Arduino_BMI270_BMM150.h>

// BLE UART Service
BLEService uartService("6E400001-B5A3-F393-E0A9-E50E24DCCA9E");

// BLE Characteristics
BLECharacteristic txCharacteristic("6E400003-B5A3-F393-E0A9-E50E24DCCA9E", BLERead | BLENotify, 20);
BLECharacteristic rxCharacteristic("6E400002-B5A3-F393-E0A9-E50E24DCCA9E", BLEWrite, 20);

// Punch Detection Parameters - FIXED
const float PUNCH_ACCEL_THRESHOLD = 1.3;  // Above gravity baseline
const float PUNCH_RETRACT_THRESHOLD = -0.5;  // Realistic retraction
unsigned long lastPunchTime = 0;  
const unsigned long PUNCH_DEBOUNCE = 300;
bool punchInProgress = false;

// Right Movement Detection - FIXED
const float TILT_RIGHT_THRESHOLD = 0.5;  // Activate threshold
const float TILT_NEUTRAL_THRESHOLD = 0.3;  // Deactivate threshold (must be lower)
bool rightMovementActive = false;

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
  BLE.setLocalName("Right Hand");
  BLE.setDeviceName("Right Hand");
  
  uartService.addCharacteristic(txCharacteristic);
  uartService.addCharacteristic(rxCharacteristic);
  
  BLE.addService(uartService);
  BLE.setAdvertisedService(uartService);
  
  BLE.advertise();
  
  Serial.println("Right Hand ready! Tilt-hold & soft punch mode.");
  
  // HELPFUL: Print resting values for 3 seconds
  Serial.println("Calibration - hold hand still:");
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
        // Serial.print(" Punch:"); Serial.print(punchInProgress);
        // Serial.print(" Tilt:"); Serial.println(rightMovementActive);
        
        // === PUNCH DETECTION ===
        float punchForce = xA;
        
        if (punchForce > PUNCH_ACCEL_THRESHOLD && !punchInProgress) {
          if (currentTime - lastPunchTime > PUNCH_DEBOUNCE) {
            String message = "Movement:PunchR\n";
            Serial.print("PUNCH! Force: ");
            Serial.println(punchForce);
            
            txCharacteristic.writeValue(message.c_str());
            
            lastPunchTime = currentTime;
            punchInProgress = true;
          }
        }
        
        // Reset punch when hand retracts OR returns to baseline
        if ((punchForce < PUNCH_RETRACT_THRESHOLD || punchForce < 0.8) && punchInProgress) {
          punchInProgress = false;
          Serial.println("Punch reset");
        }
        
        // === RIGHT MOVEMENT DETECTION ===
        float tiltAmount = yA;d
        
        // Only check tilt when not punching
        if (!punchInProgress) {
          // ACTIVATE: Hand tilted right
          if (tiltAmount > TILT_RIGHT_THRESHOLD && !rightMovementActive) {
            String message = "Movement:Right_Down\n";
            Serial.print("RIGHT TILT ACTIVE! Tilt: ");
            Serial.println(tiltAmount);
            
            txCharacteristic.writeValue(message.c_str());
            rightMovementActive = true;
          }
          
          // DEACTIVATE: Hand returned to neutral
          else if (tiltAmount < TILT_NEUTRAL_THRESHOLD && rightMovementActive) {
            String message = "Movement:Right_Up\n";
            Serial.print("RIGHT TILT RELEASED! Tilt: ");
            Serial.println(tiltAmount);
            
            txCharacteristic.writeValue(message.c_str());
            rightMovementActive = false;
          }
        }
      }
      
      delay(10);
    }
    
    Serial.println("Disconnected from central");
  }
}
