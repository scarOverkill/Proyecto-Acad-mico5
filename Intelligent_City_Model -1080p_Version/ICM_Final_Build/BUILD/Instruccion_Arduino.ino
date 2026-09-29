// === Sistema Inteligente de Control de Tráfico ===
// Flujo por defecto, conteo, cruce peatonal y emergencia

//Includes necesarios para la visualizacion
#include <Wire.h>                // Comunicación I2C para controlar la pantalla LCD
#include <LiquidCrystal_I2C.h>  // Librería para manejar pantallas LCD vía I2C

//Inicializacion y dimensionamiento de la pantalla LCD con libreria LiquidCrystal
LiquidCrystal_I2C lcd(0x27, 16, 2);

// === Pines Semáforos Vehiculares ===
int LED_GREEN1 = 13;   //bn 
int LED_RED1  = 12; //bn
int LED_YELLOW1 = 11; // bn

int LED_GREEN2 = 10;// bn 
int LED_YELLOW2 = 9; // bn
int LED_RED2 = 8; //bn

int  LED_RED3= 6;  //bn 
int  LED_YELLOW3 = 7; //bn 
int LED_GREEN3 = 5; //bn

int LED_GREEN4 = 3; //bn
int LED_YELLOW4 = 2;// bn
int LED_RED4  = 4; //bn 

// === Pines Semáforos Peatonales ===
int LED_VERDE_P1 = 24; //bn
int LED_VERDE_P2 = 25; //bn 
int LED_ROJO_P1  = 22; //bn
int LED_ROJO_P2  = 23; //bn

// === Pines Botones ===
int BOTON_P1 = 26;
int BOTON_P2 = 27;


// === Variables globales ===
unsigned long tiempoCambio = 0;
bool enCrucePeatonal = false;
bool emergenciaActiva = false;
bool via1Activa = true;       // Controla cuál vía está activa actualmente
int conteoZ1 = 0;             // Conteo de vehículos recibido por Serial Zona 1
int conteoZ2 = 0;             // Conteo de vehículos recibido por Serial Zona 2

//funcion de set up para inicializacion de componentes
void setup() {
  Serial.begin(9600);
  lcd.init();               // Inicia la LCD
  lcd.backlight();          // Enciende la luz de fondo

  //Inicializacion de los pines de salida por medio de ciclo for
  //Sale mas eficiente en codigo que estar ingresando los pin output 1 a 1
  for (int pin = 2; pin <= 27; pin++) {
    pinMode(pin, OUTPUT);
  }

  pinMode(BOTON_P1, INPUT_PULLUP);
  pinMode(BOTON_P2, INPUT_PULLUP);

  // Estado inicial de los semáforos peatonales
  digitalWrite(LED_ROJO_P1, HIGH);
  digitalWrite(LED_ROJO_P2, HIGH);
  digitalWrite(LED_VERDE_P1, LOW);
  digitalWrite(LED_VERDE_P2, LOW);

  activarZona1();
  tiempoCambio = millis();

  lcd.setCursor(0, 0);
  lcd.print("Sistema iniciado");
  delay(2000);
  lcd.clear();
}

//Instruccion principal que va a realizar el arduino
//Se maneja el comportamiento de los componentes por medio de otras funciones vacias dada la naturaleza y 
//cantidad de cambios necesarios entre outputs e inputs
//Se maneja mas facil por funciones debido a que se tiene que integrar/complementar 
//instrucciones tomando en cuenta otro lenguaje de programacion y librerarias
void loop() {
  leerSerial(); // Escucha instrucciones desde Python/OpenCV

  if (emergenciaActiva) return;

  if (!digitalRead(BOTON_P1) || !digitalRead(BOTON_P2)) {
    activarCrucePeatonal();
    return;
  }

  mostrarEstadoLCD("Luz verde: Z" + String(via1Activa ? "1" : "2"));

  if (millis() - tiempoCambio > 10000) {
    if (conteoZ1 > conteoZ2) activarZona1();
    else if (conteoZ2 > conteoZ1) activarZona2();
    else alternarZona();
    tiempoCambio = millis();
  }
}

