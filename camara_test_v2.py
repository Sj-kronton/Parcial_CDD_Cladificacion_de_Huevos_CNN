import cv2
import numpy as np
import tensorflow as tf


# ==========================================
# CONFIGURACIÓN
# ==========================================

MODEL_PATH = "C:\\Users\\juana\\Apuntes-Ciencia-de-Datos\\Parcial_CNN\\best_egg_model.keras"

IMG_SIZE = (224, 224)

CLASS_NAMES = [
    "broken",
    "dirty",
    "good"
]


# ==========================================
# CARGAR MODELO
# ==========================================

print("Cargando modelo...")

model = tf.keras.models.load_model(MODEL_PATH)

print("Modelo cargado correctamente.")


# ==========================================
# FUNCIÓN DE CLASIFICACIÓN
# ==========================================

def classify_roi(roi):

    # OpenCV trabaja en BGR.
    # Convertimos a RGB para TensorFlow.
    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)

    # Redimensionar al tamaño esperado por MobileNetV2
    image = cv2.resize(roi_rgb, IMG_SIZE)

    # Convertir a float32
    image = image.astype(np.float32)

    # Agregar dimensión del batch
    image = np.expand_dims(image, axis=0)

    # Predicción
    predictions = model.predict(image, verbose=0)[0]

    # Clase con mayor probabilidad
    predicted_class = np.argmax(predictions)

    # Confianza
    confidence = predictions[predicted_class]

    class_name = CLASS_NAMES[predicted_class]

    return class_name, confidence, predictions


# ==========================================
# CÁMARA
# ==========================================

print("Iniciando cámara...")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: No se pudo abrir la cámara.")
    exit()

print("Cámara iniciada.")
print()
print("Coloca el huevo dentro del rectángulo.")
print("Presiona Q para salir.")


# ==========================================
# BUCLE PRINCIPAL
# ==========================================

while True:

    # Leer frame
    ret, frame = cap.read()

    if not ret:
        print("ERROR: No se pudo leer la cámara.")
        break


    # ======================================
    # DEFINIR ROI
    # ======================================

    height, width, _ = frame.shape

    # Tamaño del ROI
    roi_width = int(width * 0.60)
    roi_height = int(height * 0.60)

    # Coordenadas para centrarlo
    x1 = (width - roi_width) // 2
    y1 = (height - roi_height) // 2

    x2 = x1 + roi_width
    y2 = y1 + roi_height


    # Extraer ROI
    roi = frame[y1:y2, x1:x2]


    # ======================================
    # CLASIFICAR ROI
    # ======================================

    class_name, confidence, predictions = classify_roi(roi)


    # Probabilidades individuales
    broken_prob = predictions[0] * 100
    dirty_prob = predictions[1] * 100
    good_prob = predictions[2] * 100


    # ======================================
    # DIBUJAR ROI
    # ======================================

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (255, 255, 255),
        2
    )


    # ======================================
    # MOSTRAR PREDICCIÓN
    # ======================================

    cv2.putText(
        frame,
        f"PREDICCION: {class_name.upper()}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"BROKEN: {broken_prob:.2f}%",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"DIRTY:  {dirty_prob:.2f}%",
        (20, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"GOOD:   {good_prob:.2f}%",
        (20, 140),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"CONF:   {confidence * 100:.2f}%",
        (20, 175),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # ======================================
    # MOSTRAR FRAME
    # ======================================

    cv2.imshow(
        "Egg Classifier - ROI - END2END",
        frame
    )


    # ======================================
    # SALIR
    # ======================================

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ==========================================
# CERRAR
# ==========================================

cap.release()
cv2.destroyAllWindows()

print("Programa finalizado.")