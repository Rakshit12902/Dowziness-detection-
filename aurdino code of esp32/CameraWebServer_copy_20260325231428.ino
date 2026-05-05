#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

const char *ssid = "moto";
const char *password = "12345678";

WebServer server(80);

// Pins
#define BUZZER_PIN 12
#define LED_PIN 4

void startCameraServer();

void setup() {
  Serial.begin(115200);
  Serial.println();

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  // ================= CAMERA CONFIG =================
  camera_config_t config;

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;

  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;

  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href = 23;

  config.pin_sccb_sda = 26;
  config.pin_sccb_scl = 27;

  config.pin_pwdn = 32;
  config.pin_reset = -1;

  config.xclk_freq_hz = 16000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // 🔥 OPTIMIZED FOR NO PSRAM
  config.frame_size = FRAMESIZE_QVGA;     // 320x240 (BEST)
  config.jpeg_quality = 12;               // clear + small
  config.fb_count = 1;
  config.fb_location = CAMERA_FB_IN_DRAM;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

  // ================= INIT CAMERA =================
  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("❌ Camera init failed");
    return;
  }

  // 🔥 SENSOR OPTIMIZATION (IMPORTANT)
  sensor_t *s = esp_camera_sensor_get();
  s->set_brightness(s, 2);
  s->set_contrast(s, 1);
  s->set_saturation(s, 1);
  s->set_sharpness(s, 2);
  // extra exposure
  s->set_gain_ctrl(s, 1);      // enable auto gain
  s->set_exposure_ctrl(s, 1);  // enable auto exposure
  s->set_awb_gain(s, 1);       // auto white balance

// Optional boost
  s->set_aec2(s, 1);   

  // ================= WIFI =================
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("Connecting...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // ================= CAMERA SERVER =================
  startCameraServer();

  // ================= BUZZER API =================
  server.on("/on", HTTP_GET, []() {
    digitalWrite(BUZZER_PIN, HIGH);
    server.send(200, "text/plain", "Buzzer ON");
  });

  server.on("/off", HTTP_GET, []() {
    digitalWrite(BUZZER_PIN, LOW);
    server.send(200, "text/plain", "Buzzer OFF");
  });

  server.begin();

  Serial.println("🚀 Server started");
  Serial.print("Camera: http://");
  Serial.println(WiFi.localIP());
}

void loop() {
  server.handleClient();
}