import cv2
import numpy as np
import tensorflow as tf
import serial
import time
import tkinter as tk
from tkinter import messagebox
import winsound


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

MODEL_PATH = "best_egg_model.keras"

SERIAL_PORT = "COM3"
BAUDRATE = 9600

IMG_SIZE = (224, 224)

CLASS_NAMES = [
    "broken",
    "dirty",
    "good"
]


# ==========================================================
# TIEMPOS DEL SISTEMA
# ==========================================================

# Análisis inicial después de detectar un posible huevo
INITIAL_ANALYSIS_TIME = 1.0

# Tiempo que permanece cerrado para que el huevo llegue
WAIT_TIME = 2.5

# Segundo período de análisis
SECOND_ANALYSIS_TIME = 4.0

# Tiempo que permanece en posición de rechazo
REJECT_TIME = 2.5


# ==========================================================
# UMBRALES
# ==========================================================

# Probabilidad mínima para considerar una clase dominante
MIN_CONFIDENCE = 0.70

# Porcentaje mínimo de frames que deben coincidir
MIN_CONSISTENCY = 0.70


# ==========================================================
# CARGAR MODELO
# ==========================================================

print("Cargando modelo...")

model = tf.keras.models.load_model(MODEL_PATH)

print("Modelo cargado correctamente.")


# ==========================================================
# CONECTAR ARDUINO
# ==========================================================

print("Conectando con Arduino...")

arduino = serial.Serial(
    SERIAL_PORT,
    BAUDRATE,
    timeout=1
)

# Arduino se reinicia al abrir COM3
time.sleep(2)

print("Arduino conectado.")


# ==========================================================
# ENVIAR COMANDO
# ==========================================================

def send_command(command):

    message = command + "\n"

    arduino.write(message.encode("utf-8"))

    print(f"Arduino <- {command}")


# ==========================================================
# CLASIFICAR ROI
# ==========================================================

def classify_roi(roi):

    roi_rgb = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2RGB
    )

    image = cv2.resize(
        roi_rgb,
        IMG_SIZE
    )

    image = image.astype(np.float32)

    image = np.expand_dims(
        image,
        axis=0
    )

    predictions = model.predict(
        image,
        verbose=0
    )[0]

    predicted_class = np.argmax(predictions)

    confidence = predictions[predicted_class]

    class_name = CLASS_NAMES[predicted_class]

    return class_name, confidence, predictions


# ==========================================================
# OBTENER ROI
# ==========================================================

def get_roi(frame):

    height, width, _ = frame.shape

    roi_width = int(width * 0.60)
    roi_height = int(height * 0.60)

    x1 = (width - roi_width) // 2
    y1 = (height - roi_height) // 2

    x2 = x1 + roi_width
    y2 = y1 + roi_height

    roi = frame[y1:y2, x1:x2]

    return roi, (x1, y1, x2, y2)


# ==========================================================
# ANALIZAR VARIOS FRAMES
# ==========================================================

