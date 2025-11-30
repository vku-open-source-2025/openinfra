/*
 * OpenInfra IoT Sensor - ESP8266
 * Drainage System Water Level Monitor
 * 
 * Hardware:
 * - ESP8266 (NodeMCU/Wemos D1 Mini)
 * - HC-SR04 Ultrasonic Distance Sensor (water level)
 * - Optional: Flow sensor, temperature sensor
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
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// IoT Producer API endpoint
const char* IOT_API_URL = "http://YOUR_SERVER_IP:8001/api/iot/reading";
const char* IOT_API_KEY = "YOUR_API_KEY";  // Optional authentication

// Sensor identification
const char* SENSOR_ID = "drainage-sensor-001";
const char* ASSET_ID = "69298e9e3127bed87ace1a93";  // The specific drainage asset

// HC-SR04 Ultrasonic sensor pins
const int TRIG_PIN = D1;  // GPIO5
const int ECHO_PIN = D2;  // GPIO4

// Measurement configuration
const float PIPE_HEIGHT_CM = 100.0;      // Total pipe height in cm
const int READING_INTERVAL_MS = 60000;   // Send reading every 60 seconds
const int READINGS_TO_AVERAGE = 5;       // Number of readings to average

// ==================== GLOBAL VARIABLES ====================
WiFiClient wifiClient;
unsigned long lastReadingTime = 0;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n========================================");
  Serial.println("OpenInfra IoT Sensor - Drainage Monitor");
  Serial.println("========================================");
  
  // Initialize ultrasonic sensor pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
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
  
  delay(100);  // Small delay to prevent watchdog issues
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

// ==================== ULTRASONIC SENSOR ====================
float measureDistance() {
  // Send ultrasonic pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Measure echo duration
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
  
  if (duration == 0) {
    return -1;  // No echo received
  }
  
  // Calculate distance in cm (speed of sound = 343 m/s)
  float distance = (duration * 0.0343) / 2.0;
  return distance;
}

float getAverageDistance() {
  float total = 0;
  int validReadings = 0;
  
  for (int i = 0; i < READINGS_TO_AVERAGE; i++) {
    float distance = measureDistance();
    if (distance > 0 && distance < 400) {  // Valid range
      total += distance;
      validReadings++;
    }
    delay(50);
  }
  
  if (validReadings == 0) {
    return -1;
  }
  
  return total / validReadings;
}

float calculateWaterLevel() {
  float distance = getAverageDistance();
  
  if (distance < 0) {
    return -1;  // Invalid reading
  }
  
  // Water level = pipe height - distance to water surface
  float waterLevel = PIPE_HEIGHT_CM - distance;
  
  // Clamp to valid range
  if (waterLevel < 0) waterLevel = 0;
  if (waterLevel > PIPE_HEIGHT_CM) waterLevel = PIPE_HEIGHT_CM;
  
  // Convert to meters
  return waterLevel / 100.0;
}

// ==================== BATTERY MONITORING ====================
int getBatteryPercentage() {
  // Read ADC (A0 pin)
  int adcValue = analogRead(A0);
  
  // Map ADC value to battery percentage
  // Assuming voltage divider: 4.2V max -> 1V at A0, 3.0V min -> 0.71V at A0
  // ADC range: 0-1024 for 0-1V
  int percentage = map(adcValue, 727, 1024, 0, 100);
  percentage = constrain(percentage, 0, 100);
  
  return percentage;
}

// ==================== SEND DATA ====================
void sendSensorReading() {
  Serial.println("\n--- Taking sensor reading ---");
  
  // Get sensor values
  float waterLevel = calculateWaterLevel();
  int batteryPercent = getBatteryPercentage();
  int rssi = WiFi.RSSI();
  
  Serial.print("Water level: ");
  if (waterLevel >= 0) {
    Serial.print(waterLevel, 2);
    Serial.println(" m");
  } else {
    Serial.println("INVALID");
  }
  Serial.print("Battery: ");
  Serial.print(batteryPercent);
  Serial.println("%");
  Serial.print("RSSI: ");
  Serial.print(rssi);
  Serial.println(" dBm");
  
  // Build JSON payload
  StaticJsonDocument<512> doc;
  doc["sensor_id"] = SENSOR_ID;
  doc["asset_id"] = ASSET_ID;
  
  // Get current time (you could add NTP sync for real timestamps)
  // For now, let the server set the timestamp
  
  JsonObject readings = doc.createNestedObject("readings");
  if (waterLevel >= 0) {
    readings["water_level"] = waterLevel;
  }
  // Add more readings here as you add sensors
  // readings["flow_rate"] = flowRate;
  // readings["temperature"] = temperature;
  
  doc["battery"] = batteryPercent;
  doc["rssi"] = rssi;
  
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["firmware_version"] = "1.0.0";
  metadata["device_type"] = "ESP8266";
  
  String payload;
  serializeJson(doc, payload);
  
  Serial.print("Payload: ");
  Serial.println(payload);
  
  // Send HTTP POST request
  HTTPClient http;
  http.begin(wifiClient, IOT_API_URL);
  http.addHeader("Content-Type", "application/json");
  
  // Add API key if configured
  if (strlen(IOT_API_KEY) > 0) {
    http.addHeader("X-API-Key", IOT_API_KEY);
  }
  
  int httpCode = http.POST(payload);
  
  if (httpCode > 0) {
    Serial.print("HTTP Response: ");
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
