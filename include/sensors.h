#pragma once
#include <Arduino.h>

struct Readings {
  int   fsr;                 // 0–4095 (12-bit ADC)
  float ax, ay, az;          // accelerometer, g
  float gx, gy, gz;          // gyroscope, deg/s
  float mx, my, mz;          // magnetometer, uT
  float roll, pitch, yaw;    // fused orientation, degrees
};

// Initialize ADC settings, the on-board IMU, and the Madgwick filter.
// Returns false if the IMU fails.
bool sensors_begin();

// Update the Madgwick filter with the latest IMU samples and fill `out`.
// Call this in a loop at a roughly steady cadence.
void sensors_read(Readings& out);

// Print one tab-separated line (FSR + 9 IMU axes + roll/pitch/yaw).
void sensors_print(const Readings& r);

// Print CSV "roll,pitch,yaw" — consumed by the Processing viewer.
void sensors_print_rpy(const Readings& r);
