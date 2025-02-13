#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* ssid = "ESP_Server_123";  // WiFi Name
const char* password = "12345678";    // WiFi Password

ESP8266WebServer server(80);
String sensorData = "Waiting for data...";

void setup() {
  Serial.begin(115200);         // Communication with Arduino
  WiFi.softAP(ssid, password);  // Create ESP Wi-Fi Network

  server.on("/", []() {
    server.send(200, "text/plain", sensorData);  // Serve Sensor Data
  });

  server.begin();
}

void loop() {
  if (Serial.available()) {
    sensorData = Serial.readStringUntil('\n');  // Read data from Arduino
  }
  server.handleClient();
}
