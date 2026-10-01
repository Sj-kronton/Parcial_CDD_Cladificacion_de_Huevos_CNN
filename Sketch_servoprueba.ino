#include <Servo.h>

Servo servo;

const int SERVO_PIN = 9;

// =====================================================
// CONTROL DEL SERVO CONTINUO
// =====================================================

const int SERVO_DERECHA = 180;
const int SERVO_IZQUIERDA = 0;
const int SERVO_STOP = 90;

// =====================================================
// TIEMPOS DE MOVIMIENTO
// =====================================================

const int TIEMPO_45 = 65;
const int TIEMPO_85 = 130;
const int TIEMPO_135 = 195;
const int TIEMPO_180 = 260;

// =====================================================
// POSICIÓN ACTUAL DEL MECANISMO
// =====================================================

int posicionActual = 0;

// 0 = OPEN
// 1 = CLOSE
// 2 = REJECT

// =====================================================
// FUNCIONES BÁSICAS
// =====================================================

void detenerServo() {
  servo.write(SERVO_STOP);
  delay(100);

  Serial.println("SERVO: DETENIDO");
}

void moverDerecha(int tiempo) {
  servo.write(SERVO_DERECHA);
  delay(tiempo);
  detenerServo();
}

void moverIzquierda(int tiempo) {
  servo.write(SERVO_IZQUIERDA);
  delay(tiempo);
  detenerServo();
}

// =====================================================
// MOVIMIENTOS DEL MECANISMO
// =====================================================

void abrir() {
  Serial.println("ACCION: OPEN");

  if (posicionActual == 0) {
    Serial.println("Ya esta en OPEN.");
    return;
  }

  if (posicionActual == 1) {
    moverDerecha(TIEMPO_85);
  }

  else if (posicionActual == 2) {
    moverDerecha(TIEMPO_135);
  }

  posicionActual = 0;
  Serial.println("POSICION: OPEN");
}

void cerrar() {
  Serial.println("ACCION: CLOSE");

  if (posicionActual == 1) {
    Serial.println("Ya esta en CLOSE.");
    return;
  }

  if (posicionActual == 0) {
    moverIzquierda(TIEMPO_85);
  }

  else if (posicionActual == 2) {
    moverDerecha(TIEMPO_85);
  }

  posicionActual = 1;
  Serial.println("POSICION: CLOSE");
}

void rechazar() {
  Serial.println("ACCION: REJECT");

  if (posicionActual == 2) {
    Serial.println("Ya esta en REJECT.");
    return;
  }

  if (posicionActual == 0) {
    moverIzquierda(TIEMPO_135);
  }

  else if (posicionActual == 1) {
    moverIzquierda(TIEMPO_85);
  }

  posicionActual = 2;
  Serial.println("POSICION: REJECT");
}

// =====================================================
// SETUP
// =====================================================

void setup() {
  Serial.begin(9600);
  servo.attach(SERVO_PIN);
  servo.write(SERVO_STOP);
  delay(1000);

  Serial.println();
  Serial.println("================================");
  Serial.println(" CLASIFICADOR DE HUEVOS");
  Serial.println(" CONTROLADOR SG90 CONTINUO");
  Serial.println("================================");
  Serial.println("Arduino listo.");
  Serial.println("Estado inicial: OPEN");
  Serial.println();
}

// =====================================================
// LOOP
// =====================================================

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    command.toUpperCase();

    if (command == "OPEN") {
      abrir();
    }

    else if (command == "CLOSE") {
      cerrar();
    }

    else if (command == "REJECT") {
      rechazar();
    }

    else if (command == "RESET") {
      abrir();
    }

    else if (command == "STOP") {
      detenerServo();
    }

    else {
      Serial.print("Comando desconocido: ");
      Serial.println(command);
    }
  }
}
