#include <Arduino.h>
#include "sensors.h"

// Loop period in microseconds — must match FILTER_HZ in sensors.cpp (100 Hz -> 10000 us).
static const unsigned long LOOP_US = 10000;
static unsigned long next_tick = 0;

// --- I/O pins ---
static const int PIN_BUTTON = 2;    // D2, wired to GND (active LOW via internal pull-up)
static const int PIN_BUZZER = 3;    // D3, passive buzzer to GND

// --- Button debounce ---
static const unsigned long DEBOUNCE_MS = 50;
static int           last_btn_level = HIGH;   // HIGH = not pressed (pull-up)
static unsigned long last_btn_change = 0;

// --- Recording state ---
static bool recording = false;

static void beep(int freq_hz, int dur_ms) {
  tone(PIN_BUZZER, freq_hz, dur_ms);
  delay(dur_ms);
  noTone(PIN_BUZZER);
}

static void chirp_ready() {   // "system ready" — two short high beeps
  beep(1500, 80);
  delay(60);
  beep(1500, 80);
}

static void chirp_start() {   // recording started — rising
  beep(900, 100);
  beep(1400, 120);
}

static void chirp_stop() {    // recording stopped — falling
  beep(1400, 100);
  beep(900, 120);
}

void setup() {
  Serial.begin(115200);
  while (!Serial);   // remove this line to run standalone on battery

  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  if (!sensors_begin()) {
    Serial.println("Sensor init failed!");
    // long sad tone so you know it failed without the serial monitor
    beep(300, 500);
    while (1);
  }

  chirp_ready();
  Serial.println("# Ready. Press the button to start/stop recording.");
  next_tick = micros();
}

void loop() {
  // --- button: debounced toggle ---
  int btn = digitalRead(PIN_BUTTON);
  unsigned long now_ms = millis();
  if (btn != last_btn_level && (now_ms - last_btn_change) > DEBOUNCE_MS) {
    last_btn_change = now_ms;
    last_btn_level  = btn;
    if (btn == LOW) {                // press (not release) toggles state
      recording = !recording;
      digitalWrite(LED_BUILTIN, recording ? HIGH : LOW);
      if (recording) {
        Serial.println("# --- recording started ---");
        chirp_start();
      } else {
        Serial.println("# --- recording stopped ---");
        chirp_stop();
      }
      next_tick = micros();          // resync sample clock after beep delay
    }
  }

  // --- steady 100 Hz sampling loop ---
  unsigned long now = micros();
  if ((long)(now - next_tick) < 0) return;
  next_tick += LOOP_US;

  Readings r;
  sensors_read(r);

  if (recording) {
    sensors_print_rpy(r);
  }
}
