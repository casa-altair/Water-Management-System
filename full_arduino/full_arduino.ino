#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <SoftwareSerial.h>

#define TRIG 7
#define ECHO 6
#define PH_SENSOR A0
#define TDS_SENSOR A1
#define TURBIDITY_SENSOR A2

#define RELAY_PUMP 11
#define RELAY_ACID 8
#define RELAY_BASE 10
#define RELAY_NEUTRAL 9

const int tankHeight = 30;  // Define your tank height in cm
float waterLevelPercent = 0;
unsigned long lastSendTime = 0;
unsigned long displastSendTime = 0;
float waterLevelPercent_var = 0;



LiquidCrystal_I2C lcd(0x27, 16, 2);

// Serial for ESP8266
SoftwareSerial espSerial(2, 3);  // RX, TX

void setup() {
  Serial.begin(9600);
  espSerial.begin(115200);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(RELAY_PUMP, OUTPUT);
  pinMode(RELAY_ACID, OUTPUT);
  pinMode(RELAY_BASE, OUTPUT);
  pinMode(RELAY_NEUTRAL, OUTPUT);

  digitalWrite(RELAY_PUMP, HIGH);
  digitalWrite(RELAY_ACID, HIGH);
  digitalWrite(RELAY_BASE, HIGH);
  digitalWrite(RELAY_NEUTRAL, HIGH);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Water Quality");
  lcd.setCursor(0, 1);
  lcd.print("Monitoring...");
  delay(2000);
}

float getWaterLevel() {
  int water_perc = 0;
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duration = pulseIn(ECHO, HIGH);
  if (duration) {
    float distance = duration * 0.034 / 2;
    water_perc = (1 - (distance / tankHeight)) * 100;
  }

  return water_perc;
}

void controlPump(float waterLevelPercent) {
  if ((waterLevelPercent > 0) && (waterLevelPercent < 70)) {
    digitalWrite(RELAY_PUMP, LOW);
  } else if ((waterLevelPercent > 70) && (waterLevelPercent < 100)) {
    digitalWrite(RELAY_PUMP, HIGH);
  }

  else {
    digitalWrite(RELAY_PUMP, HIGH);
  }
}

void controlPH(float ph) {
  if (ph < 6.5) {
    digitalWrite(RELAY_BASE, LOW);
    digitalWrite(RELAY_ACID, HIGH);
  } else if (ph > 7.5) {
    digitalWrite(RELAY_ACID, LOW);
    digitalWrite(RELAY_BASE, HIGH);
  } else {
    digitalWrite(RELAY_BASE, HIGH);
    digitalWrite(RELAY_ACID, HIGH);
  }
}

void updateLCD(float ph, float tds, float turbidity, float water) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("pH: ");
  lcd.print(ph);
  lcd.setCursor(8, 0);
  lcd.print("TDS:");
  lcd.print(tds);

  lcd.setCursor(0, 1);
  lcd.print("Tur: ");
  lcd.print(turbidity);
  lcd.setCursor(8, 1);
  lcd.print("Lvl:");
  lcd.print(water);
  lcd.print("%");
}

void loop() {
  float phValue = analogRead(PH_SENSOR) * (14.0 / 1023.0);
  float tdsValue = analogRead(TDS_SENSOR) * (5.0 / 1023.0);
  float turbidity = analogRead(TURBIDITY_SENSOR) * (5.0 / 1023.0);
  float chk_waterLevelPercent_var = getWaterLevel();
  if (chk_waterLevelPercent_var > 0.00) {
    waterLevelPercent_var = chk_waterLevelPercent_var;
  }
  Serial.println(waterLevelPercent_var);


  controlPump(waterLevelPercent_var);
  // controlPH(phValue);

  if (millis() - displastSendTime > 500) {
    displastSendTime = millis();
    updateLCD(phValue, tdsValue, turbidity, waterLevelPercent_var);
  }

  if (millis() - lastSendTime > 1000) {
    lastSendTime = millis();
    Serial.println("Write data");
    espSerial.print(phValue);
    Serial.print(phValue);
    espSerial.print(",");
    Serial.print(",");
    espSerial.print(tdsValue);
    Serial.print(tdsValue);
    espSerial.print(",");
    Serial.print(",");
    espSerial.print(turbidity);
    Serial.print(turbidity);
    espSerial.print(",");
    Serial.print(",");
    espSerial.println(waterLevelPercent_var);
    Serial.println(waterLevelPercent_var);
  }
}
