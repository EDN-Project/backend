#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define WIFI_SSID "elfagr"
#define WIFI_PASSWORD "ahlyahly****10"

#define MQTT_BROKER "test.mosquitto.org"
#define MQTT_PORT 1883

#define MQTT_TOPIC "esp32/eden"
#define ALERT_TOPIC "esp32/alert"
#define LIGHT_TOPIC "esp32/light"
#define SALT_TOPIC "esp32/salt"
#define HUM_TOPIC "esp32/humidity"

#define DHTPIN 4
#define DHTTYPE DHT22

#define LED_PIN 16        // ليد الحرارة
#define LED2_PIN 14       // ليد الإضاءة
#define LED3_PIN 12       // ليد TDS
#define LED4_PIN 17    
#define LDR_PIN 34       // مستشعر الإضاءة (تم تغييره لتفادي التعارض)
#define TDS_PIN 35       // مستشعر TDS

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastMsgTime = 0;
const long interval = 3600000; // ساعة

unsigned long led1StartTime = 0;
unsigned long led2StartTime = 0;
unsigned long led3StartTime = 0;
unsigned long led4StartTime = 0;

bool led1Active = false;
bool led2Active = false;
bool led3Active = false;
bool led4Active = false;

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to WiFi ");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");

  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setKeepAlive(4000);
  client.setCallback(callback);
  reconnectMQTT();
  dht.begin();

  pinMode(LED_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(LED3_PIN, OUTPUT);
  pinMode(LED4_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);
  digitalWrite(LED3_PIN, LOW);
  digitalWrite(LED4_PIN, LOW);

  pinMode(LDR_PIN, INPUT);
  pinMode(TDS_PIN, INPUT);

  sendSensorData(); // أول قراءة
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi Disconnected! Reconnecting...");
    WiFi.disconnect();
    WiFi.reconnect();
    delay(5000);
  }

  if (!client.connected()) {
    reconnectMQTT();
  }

  client.loop();

  unsigned long now = millis();
  if (now - lastMsgTime >= interval) {
    lastMsgTime = now;
    sendSensorData(); // إرسال القيم كل ساعة
  }

  if (led1Active && (now - led1StartTime >= 10000)) {
    digitalWrite(LED_PIN, LOW);
    led1Active = false;
    Serial.println("🔴 LED OFF - Temperature timeout");
  }

  if (led2Active && (now - led2StartTime >= 10000)) {
    digitalWrite(LED2_PIN, LOW);
    led2Active = false;
    Serial.println("🔴 LED2 OFF - Light timeout");
  }

  if (led3Active && (now - led3StartTime >= 10000)) {
    digitalWrite(LED3_PIN, LOW);
    led3Active = false;
    Serial.println("🔴 LED3 OFF - TDS timeout");
  }

  if (led4Active && (now - led4StartTime >= 10000)) {
    digitalWrite(LED4_PIN, LOW);
    led4Active = false;
    Serial.println("🔴 LED4 OFF - HUM timeout");
  }

}

void reconnectMQTT() {
  if (client.connected()) return;

  Serial.println("Checking MQTT connection...");
  int maxRetries = 5;
  int attempt = 0;

 while (!client.connected() && attempt < maxRetries) {
  Serial.print("Attempting MQTT connection... (Try ");
  Serial.print(attempt + 1);
  Serial.println(")");

  if (client.connect("eden")) {
    Serial.println("MQTT Connected!");
    client.subscribe(ALERT_TOPIC);
    client.subscribe(LIGHT_TOPIC);
    client.subscribe(SALT_TOPIC); 
    client.subscribe(HUM_TOPIC);
    return;
  } else {
    Serial.print("MQTT Failed, rc=");
    Serial.print(client.state());
    Serial.println(" Retrying...");
  }

  attempt++;
  delay(10000);  // زيادة التأخير بين المحاولات (10 ثواني)
}

  if (!client.connected()) {
    Serial.println("Max retries reached. Waiting before retrying...");
    delay(30000);
  }
}

void sendSensorData() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int ldrValue = analogRead(LDR_PIN);
  int tdsValue = analogRead(TDS_PIN); // قراءة TDS بشكل صحيح

  if (!isnan(temperature) && !isnan(humidity) && !isnan(ldrValue) && !isnan(tdsValue)) {
    String payload = "{";
    payload += "\"temperature\": " + String(temperature) + ", ";
    payload += "\"humidity\": " + String(humidity) + ", ";
    payload += "\"light\": " + String(ldrValue) + ", "; // نشر قيمة الـ LDR
    payload += "\"salt\": " + String(tdsValue); // نشر قيمة الـ TDS
    payload += "}";

    client.publish(MQTT_TOPIC, payload.c_str(), true);
    Serial.println("Published: " + payload);
  } else {
    Serial.println("Failed to read from DHT sensor!");
  }
}


void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message received on topic ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(message);

  String topicStr = String(topic);
  int value = message.toInt();

  if (topicStr == ALERT_TOPIC && value == 1) {
    Serial.println("🔥 High temperature detected! Turning LED ON for 10 seconds.");
    digitalWrite(LED_PIN, HIGH);
    led1StartTime = millis();
    led1Active = true;
  }

  if (topicStr == LIGHT_TOPIC && value == 2) {
    Serial.println("💡 Light command received! Turning LED2 ON for 10 seconds.");
    digitalWrite(LED2_PIN, HIGH);
    led2StartTime = millis();
    led2Active = true;
  }

  if (topicStr == SALT_TOPIC && value == 3) {
    Serial.println("🧂 Salt alert received! Turning LED3 ON for 10 seconds.");
    digitalWrite(LED3_PIN, HIGH);
    led3StartTime = millis();
    led3Active = true;
  }

  if (topicStr == HUM_TOPIC && value == 4) {
    Serial.println("Hum alert received! Turning LED4 ON for 10 seconds.");
    digitalWrite(LED4_PIN, HIGH);
    led4StartTime = millis();
    led4Active = true;
  }
}