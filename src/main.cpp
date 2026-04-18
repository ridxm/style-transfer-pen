#include <Arduino.h>
#include "sensors.h"

// Loop period in microseconds — must match FILTER_HZ in sensors.cpp (100 Hz -> 10000 us).
static const unsigned long LOOP_US = 10000;
static unsigned long next_tick = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial);   // remove this line to run standalone on battery

  if (!sensors_begin()) {
    Serial.println("Sensor init failed!");
    while (1);
  }

  next_tick = micros();
}

void loop() {
  // steady 100 Hz cadence — Madgwick filter accuracy depends on a known sample rate
  unsigned long now = micros();
  if ((long)(now - next_tick) < 0) return;
  next_tick += LOOP_US;

  Readings r;
  sensors_read(r);
  sensors_print_rpy(r); 
}
