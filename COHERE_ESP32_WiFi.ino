#include <WiFi.h>
#include <HTTPClient.h>

// 1) Enter the Wi-Fi name and password used by your computer.
const char* WIFI_SSID = "Oppo";
const char* WIFI_PASSWORD = "thufile12";

// 2) Replace 192.168.1.100 with the computer IP printed by cohere_wifi_bridge.py.
String SERVER_URL = "http://192.168.1.100:8000/api/decision";

// Assumes a classic ESP32 DevKit with these GPIOs available.
const int PIN_ALPHA_C = 18;
const int PIN_ALPHA_D = 19;
const int PIN_BETA_C  = 21;
const int PIN_BETA_D  = 22;

struct Button {
  int pin;
  const char* player;
  const char* action;
  int stableState;
  int lastReading;
  unsigned long lastChange;
};

Button buttons[] = {
  {PIN_ALPHA_C, "A", "C", HIGH, HIGH, 0},
  {PIN_ALPHA_D, "A", "D", HIGH, HIGH, 0},
  {PIN_BETA_C,  "B", "C", HIGH, HIGH, 0},
  {PIN_BETA_D,  "B", "D", HIGH, HIGH, 0}
};
const int BUTTON_COUNT = sizeof(buttons) / sizeof(buttons[0]);
const unsigned long DEBOUNCE_MS = 35;

void sendDecision(const char* player, const char* action) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi disconnected; decision was not sent.");
    return;
  }

  HTTPClient http;
  http.setTimeout(2500);
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  String body = String("{\"player\":\"") + player +
                "\",\"action\":\"" + action + "\"}";
  int status = http.POST(body);
  if (status > 0) {
    Serial.printf("Sent %s=%s; HTTP status %d\n", player,
                  strcmp(action, "C") == 0 ? "Cooperate" : "Defect", status);
    String response = http.getString();
    if (response.length()) Serial.println(response);
  } else {
    Serial.printf("Send failed: %s\n", http.errorToString(status).c_str());
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < BUTTON_COUNT; i++) {
    pinMode(buttons[i].pin, INPUT_PULLUP);
    buttons[i].stableState = digitalRead(buttons[i].pin);
    buttons[i].lastReading = buttons[i].stableState;
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(400);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Wi-Fi connected. ESP32 IP: ");
    Serial.println(WiFi.localIP());
    Serial.println("COHERE button prototype ready.");
  } else {
    Serial.println("Wi-Fi connection failed. Check SSID/password and restart.");
  }
}

void loop() {
  unsigned long now = millis();
  for (int i = 0; i < BUTTON_COUNT; i++) {
    int reading = digitalRead(buttons[i].pin);
    if (reading != buttons[i].lastReading) {
      buttons[i].lastChange = now;
      buttons[i].lastReading = reading;
    }
    if ((now - buttons[i].lastChange) > DEBOUNCE_MS && reading != buttons[i].stableState) {
      buttons[i].stableState = reading;
      // INPUT_PULLUP means a pressed button reads LOW.
      if (buttons[i].stableState == LOW) {
        Serial.printf("Button pressed: player %s, action %s\n",
                      buttons[i].player, buttons[i].action);
        sendDecision(buttons[i].player, buttons[i].action);
      }
    }
  }
  delay(2);
}