//funcion principal que estaria interpretando los inputs de OpenCV en Python para que se efectuen en el arduino
//Python logra hacer la conversion a binario gracias a la libreria serial
void leerSerial() {
  if (Serial.available()) {
    String entrada = Serial.readStringUntil('\n');
    entrada.trim();

    if (entrada.startsWith("EMERGENCIA:1")) activarEmergencia(1);
    else if (entrada.startsWith("EMERGENCIA:2")) activarEmergencia(2);
    else if (entrada.startsWith("Z1:")) {
      int idxZ2 = entrada.indexOf(",Z2:");
      if (idxZ2 != -1) {
        conteoZ1 = entrada.substring(3, idxZ2).toInt();
        conteoZ2 = entrada.substring(idxZ2 + 4).toInt();
      }
    }
  }
}

//Funcion que maneja el comportamiento de vehiculos de emergencia en el arduino
void activarEmergencia(int zona) {
  emergenciaActiva = true;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Emergencia: Zona ");
  lcd.setCursor(0, 1);
  lcd.print(zona);

  bool esZona1 = (zona == 1);

  // Si la vía actual no es la zona con emergencia, hacer transición suave
  if ((esZona1 && !via1Activa) || (!esZona1 && via1Activa)) {
    transicionAmarillaGeneral();  // Transición para apagar vía actual
    apagarSemaforosVehiculares();

    // Activar la zona de emergencia
    if (esZona1) {
      digitalWrite(LED_GREEN1, HIGH);
      digitalWrite(LED_GREEN2, HIGH);
      digitalWrite(LED_RED3, HIGH);
      digitalWrite(LED_RED4, HIGH);
    } else {
      digitalWrite(LED_RED1, HIGH);
      digitalWrite(LED_RED2, HIGH);
      digitalWrite(LED_GREEN3, HIGH);
      digitalWrite(LED_GREEN4, HIGH);
    }
    via1Activa = esZona1;
  }

  delay(5000);

  // Mostrar mensaje temporal
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Retomando flujo");
  lcd.setCursor(0, 1);
  lcd.print("Espere...");
  delay(3000); 

  emergenciaActiva = false;
  tiempoCambio = millis();  // Reinicia el contador de tiempo al salir de emergencia
  lcd.clear();
}

//Funcion que maneja el comportamiento de las LEDs al activar los cruces
void activarCrucePeatonal() {
  enCrucePeatonal = true;

  // Solo la vía activa hace la transición a amarillo y luego rojo
  if (via1Activa) {
    digitalWrite(LED_GREEN1, LOW);
    digitalWrite(LED_GREEN2, LOW);
    digitalWrite(LED_YELLOW1, HIGH);
    digitalWrite(LED_YELLOW2, HIGH);
  } else {
    digitalWrite(LED_GREEN3, LOW);
    digitalWrite(LED_GREEN4, LOW);
    digitalWrite(LED_YELLOW3, HIGH);
    digitalWrite(LED_YELLOW4, HIGH);
  }

  delay(5000); // Amarillo encendido

  if (via1Activa) {
    digitalWrite(LED_YELLOW1, LOW);
    digitalWrite(LED_YELLOW2, LOW);
    digitalWrite(LED_RED1, HIGH);
    digitalWrite(LED_RED2, HIGH);
  } else {
    digitalWrite(LED_YELLOW3, LOW);
    digitalWrite(LED_YELLOW4, LOW);
    digitalWrite(LED_RED3, HIGH);
    digitalWrite(LED_RED4, HIGH);
  }

  // Activar semáforos peatonales en verde
  digitalWrite(LED_ROJO_P1, LOW);
  digitalWrite(LED_ROJO_P2, LOW);
  digitalWrite(LED_VERDE_P1, HIGH);
  digitalWrite(LED_VERDE_P2, HIGH);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Cruce peatonal");
  lcd.setCursor(0, 1);
  lcd.print("Espere...");

  delay(10000); // Tiempo para peatones

  // Regresar a luz roja peatonal
  digitalWrite(LED_VERDE_P1, LOW);
  digitalWrite(LED_VERDE_P2, LOW);
  digitalWrite(LED_ROJO_P1, HIGH);
  digitalWrite(LED_ROJO_P2, HIGH);

  lcd.clear();
  enCrucePeatonal = false;
  tiempoCambio = millis();
}

