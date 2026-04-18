/*
 * penDNA pen firmware — Arduino Nano 33 BLE Sense Rev2
 *
 * Reads the onboard BMI270 IMU (accelerometer + gyroscope) and a thin-film
 * FSR pressure sensor, packs each sample into a 32-byte frame, and notifies
 * it over BLE at ~100 Hz.
 *
 * Packet layout (little-endian, 32 bytes):
 *   float32 t_ms        (millis() since boot)
 *   float32 ax, ay, az  (g)
 *   float32 gx, gy, gz  (deg/s)
 *   float32 pressure    (normalized 0..1)
 *
 * Service UUID 19B10000-E8F2-537E-4F6C-D104768A1214
 * Char    UUID 19B10001-E8F2-537E-4F6C-D104768A1214 (NOTIFY)
 *
 * Wiring:
 *   FSR in series with 10k resistor as a voltage divider; junction to A0.
 *   FSR + 3V3, other leg of 10k to GND.
 */

#include <ArduinoBLE.h>
#include "Arduino_BMI270_BMM150.h"

static const char* SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214";
static const char* CHAR_UUID    = "19B10001-E8F2-537E-4F6C-D104768A1214";

BLEService penService(SERVICE_UUID);
BLECharacteristic penChar(CHAR_UUID, BLERead | BLENotify, 32);

static const uint8_t FSR_PIN = A0;
static const unsigned long SAMPLE_PERIOD_MS = 10;  // 100 Hz
unsigned long nextSampleAt = 0;

void fatal(const char* msg) {
  Serial.println(msg);
  while (1) delay(1000);
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);

  if (!IMU.begin()) fatal("IMU init failed");
  if (!BLE.begin()) fatal("BLE init failed");

  BLE.setLocalName("penDNA");
  BLE.setAdvertisedService(penService);
  penService.addCharacteristic(penChar);
  BLE.addService(penService);

  uint8_t zero[32] = {0};
  penChar.writeValue(zero, sizeof(zero));

  BLE.advertise();
  Serial.println("penDNA advertising");
}

void loop() {
  BLEDevice central = BLE.central();
  if (!central) return;

  Serial.print("Connected: ");
  Serial.println(central.address());

  while (central.connected()) {
    unsigned long now = millis();
    if ((long)(now - nextSampleAt) < 0) continue;
    nextSampleAt = now + SAMPLE_PERIOD_MS;

    float ax = 0, ay = 0, az = 0;
    float gx = 0, gy = 0, gz = 0;
    if (IMU.accelerationAvailable()) IMU.readAcceleration(ax, ay, az);
    if (IMU.gyroscopeAvailable())     IMU.readGyroscope(gx, gy, gz);

    int raw = analogRead(FSR_PIN);
    float pressure = raw / 4095.0f;

    float payload[8] = {
      (float)now, ax, ay, az, gx, gy, gz, pressure
    };
    penChar.writeValue((uint8_t*)payload, sizeof(payload));
  }

  Serial.println("Disconnected");
}
