// rotation_viewer.pde
// 3D viewer for the Nano 33 BLE Sense Rev2 pen.
// Expects CSV lines "roll,pitch,yaw,fsr\n" over serial at 115200 baud.
//
// Setup:
//   1. Install Processing from https://processing.org
//   2. Plug in the board. Close the PlatformIO serial monitor (only ONE program can own the port).
//   3. Edit PORT_INDEX below if the wrong port opens — the console prints the list on startup.
//   4. Press Run.

import processing.serial.*;

Serial port;
final int PORT_INDEX = 0;        // index into Serial.list() — change if needed
final int BAUD       = 115200;

float roll  = 0;
float pitch = 0;
float yaw   = 0;
int   fsr   = 0;                 // 0–4095 (12-bit ADC)

void setup() {
  size(800, 600, P3D);
  smooth(8);

  println("Available serial ports:");
  String[] ports = Serial.list();
  for (int i = 0; i < ports.length; i++) println("  [" + i + "] " + ports[i]);

  if (ports.length == 0) {
    println("No serial ports found — plug in the board and restart.");
    return;
  }

  port = new Serial(this, ports[PORT_INDEX], BAUD);
  port.bufferUntil('\n');
}

void draw() {
  background(20);
  lights();

  translate(width / 2, height / 2, 0);

  // Box long axis is along screen X, so:
  //   rotateX = spin about long axis = roll
  //   rotateY = pan left/right         = yaw
  //   rotateZ = nose up/down           = pitch
  rotateX(radians(-roll));
  rotateY(radians(yaw));
  rotateZ(radians(pitch));

  // Pen body: a flat rectangular box
  noStroke();
  fill(80, 170, 255);
  box(280, 40, 80);

  // Tip marker — brightens as force on the FSR increases
  float pressure = constrain(fsr / 4095.0, 0, 1);
  int tipR = (int)lerp(80,  255, pressure);
  int tipG = (int)lerp(80,   40, pressure);
  int tipB = (int)lerp(80,   40, pressure);
  pushMatrix();
  translate(160, 0, 0);
  fill(tipR, tipG, tipB);
  box(40, 20, 20);
  popMatrix();

  // HUD
  camera();
  hint(DISABLE_DEPTH_TEST);
  fill(230);
  textSize(14);
  text("roll  = " + nf(roll,  1, 1),  12, 20);
  text("pitch = " + nf(pitch, 1, 1),  12, 38);
  text("yaw   = " + nf(yaw,   1, 1),  12, 56);
  text("fsr   = " + fsr + "  (" + nf(pressure * 100, 1, 0) + "%)", 12, 74);
  text("Hold still for ~5s on startup so the filter converges.", 12, height - 12);
  hint(ENABLE_DEPTH_TEST);
}

void serialEvent(Serial p) {
  String line = p.readStringUntil('\n');
  if (line == null) return;
  line = trim(line);
  if (line.length() == 0) return;
  if (line.charAt(0) == '#') return;   // skip firmware log lines

  String[] parts = split(line, ',');
  if (parts.length < 4) return;

  try {
    roll  = float(parts[0]);
    pitch = float(parts[1]);
    yaw   = float(parts[2]);
    fsr   = int(parts[3]);
  } catch (Exception e) {
    // ignore malformed lines
  }
}