//Se asegura de funcionar como limpieza para las LEDs
void apagarSemaforosVehiculares() {
  int leds[] = {
    LED_GREEN1, LED_YELLOW1, LED_RED1,
    LED_GREEN2, LED_YELLOW2, LED_RED2,
    LED_GREEN3, LED_YELLOW3, LED_RED3,
    LED_GREEN4, LED_YELLOW4, LED_RED4
  };
  for (int i = 0; i < 12; i++) {
    digitalWrite(leds[i], LOW);
  }
}

//Mismo proposito que la funcion anterior pero en este caso incluye los Todos los LEDs
void apagarTodosSemaforos() {
  apagarSemaforosVehiculares();
  digitalWrite(LED_VERDE_P1, LOW);
  digitalWrite(LED_VERDE_P2, LOW);
  digitalWrite(LED_ROJO_P1, HIGH);
  digitalWrite(LED_ROJO_P2, HIGH);
}

//Zona de los semaforos 1 y 2
void activarZona1() {
  mostrarEstadoLCD("Cambio activo...");
  transicionAmarillaGeneral();
  apagarSemaforosVehiculares();
  digitalWrite(LED_GREEN1, HIGH);
  digitalWrite(LED_GREEN2, HIGH);
  digitalWrite(LED_RED3, HIGH);
  digitalWrite(LED_RED4, HIGH);
  via1Activa = true;
}

//Zona de los semaforos 3 y 4
void activarZona2() {
  mostrarEstadoLCD("Cambio activo...");
  transicionAmarillaGeneral();
  apagarSemaforosVehiculares();
  digitalWrite(LED_RED1, HIGH);
  digitalWrite(LED_RED2, HIGH);
  digitalWrite(LED_GREEN3, HIGH);
  digitalWrite(LED_GREEN4, HIGH);
  via1Activa = false;
}

//Maneja cambio de luces entre las zonas correspondientes
void alternarZona() {
  if (via1Activa) activarZona2();
  else activarZona1();
}

//Funcion de transicion para los LSDs amarillos
void transicionAmarillaGeneral() {
  if (via1Activa) {
    // Solo hacer transición si los verdes están activos
    if (digitalRead(LED_GREEN1) == HIGH || digitalRead(LED_GREEN2) == HIGH) {
      digitalWrite(LED_GREEN1, LOW);
      digitalWrite(LED_GREEN2, LOW);
      digitalWrite(LED_YELLOW1, HIGH);
      digitalWrite(LED_YELLOW2, HIGH);
      delay(5000);
      digitalWrite(LED_YELLOW1, LOW);
      digitalWrite(LED_YELLOW2, LOW);
      digitalWrite(LED_RED1, HIGH);
      digitalWrite(LED_RED2, HIGH);
    }
  } else {
    if (digitalRead(LED_GREEN3) == HIGH || digitalRead(LED_GREEN4) == HIGH) {
      digitalWrite(LED_GREEN3, LOW);
      digitalWrite(LED_GREEN4, LOW);
      digitalWrite(LED_YELLOW3, HIGH);
      digitalWrite(LED_YELLOW4, HIGH);
      delay(5000);
      digitalWrite(LED_YELLOW3, LOW);
      digitalWrite(LED_YELLOW4, LOW);
      digitalWrite(LED_RED3, HIGH);
      digitalWrite(LED_RED4, HIGH);
    }
  }
}

//Funcion para mostrar estado de flujo vehicular en LCD
void mostrarEstadoLCD(String mensajeLinea2) {
  lcd.setCursor(0, 0);
  lcd.print("Z1:"); lcd.print(conteoZ1);
  lcd.print(" Z2:"); lcd.print(conteoZ2);
  lcd.print("   "); // Limpieza de caracteres sobrantes

  lcd.setCursor(0, 1);
  lcd.print(mensajeLinea2);
  int espacios = 16 - mensajeLinea2.length();
  for (int i = 0; i < espacios; i++) lcd.print(" "); // Rellena espacios si el texto es corto
}