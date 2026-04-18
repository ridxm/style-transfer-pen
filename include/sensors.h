#pragma once
#include <Arduino.h>

// Number of FSRs wired to the board. Set to however many you actually
// have connected (1 through 8). Pins used are A0..A[NUM_FSR-1].
#define NUM_FSR 8

struct Readings {
  int   fsr[NUM_FSR];        // 0–4095 per sensor (12-bit ADC)
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

// Human-readable labeled line: FSR0=..FSR7=.. AX=.. ... ROLL=.. PITCH=.. YAW=..
void sensors_print(const Readings& r);

// Labeled line with every field — one per loop (for serial monitor use).
void sensors_print_rpy(const Readings& r);
