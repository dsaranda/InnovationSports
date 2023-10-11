/*
Este programa controla un dispositivo que consta de un microcontrolador Wemos D1 mini conectado a un sensor Sharp IR y un anillo de luz LED Neopixel RGB. El programa también se comunica con un servidor MQTT y se suscribe a un tema para recibir comandos de encendido y apagado de la luz.

Los datos de tiempo de detección de movimiento se guardan en una base de datos InfluxDB y se visualizan en Grafana.

El sensor se usa para detectar el movimiento en la zona de interacción del usuario. Cuando se detecta movimiento, se genera una rutina de entrenamiento para mejorar la velocidad y la coordinación. Las luces se encienden y apagan según el movimiento detectado.

*/
#include <SharpIR.h>
#include <Adafruit_NeoPixel.h> 
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#ifdef __AVR__
#include <avr/power.h>
#endif

// Establece el nombre y la contraseña de la red Wi-Fi
const char* ssid = "MovistarFibra-58E3EF";
const char* password = "Notecalentes123.";

// Establece la dirección del servidor MQTT
const char* mqtt_server = "192.168.1.56";

WiFiClient espClient;
PubSubClient client(espClient);

// Define el pin de salida de la luz LED
#define LED_PIN D5

// Define los pines de entrada del sensor y la cantidad de píxeles en el anillo LED
#define PIN        14 
#define NUMPIXELS 24 

// Inicializa el objeto Adafruit_NeoPixel
Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

// Inicializa el objeto SharpIR
SharpIR sensor( SharpIR::GP2Y0A41SK0F, A0 );

// Variables para el seguimiento del tiempo y el movimiento detectado
unsigned long startTime; 
unsigned long endTime; 
bool motionDetected = false; 
unsigned long milis; 

// Variable para el seguimiento del estado de la luz
bool lightOn = false;

// Función para recibir comandos de encendido y apagado de la luz desde el servidor MQTT
void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  if (message == "on") { // si recibe un mensaje con la palabra "on" se encienden las luces
    digitalWrite(LED_PIN, HIGH);
    int i;
    int ant = -1;
    for(i=0;i<24;i++) // Recorre los 24 píxeles del anillo de luz NeoPixel
    {
    pixels.setPixelColor(i, pixels.Color(50, 0, 0));
    pixels.show();
    ant ++;
    delay(3); // Espera 3 milisegundos antes de pasar al siguiente píxel
    }
    lightOn = true; // Si se encienden las luces las variable LigthOn que es boolean se pone en True
  } else if (message == "off") { // si recibe un mensaje con la palabra "off" se apagan las luces
    digitalWrite(LED_PIN, LOW);
    int i;
    int ant = -1;
    for(i=0;i<24;i++) // Recorre los 24 píxeles del anillo de luz NeoPixel
    {
    pixels.setPixelColor(i, pixels.Color(0, 0, 0));
    pixels.show();
    ant ++;
    delay(3); // Espera 3 milisegundos antes de pasar al siguiente píxel
    }
    lightOn = false; // Si se apagan las luces la variable LigthOn que es boolean se pone en False
   }
}

// Función de configuración inicial
void setup() {
  #if defined(__AVR_ATtiny85__)
  if (F_CPU == 16000000) clock_prescale_set(clock_div_1);
  #endif
  // END of Trinket-specific code.
  Serial.begin( 115200 ); // Inicializa el puerto serial a 115200 baudios
  WiFi.mode(WIFI_STA); // Configura el modo Wi-Fi como cliente
  WiFi.begin(ssid, password); // Configura el modo Wi-Fi como cliente
  client.setServer(mqtt_server, 1883); // Configura la dirección y puerto del servidor MQTT
  while (!client.connected()) { // Bucle mientras el cliente MQTT no está conectado
    if (client.connect("arduinoClient3")) { // Intenta conectarse con un nombre de cliente
    } else {
      delay(5000); // Espera 5 segundos antes de intentar conectarse de nuevo
    }
  }
  client.subscribe("encender_luz3"); // Se suscribe al tópico "encender_luz3" para recibir mensajes MQTT
  client.setCallback(callback); // Configura la función de devolución de llamada para manejar los mensajes MQTT
  pixels.begin(); // Inicializa el objeto pixels
} 

void loop() {
  int distance = sensor.getDistance(); // Lee la distancia del sensor Sharp IR
  if (distance < 5) { // Si la distancia es menor que 5 cm (detecta movimiento)
    if (!motionDetected && lightOn) {  // Si el movimiento no ha sido detectado anteriormente y la luz está encendida
      startTime = millis(); // Registra el tiempo de inicio
      motionDetected = true; // Marca que se ha detectado movimiento
      client.publish("detectado3", "si"); // Publica un mensaje MQTT para indicar que se ha detectado movimiento
      milis = startTime - endTime; // Calcula el tiempo transcurrido desde la última detección de movimiento
      lightOn = false;  // Apaga la luz
      client.publish("elapsed_time3", String(milis).c_str()); // Publica un mensaje MQTT con el tiempo transcurrido
      startTime = 0; // Reinicia el tiempo de inicio
      milis = 0;  // Reinicia el tiempo transcurrido
    }
    int i;
    int ant = -1;
    for(i=0;i<24;i++) // Recorre los 24 píxeles del anillo de luz NeoPixel
    {
    pixels.setPixelColor(i, pixels.Color(0, 0, 0)); // Establece el color del píxel en negro (apagado)
    pixels.show(); // Muestra el nuevo color del píxel
    ant ++;
    delay(3); // Espera 3 milisegundos antes de pasar al siguiente píxel
    }
  } else {
    if (motionDetected && lightOn) { // Si se había detectado movimiento anteriormente y la luz está encendida
      endTime = millis();  // Registra el tiempo de finalización
      motionDetected = false;  // Marca que ya no se ha detectado movimiento
    }
    delay(3);  // Espera 3 milisegundos antes de continuar
  }
  client.loop(); // Mantiene la conexión MQTT activa
}
