/*
 * OpenInfra IoT Sensor - ESP8266 (Fake Data Mode)
 * Drainage System Water Level Monitor - FAKE DATA
 * 
 * Hardware:
 * - ESP8266 (NodeMCU/Wemos D1 Mini)
 * 
 * Data Flow: ESP8266 -> HTTP POST -> IoT Producer -> Kafka -> Consumer -> MongoDB
 * 
 * Copyright 2025 VKU.OneLove - Apache License 2.0
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURATION ====================
// WiFi credentials
const char* WIFI_SSID     = "";
const char* WIFI_PASSWORD = "";

// IoT Producer API endpoint
// TODO: ĐỔI YOUR_SERVER_IP THÀNH SERVER THẬT (IP hoặc domain)
const char* IOT_API_URL = "https://api.openinfra.space/api/iot/reading";

// API key thật của bạn
const char* IOT_API_KEY = "";

// Sensor identification
const char* SENSOR_ID = "drainage-sensor-001";
const char* ASSET_ID  = "69298e9e3127bed87ace1a93";  // Asset ID cụ thể của drainage

// Measurement configuration
const float PIPE_HEIGHT_CM      = 100.0;        // Chiều cao ống giả định 100cm -> 1m
const int   READING_INTERVAL_MS = 5000;         // Gửi mỗi 5 giây
// ==================== GLOBAL VARIABLES ====================
WiFiClient wifiClient;
unsigned long lastReadingTime = 0;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(100);

  Serial.println("\n\n========================================");
  Serial.println("OpenInfra IoT Sensor - Drainage Monitor (FAKE DATA)");
  Serial.println("========================================");

  // Seed random (dùng ADC nhiễu để random)
  randomSeed(analogRead(A0));

  // Connect to WiFi
  connectWiFi();

  Serial.println("Setup complete!");
}

// ==================== MAIN LOOP ====================
void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    connectWiFi();
  }

  // Send reading at interval
  unsigned long currentTime = millis();
  if (currentTime - lastReadingTime >= READING_INTERVAL_MS) {
    lastReadingTime = currentTime;
    sendSensorReading();
  }

  delay(100);  // Small delay to prevent watchdog
}

// ==================== WIFI CONNECTION ====================
void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\nWiFi connection failed! Restarting...");
    ESP.restart();
  }
}

// ==================== FAKE SENSOR ====================
// Fake mực nước theo kiểu "dao động nhẹ" để nhìn log cho giống thật
float generateFakeWaterLevel() {
  static float level_m = 0.30;  // 0.3m ban đầu

  // Thay đổi mỗi lần gửi: -0.05m -> +0.05m
  float delta = (float)random(-5, 6) / 100.0;  // -0.05 .. +0.05
  level_m += delta;

  // Clamp trong [0, 1m]
  if (level_m < 0.0) level_m = 0.0;
  if (level_m > (PIPE_HEIGHT_CM / 100.0)) level_m = PIPE_HEIGHT_CM / 100.0;

  return level_m;
}

// Fake battery 30–100%
int generateFakeBattery() {
  return random(30, 101);
}

// ==================== SEND DATA ====================
void sendSensorReading() {
  Serial.println("\n--- Sending FAKE sensor reading ---");

  // Fake sensor values
  float waterLevel_m   = generateFakeWaterLevel();
  int   batteryPercent = generateFakeBattery();
  int   rssi           = WiFi.RSSI();

  Serial.print("Fake water level: ");
  Serial.print(waterLevel_m, 2);
  Serial.println(" m");

  Serial.print("Fake battery: ");
  Serial.print(batteryPercent);
  Serial.println("%");

  Serial.print("RSSI: ");
  Serial.print(rssi);
  Serial.println(" dBm");

  // Build JSON payload
  StaticJsonDocument<512> doc;
  doc["sensor_id"] = SENSOR_ID;
  doc["asset_id"]  = ASSET_ID;

  JsonObject readings = doc.createNestedObject("readings");
  readings["water_level"] = waterLevel_m;

  doc["battery"] = batteryPercent;
  doc["rssi"]    = rssi;

  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["firmware_version"] = "1.0.0-fake";
  metadata["device_type"]      = "ESP8266";
  metadata["mode"]             = "fake";

  String payload;
  serializeJson(doc, payload);

  Serial.print("Payload: ");
  Serial.println(payload);

  // Send HTTP POST request
  HTTPClient http;
  http.begin(wifiClient, IOT_API_URL);
  http.addHeader("Content-Type", "application/json");

  // Add API key header
  if (strlen(IOT_API_KEY) > 0) {
    http.addHeader("X-API-Key", IOT_API_KEY);
  }

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpCode);

    if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED) {
      String response = http.getString();
      Serial.print("Response: ");
      Serial.println(response);
    }
  } else {
    Serial.print("HTTP Error: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
}
