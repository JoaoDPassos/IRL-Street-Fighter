#include <Arduino_BMI270_BMM150.h>
#include <MadgwickAHRS.h>

Madgwick filter;

const float sampleHz = 200.0f;     // 5 ms loop -> 200 Hz
const float g_to_ms2 = 9.80665f;

void setup() {
  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && (millis() - t0 < 3000)) {}

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  filter.begin(sampleHz);
  Serial.println("IMU + Madgwick started");
}

void loop() {
  static unsigned long lastLoop = 0;
  if (micros() - lastLoop < 5000) return;  // ~200 Hz
  lastLoop = micros();

  float ax=0, ay=0, az=0;   // accel (g)
  float gx=0, gy=0, gz=0;   // gyro (deg/s)
  float mx=0, my=0, mz=0;   // mag (uT)

  if (IMU.accelerationAvailable()) IMU.readAcceleration(ax, ay, az);
  if (IMU.gyroscopeAvailable())     IMU.readGyroscope(gx, gy, gz);

  bool haveMag = false;
  if (IMU.magneticFieldAvailable()) {
    IMU.readMagneticField(mx, my, mz);
    haveMag = true;
  }

  if (haveMag) filter.update(gx, gy, gz, ax, ay, az, mx, my, mz);
  else         filter.updateIMU(gx, gy, gz, ax, ay, az);

  float roll  = filter.getRoll();
  float pitch = filter.getPitch();
  float yaw   = filter.getYaw();

  // Print angles
  Serial.print("Yaw: ");   Serial.print(yaw, 1);
  Serial.print("\tPitch: ");Serial.print(pitch, 1);
  Serial.print("\tRoll: "); Serial.print(roll, 1);

  // Print accel in m/s^2
  Serial.print("\tAcc[m/s^2] x: "); Serial.print(ax * g_to_ms2, 2);
  Serial.print(" y: ");              Serial.print(ay * g_to_ms2, 2);
  Serial.print(" z: ");              Serial.print(az * g_to_ms2, 2);

  Serial.println();
}

