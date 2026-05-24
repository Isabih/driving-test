// Include required libraries
#include <DHT.h>

// Pin definitions
#define DHTPIN 5            // DHT11 sensor pin
#define DHTTYPE DHT11       // DHT11 type
#define LIGHT_SENSOR_PIN A0 // Light sensor pin (analog)
#define RAIN_SENSOR_PIN 6   // Rain sensor pin (digital)
#define LIGHT_LED_PIN 8     // Light LED pin
#define TEMP_LED_PIN 9      // Temperature LED pin
#define RAIN_LED_PIN 7      // Rain LED pin

// L298N Motor Driver Pins
#define MOTOR_IN1_PIN 10    // IN1 pin of L298N
#define MOTOR_IN2_PIN 11    // IN2 pin of L298N
#define MOTOR_EN_PIN 12     // EN pin of L298N (for motor speed or enabling motor)

// Thresholds
const int lightThreshold = 700;   // Adjust based on your light sensor
const float tempThreshold = 30.0; // 30°C temperature threshold

// Create DHT sensor object
DHT dht(DHTPIN, DHTTYPE);

// Motor state (to track if the tent is open or closed)
bool tentIsOpen = false;

void setup() {
  // Initialize serial communication for debugging
  Serial.begin(9600);

  // Initialize DHT11 sensor
  dht.begin();

  // Initialize pins
  pinMode(LIGHT_SENSOR_PIN, INPUT);
  pinMode(RAIN_SENSOR_PIN, INPUT);
  pinMode(LIGHT_LED_PIN, OUTPUT);
  pinMode(TEMP_LED_PIN, OUTPUT);
  pinMode(RAIN_LED_PIN, OUTPUT);

  // Initialize motor control pins
  pinMode(MOTOR_IN1_PIN, OUTPUT);
  pinMode(MOTOR_IN2_PIN, OUTPUT);
  pinMode(MOTOR_EN_PIN, OUTPUT);
}

void loop() {
  // Read sensor values
  int lightValue = analogRead(LIGHT_SENSOR_PIN);
  int rainValue = digitalRead(RAIN_SENSOR_PIN);
  float temperature = dht.readTemperature();

  // Debugging information
  Serial.print("Light: ");
  Serial.print(lightValue);
  Serial.print(" | Temperature: ");
  Serial.print(temperature);
  Serial.print("°C | Rain: ");
  Serial.println(rainValue == HIGH ? "Yes" : "No");

  // Light LED control
  digitalWrite(LIGHT_LED_PIN, lightValue > lightThreshold ? HIGH : LOW);
  
  // Temperature LED control
  digitalWrite(TEMP_LED_PIN, temperature > tempThreshold ? HIGH : LOW);
  
  // Rain LED control
  digitalWrite(RAIN_LED_PIN, rainValue == HIGH ? LOW : HIGH);

  // Tent control logic based on rain and light
  if (rainValue == HIGH || lightValue > lightThreshold) {
    // If rain is detected or light exceeds threshold, close the tent if it's not already closed
    if (tentIsOpen) {
      closeTent();
    }
  } else {
    // If no rain and light is below the threshold, open the tent if it's not already open
    if (!tentIsOpen) {
      openTent();
    }
  }


  if (lightValue > lightThreshold) {
    // If rain is detected or light exceeds threshold, close the tent if it's not already closed
    if (tentIsOpen) {
      closeTent();
    }
  } else {
    // If no rain and light is below the threshold, open the tent if it's not already open
    if (!tentIsOpen) {
      openTent();
    }
  }


  // Delay to avoid flooding the serial monitor
  delay(2000);
}

// Function to open the tent
void openTent() {
  Serial.println("Opening the tent...");
  // Set motor direction for opening the tent
  digitalWrite(MOTOR_IN1_PIN, HIGH);
  digitalWrite(MOTOR_IN2_PIN, LOW);
  analogWrite(MOTOR_EN_PIN, 255); // Start motor at full speed (PWM value 255)
  
  delay(5000); // Adjust this delay to match the time needed to fully open the tent

  // Stop the motor
  analogWrite(MOTOR_EN_PIN, 0);   // Stop motor (set speed to 0)
  tentIsOpen = true;              // Update state
}

// Function to close the tent
void closeTent() {
  Serial.println("Closing the tent...");
  // Set motor direction for closing the tent
  digitalWrite(MOTOR_IN1_PIN, LOW);
  digitalWrite(MOTOR_IN2_PIN, HIGH);
  analogWrite(MOTOR_EN_PIN, 255); // Start motor at full speed (PWM value 255)
  
  delay(5000); // Adjust this delay to match the time needed to fully close the tent

  // Stop the motor
  analogWrite(MOTOR_EN_PIN, 0);   // Stop motor (set speed to 0)
  tentIsOpen = false;             // Update state
}
