#include "sensors.h"
#include "Arduino_BMI270_BMM150.h"
#include <MadgwickAHRS.h>

// First NUM_FSR analog pins on the Nano 33 BLE. Wire FSR 0 to A0, FSR 1 to A1, ...
static const int FSR_PINS[NUM_FSR] = {
  A0, A1, A2, A3, A4, A5, A6, A7
};

static const float FILTER_HZ     = 100.0f;   // must match the loop cadence in main.cpp
static const int   CAL_SAMPLES   = 200;      // ~2 s at 100 Hz

static Madgwick filter;

// gyro bias measured at startup; subtracted from every future reading
static float gyro_bias_x = 0, gyro_bias_y = 0, gyro_bias_z = 0;

// keep last-known IMU values so a missed sample doesn't zero the output
static float s_ax = 0, s_ay = 0, s_az = 0;
static float s_gx = 0, s_gy = 0, s_gz = 0;
static float s_mx = 0, s_my = 0, s_mz = 0;

static void calibrate_gyro() {
  Serial.println("# Calibrating gyro — hold the pen still for 2 s...");

  float sx = 0, sy = 0, sz = 0;
  int   n  = 0;

  unsigned long t_end = millis() + 2000;
  while (millis() < t_end && n < CAL_SAMPLES) {
    if (IMU.gyroscopeAvailable()) {
      float x, y, z;
      IMU.readGyroscope(x, y, z);
      sx += x; sy += y; sz += z;
      n++;
    }
  }

  if (n > 0) {
    gyro_bias_x = sx / n;
    gyro_bias_y = sy / n;
    gyro_bias_z = sz / n;
  }

  Serial.print("# Gyro bias (deg/s): ");
  Serial.print(gyro_bias_x, 3); Serial.print(", ");
  Serial.print(gyro_bias_y, 3); Serial.print(", ");
  Serial.println(gyro_bias_z, 3);
}

bool sensors_begin() {
  analogReadResolution(12);
  analogReference(AR_INTERNAL1V2);

  if (!IMU.begin()) return false;

  calibrate_gyro();
  filter.begin(FILTER_HZ);
  return true;
}

void sensors_read(Readings& out) {
  for (int i = 0; i < NUM_FSR; i++) {
    out.fsr[i] = analogRead(FSR_PINS[i]);
  }

  if (IMU.accelerationAvailable())  IMU.readAcceleration(s_ax, s_ay, s_az);
  if (IMU.gyroscopeAvailable())     IMU.readGyroscope(s_gx, s_gy, s_gz);
  if (IMU.magneticFieldAvailable()) IMU.readMagneticField(s_mx, s_my, s_mz);

  float gx = s_gx - gyro_bias_x;
  float gy = s_gy - gyro_bias_y;
  float gz = s_gz - gyro_bias_z;

  // 6-axis mode: ignore magnetometer entirely. Roll & pitch stay locked via accel;
  // yaw has no absolute reference and will drift slowly — fine for a pen viewer.
  filter.updateIMU(gx, gy, gz, s_ax, s_ay, s_az);

  out.ax = s_ax; out.ay = s_ay; out.az = s_az;
  out.gx = gx;   out.gy = gy;   out.gz = gz;
  out.mx = s_mx; out.my = s_my; out.mz = s_mz;
  out.roll  = filter.getRoll();
  out.pitch = filter.getPitch();
  out.yaw   = filter.getYaw();
}

void sensors_print(const Readings& r) {
  for (int i = 0; i < NUM_FSR; i++) {
    Serial.print("FSR"); Serial.print(i); Serial.print('=');
    Serial.print(r.fsr[i]);
    Serial.print(' ');
  }
  Serial.print(" AX="); Serial.print(r.ax, 3);
  Serial.print(" AY=");  Serial.print(r.ay, 3);
  Serial.print(" AZ=");  Serial.print(r.az, 3);
  Serial.print("  GX="); Serial.print(r.gx, 2);
  Serial.print(" GY=");  Serial.print(r.gy, 2);
  Serial.print(" GZ=");  Serial.print(r.gz, 2);
  Serial.print("  MX="); Serial.print(r.mx, 2);
  Serial.print(" MY=");  Serial.print(r.my, 2);
  Serial.print(" MZ=");  Serial.print(r.mz, 2);
  Serial.print("  ROLL=");  Serial.print(r.roll, 1);
  Serial.print(" PITCH=");  Serial.print(r.pitch, 1);
  Serial.print(" YAW=");    Serial.println(r.yaw, 1);
}

// CSV line consumed by the Processing viewer: "roll,pitch,yaw,fsr\n"
void sensors_print_rpy(const Readings& r) {
  Serial.print("roll = ");  Serial.print(r.roll, 2);  Serial.print(", ");
  Serial.print("pitch = "); Serial.print(r.pitch, 2); Serial.print(", ");
  Serial.print("yaw = ");   Serial.print(r.yaw, 2);
  for (int i = 0; i < NUM_FSR; i++) {
    Serial.print(", fsr"); Serial.print(i); Serial.print(" = ");
    Serial.print(r.fsr[i]);
  }
  Serial.println();
}