def analyze_period(cap, duration):

    predictions_list = []

    start_time = time.time()

    while time.time() - start_time < duration:

        ret, frame = cap.read()

        if not ret:
            continue

        roi, coords = get_roi(frame)

        class_name, confidence, predictions = classify_roi(roi)

        predictions_list.append(predictions)

        # Mostrar información
        x1, y1, x2, y2 = coords

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (255, 255, 255),
            2
        )

        broken = predictions[0] * 100
        dirty = predictions[1] * 100
        good = predictions[2] * 100

        cv2.putText(
            frame,
            f"BROKEN: {broken:.1f}%",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"DIRTY: {dirty:.1f}%",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"GOOD: {good:.1f}%",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"PRED: {class_name.upper()}",
            (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.imshow(
            "Egg Classifier - END2END",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            return None


    if len(predictions_list) == 0:
        return None


    # Promedio de probabilidades
    average_predictions = np.mean(
        predictions_list,
        axis=0
    )


    # Clase dominante del promedio
    average_class_index = np.argmax(
        average_predictions
    )

    average_class = CLASS_NAMES[
        average_class_index
    ]

    average_confidence = average_predictions[
        average_class_index
    ]


    # Clase ganadora de cada frame
    frame_classes = [
        np.argmax(pred)
        for pred in predictions_list
    ]


    # Cantidad de frames donde ganó la clase promedio
    consistent_frames = sum(
        c == average_class_index
        for c in frame_classes
    )


    consistency = (
        consistent_frames /
        len(frame_classes)
    )


    return {
        "class": average_class,
        "confidence": average_confidence,
        "consistency": consistency,
        "predictions": average_predictions
    }


# ==========================================================
# DETERMINAR SI ES UN RECHAZO
# ==========================================================

def is_rejection(result):

    if result is None:
        return False

    class_name = result["class"]

    confidence = result["confidence"]

    consistency = result["consistency"]


    if class_name not in ["broken", "dirty"]:
        return False


    if confidence < MIN_CONFIDENCE:
        return False


    if consistency < MIN_CONSISTENCY:
        return False


    return True


# ==========================================================
# ALARMA
# ==========================================================

def human_intervention():

    print()
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("INTERVENCION HUMANA NECESARIA")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    # Sonido
    for _ in range(5):

        winsound.Beep(
            1000,
            500
        )

        time.sleep(0.2)


    # Ventana de intervención
    root = tk.Tk()

    root.withdraw()

    messagebox.showwarning(
        "INTERVENCIÓN HUMANA",
        "Clasificación ambigua.\n\n"
        "El flujo permanece detenido.\n\n"
        "Revise el huevo y presione ACEPTAR "
        "para continuar."
    )

    root.destroy()


# ==========================================================
# CÁMARA
# ==========================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("ERROR: No se pudo abrir la cámara.")

    arduino.close()

    exit()


# ==========================================================
# ESTADO INICIAL
# ==========================================================

send_command("OPEN")

print()
print("========================================")
print("SISTEMA END2END INICIADO")
print("Servo: ABIERTO")
print("========================================")
print()


# ==========================================================
# BUCLE PRINCIPAL
# ==========================================================

try:

    while True:

        # --------------------------------------------------
        # 1. ESPERAR HUEVO
        # --------------------------------------------------

        print("Esperando huevo...")

        result = analyze_period(
            cap,
            INITIAL_ANALYSIS_TIME
        )


        if result is None:
            break


        print(
            f"Analisis inicial: "
            f"{result['class']} "
            f"{result['confidence']:.2%}"
        )


        # --------------------------------------------------
        # 2. ¿HAY POSIBLE HUEVO DEFECTUOSO?
        # --------------------------------------------------

        if is_rejection(result):

            print("Posible huevo defectuoso.")

            send_command("CLOSE")


            # ------------------------------------------------
            # 3. ESPERAR A QUE EL HUEVO LLEGUE AL CIERRE
            # ------------------------------------------------

            print(
                f"Esperando {WAIT_TIME} segundos..."
            )

            time.sleep(WAIT_TIME)


            # ------------------------------------------------
            # 4. SEGUNDO ANÁLISIS
            # ------------------------------------------------

            print("Segundo análisis...")

            second_result = analyze_period(
                cap,
                SECOND_ANALYSIS_TIME
            )


            if second_result is None:
                break


            print(
                f"Resultado final: "
                f"{second_result['class']} "
                f"{second_result['confidence']:.2%}"
            )

            print(
                f"Consistencia: "
                f"{second_result['consistency']:.2%}"
            )


            # ================================================
            # 5. BROKEN / DIRTY CONSISTENTE
            # ================================================

            if is_rejection(second_result):

                print("HUEVO RECHAZADO.")

                send_command("REJECT")

                time.sleep(REJECT_TIME)

                send_command("OPEN")

                print("Flujo restaurado.")


            # ================================================
            # 6. GOOD CONSISTENTE
            # ================================================

            elif (
                second_result["class"] == "good"
                and
                second_result["confidence"] >= MIN_CONFIDENCE
                and
                second_result["consistency"] >= MIN_CONSISTENCY
            ):

                print("HUEVO BUENO.")

                send_command("OPEN")

                print("Flujo restaurado.")


            # ================================================
            # 7. CASO AMBIGUO
            # ================================================

            else:

                print("CLASIFICACIÓN AMBIGUA.")

                # Arduino permanece cerrado
                send_command("CLOSE")

                human_intervention()

                # Después de intervención
                send_command("OPEN")

                print(
                    "Intervención completada."
                )

        else:

            # ------------------------------------------------
            # HUEVO NORMAL
            # ------------------------------------------------

            print(
                "No se detectó un defecto "
                "con suficiente confianza."
            )

            send_command("OPEN")


except KeyboardInterrupt:

    print()
    print("Programa detenido por el usuario.")


finally:

    # ==========================================
    # SEGURIDAD AL SALIR
    # ==========================================

    send_command("OPEN")

    time.sleep(0.5)

    cap.release()

    cv2.destroyAllWindows()

    arduino.close()

    print("Sistema cerrado.")