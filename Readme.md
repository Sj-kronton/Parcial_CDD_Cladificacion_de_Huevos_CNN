# Readme para el parcial

## Aclaracion: Su servidor desconocia el detalle de que el sistema para la deteccion de huevos debia hacerse con una API y el uso del servidor de AWS
## Debido a esto y de forma equivocada realice el parcial y el sistema de forma local en codigos de python para ejecutar en VS code.
## Tambien, esperando que el factor diferenciador sea el uso de un arduino UNO junto a un micro servomotor sg90 para automatizar la clasificacion de los huevos en la rampa: existen configuraciones para que el sistema envie comandos e interactue junto al Arduino.


# 🥚 Detección de Huevos con Daños — Sistema End-to-End

Sistema de clasificación automática de huevos mediante visión por computador y Deep Learning, integrado con Arduino UNO y un servomotor SG90 de rotación continua para simular una banda transportadora con separación física.

## 🎯 Objetivo

Clasificar huevos en tres categorías:

- `broken` — huevo roto
- `dirty` — huevo sucio
- `good` — huevo en buen estado

El flujo completo es:

```text
Cámara → Python/OpenCV → MobileNetV2 → decisión → USB Serial → Arduino UNO → SG90 → separación física
```

El proyecto busca llevar el modelo desde el entrenamiento hasta una demostración End-to-End.

---

## ⭐ Diferencial del proyecto

El sistema no obliga al modelo a tomar una decisión cuando la predicción es ambigua.

Cuando la confianza y la consistencia no alcanzan los umbrales establecidos, el mecanismo permanece cerrado, se genera una alerta y se solicita **intervención humana** antes de continuar.

```text
Predicción confiable
       │
       ├── GOOD ───────────► OPEN
       │
       └── BROKEN/DIRTY ──► CLOSE → REJECT → OPEN

Predicción ambigua
       │
       ▼
     CLOSE
       │
       ▼
Alerta + intervención humana
       │
       ▼
      OPEN
```

Este mecanismo constituye el principal valor añadido del proyecto frente a una clasificación que simplemente ejecuta automáticamente la clase predicha.

---

# 🧠 Modelo de Deep Learning

Se utilizó **MobileNetV2 preentrenada con ImageNet** como extractor de características.

Arquitectura:

```text
Input 224×224×3
      ↓
Data Augmentation
      ↓
MobileNetV2
(pretrained ImageNet)
      ↓
Global Average Pooling
      ↓
Dropout 0.20
      ↓
Dense(3, Softmax)
      ↓
broken / dirty / good
```

### Data augmentation

- `RandomFlip("horizontal")`
- `RandomRotation(0.08)`
- `RandomZoom(0.10)`
- `RandomContrast(0.10)`

### Entrenamiento

- Optimizer: Adam
- Learning rate inicial: `1e-4`
- Loss: Sparse Categorical Crossentropy
- Batch size: `32`
- Early Stopping
- Model Checkpoint
- ReduceLROnPlateau
- Máximo: 30 épocas

El mejor modelo se obtuvo alrededor de la época 26.

```text
Train accuracy:      94.66%
Validation accuracy: 95.48%
```

Modelo:

```text
best_egg_model.keras
```

---

# 📊 Dataset

Dataset utilizado:

```text
CDD_eggs_SJ-2
```

obtenido mediante Roboflow.

| Característica | Valor |
|---|---:|
| Imágenes totales | 9,549 |
| Resolución | 224×224 |
| Clases | 3 |
| Imágenes corruptas | 0 |

### Clases

| Clase | Imágenes |
|---|---:|
| broken | 3,649 |
| dirty | 2,947 |
| good | 2,953 |

### División

| Conjunto | Imágenes |
|---|---:|
| Train | 8,488 |
| Validation | 531 |
| Test | 530 |

Mapeo:

```text
0 = broken
1 = dirty
2 = good
```

---

# 📈 Evaluación

El modelo fue evaluado sobre 530 imágenes de prueba.

```text
Test loss:     0.1082
Test accuracy: 0.9623
```

**Accuracy: 96.23%**

### Matriz de confusión

```text
                 Predicción
              broken dirty good

Real broken     193    0     8
Real dirty        0  158     0
Real good        12    0   159
```

Resultado:

```text
510 / 530 correctas
20 / 530 incorrectas
```

### Métricas

| Clase | Precision | Recall | F1-score |
|---|---:|---:|---:|
| broken | 94.15% | 96.02% | 95.07% |
| dirty | 100.00% | 100.00% | 100.00% |
| good | 95.21% | 92.98% | 94.08% |
| **Accuracy** | | | **96.23%** |

Los errores del conjunto de prueba se concentraron entre `broken` y `good`:

```text
broken → good = 8
good → broken = 12
```

No hubo confusiones entre `dirty` y las otras clases en el conjunto de prueba.

---

# 📷 Pruebas con cámara

Se realizaron pruebas utilizando una webcam.

Inicialmente se clasificó la imagen completa. Se observó que el fondo y el contexto afectaban las predicciones.

Posteriormente se implementó una **ROI central** de aproximadamente:

```text
60% del ancho
60% de la altura
```

La ROI se redimensiona a:

```text
224×224
```

Esto permitió que el huevo ocupara una mayor proporción de la entrada del modelo.

En las pruebas:

- huevos buenos: aproximadamente 95% en condiciones favorables;
- huevos rotos: aproximadamente 85–95% en varias pruebas;
- huevos sucios: aproximadamente 70–90% en varias pruebas.

También se comprobó que utilizar un fondo negro no mejoraba consistentemente todas las clases. Por ello, el sistema se apoya principalmente en una ROI adecuada y análisis temporal.

---

# ⏱️ Análisis temporal

Para evitar reaccionar ante una única predicción, el sistema considera varias imágenes durante una ventana de tiempo.

Se utilizan:

- probabilidad promedio;
- clase dominante;
- consistencia entre frames.

Parámetros iniciales:

```python
INITIAL_ANALYSIS_TIME = 1.0
WAIT_TIME = 2.5
SECOND_ANALYSIS_TIME = 2.5
REJECT_TIME = 1.0

MIN_CONFIDENCE = 0.70
MIN_CONSISTENCY = 0.70
```

Estos valores son parámetros del prototipo y pueden ajustarse durante la integración física.

---

# 🔌 Hardware

## Componentes

- Arduino UNO R3
- SG90 de rotación continua
- PC/laptop
- Webcam
- Cable USB
- Cables jumper
- Mecanismo físico de separación

## Conexión SG90

| SG90 | Arduino UNO |
|---|---|
| Marrón/negro | GND |
| Rojo | 5V |
| Naranja/amarillo | D9 |

Si aparecen reinicios o movimientos erráticos por consumo de corriente, se recomienda una fuente externa de 5 V para el servo con GND común con Arduino.

---

# ⚙️ Calibración del SG90

El SG90 utilizado es de **rotación continua**, por lo que no se controla mediante posiciones absolutas como un servo convencional.

Se utiliza el tiempo de movimiento para aproximar el desplazamiento.

Resultados de calibración:

| Comando | Dirección | Tiempo | Desplazamiento |
|---|---|---:|---:|
| `1` | Derecha | 65 ms | ≈45° |
| `2` | Izquierda | 65 ms | ≈50° |
| `3` | Derecha | 130 ms | ≈85° |
| `4` | Izquierda | 130 ms | ≈85° |
| `5` | Derecha | 195 ms | ≈135° |
| `6` | Izquierda | 195 ms | ≈135° |
| `7` | Derecha | 260 ms | ≈178° |
| `8` | Izquierda | 260 ms | ≈175° |
| `9` | Derecha | 490 ms | ≈320° |
| `A` | Izquierda | 490 ms | ≈320° |

Estos valores dependen del servo, alimentación y carga mecánica utilizados.

---

# 🤖 Arduino y comunicación serial

Arduino funciona como controlador del actuador. La inteligencia de clasificación permanece en Python.

Arquitectura:

```text
Python
  │
  │ USB Serial
  ▼
Arduino UNO
  │
  ▼
SG90
```

Comandos previstos:

```text
OPEN
CLOSE
REJECT
RESET
STOP
```

### Responsabilidades de Python

- Captura de cámara.
- Procesamiento de ROI.
- Inferencia con MobileNetV2.
- Cálculo de probabilidades.
- Evaluación de confianza y consistencia.
- Decisión.
- Comunicación serial.
- Intervención humana.

### Responsabilidades de Arduino

- Recibir comandos.
- Controlar dirección del SG90.
- Controlar duración del movimiento.
- Detener el servo.
- Ejecutar la acción física solicitada.

---

# 🔄 Lógica End-to-End

```text
                    INICIO
                       │
                       ▼
                    OPEN
                       │
                       ▼
             Análisis inicial
                       │
          ┌────────────┴────────────┐
          │                         │
       GOOD                  BROKEN / DIRTY
          │                         │
          ▼                         ▼
        OPEN                      CLOSE
                                    │
                                    ▼
                              Esperar 2.5 s
                                    │
                                    ▼
                            Segundo análisis
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
           GOOD              BROKEN / DIRTY           AMBIGUO
             │                      │                      │
             ▼                      ▼                      ▼
           OPEN                  REJECT                 CLOSE
                                    │                      │
                                    ▼                      ▼
                               Esperar 1 s          Alarma + popup
                                    │                      │
                                    ▼                      ▼
                                  OPEN              Intervención
                                                           │
                                                           ▼
                                                         OPEN
```

---

# 🚦 Estados físicos

### OPEN

Permite el paso normal del huevo.

```text
Python → OPEN
```

### CLOSE

Bloquea temporalmente el flujo mientras se realiza una segunda evaluación.

```text
Python → CLOSE
```

### REJECT

Desvía el huevo clasificado como `broken` o `dirty`.

```text
Python → REJECT
```

### Intervención humana

Si la confianza o consistencia no es suficiente:

```text
CLOSE
  ↓
Alarma
  ↓
Popup
  ↓
Intervención humana
  ↓
OPEN
```

---

# 🖥️ Software

Principales tecnologías:

- Python
- TensorFlow / Keras
- MobileNetV2
- OpenCV
- NumPy
- PySerial
- Arduino IDE
- Arduino `Servo.h`

Instalación:

```bash
pip install tensorflow opencv-python numpy pyserial
```

O:

```bash
pip install -r requirements.txt
```

---

# 📁 Estructura sugerida

```text
deteccion-huevos/
│
├── README.md
├── arduino/
│   └── egg_sorter.ino
├── python/
│   └── end2end_egg_sorter.py
├── model/
│   └── best_egg_model.keras
├── notebooks/
│   └── entrenamiento.ipynb
├── tests/
│   └── camera_test.py
└── requirements.txt
```

No es necesario incluir el dataset completo en el repositorio.

---

# ▶️ Ejecución

## 1. Arduino

1. Conectar Arduino UNO por USB.
2. Conectar el SG90.
3. Abrir el sketch.
4. Seleccionar Arduino UNO.
5. Seleccionar el puerto, por ejemplo:

```text
COM3
```

6. Cargar el sketch.
7. Comprobar la posición inicial del mecanismo.

## 2. Python

Instalar dependencias:

```bash
pip install tensorflow opencv-python numpy pyserial
```

Verificar que:

```text
best_egg_model.keras
```

esté en la ruta esperada por el script.

Configurar el puerto:

```python
PORT = "COM3"
BAUDRATE = 9600
```

Ejecutar:

```bash
python end2end_egg_sorter.py
```

> El Monitor Serial del Arduino IDE y Python no deben utilizar COM3 simultáneamente.

---

# 🧪 Estrategia de pruebas

Se recomienda probar el sistema por etapas:

### 1. Modelo

```text
imagen → MobileNetV2 → clase + probabilidades
```

### 2. Cámara

```text
cámara → ROI → predicción
```

### 3. Serial

```text
Python → COM3 → Arduino
```

con:

```text
OPEN
CLOSE
REJECT
```

### 4. Mecanismo

Comprobar físicamente:

```text
OPEN  → paso normal
CLOSE → bloqueo
REJECT → desviación
```

### 5. End-to-End

```text
Huevo
  ↓
Cámara
  ↓
ROI
  ↓
MobileNetV2
  ↓
Decisión
  ↓
Serial
  ↓
Arduino
  ↓
SG90
  ↓
Separación física
```

---

# ⚠️ Limitaciones

### SG90 de rotación continua

El servo no proporciona retroalimentación de posición. La posición física depende de:

- tiempo de movimiento;
- velocidad;
- alimentación;
- carga;
- posición inicial.

Por ello, el mecanismo debe iniciar en una posición conocida.

### Clasificación mediante ROI

MobileNetV2 es un clasificador y no un detector de objetos. El huevo debe aparecer dentro de la región de interés.

### Activación del ciclo

La versión de prototipo utiliza ventanas temporales. Una versión posterior podría utilizar un sensor infrarrojo para detectar la entrada exacta de cada huevo.

### Variación de cámara

Iluminación, fondo, distancia y posición pueden modificar la predicción.

### Umbrales

Los valores de 70% de confianza y 70% de consistencia son parámetros iniciales y pueden requerir calibración adicional.

---

# 🔮 Mejoras futuras

- Sensor infrarrojo para detectar la llegada del huevo.
- Iluminación controlada.
- Cámara fija.
- Reentrenamiento con imágenes tomadas directamente desde el prototipo.
- Seguimiento del huevo.
- Sensores de posición para el mecanismo.
- Interfaz gráfica con cámara, clase, probabilidades y estado del servo.
- Registro de decisiones y tiempos.
- Métricas del sistema físico completo.
- Calibración automática del mecanismo.

---

# 📋 Resumen técnico

| Elemento | Implementación |
|---|---|
| Problema | Clasificación de huevos |
| Clases | broken / dirty / good |
| Dataset | CDD_eggs_SJ-2 |
| Imágenes | 9,549 |
| Resolución | 224×224 |
| Modelo | MobileNetV2 |
| Transfer learning | Sí |
| Accuracy test | **96.23%** |
| Cámara | Webcam |
| Procesamiento | OpenCV + ROI |
| Computación | PC |
| Microcontrolador | Arduino UNO R3 |
| Actuador | SG90 continuo |
| Comunicación | USB Serial |
| Puerto probado | COM3 |
| Baudrate | 9600 |
| Diferencial | Intervención humana ante incertidumbre |

---

# 📌 Estado del proyecto

```text
Modelo                  ✅
Evaluación              ✅
Pruebas con cámara      ✅
ROI                     ✅
Arduino UNO             ✅
Calibración SG90        ✅
Comunicación serial     ✅
Lógica End-to-End       🔄
Integración física      🔄
Demostración final      🔄
```

## Flujo general

```text
                 DATASET
                    │
                    ▼
              ENTRENAMIENTO
                    │
                    ▼
               MobileNetV2
                    │
                    ▼
               EVALUACIÓN
                    │
               96.23% TEST
                    │
                    ▼
             PRUEBAS CÁMARA
                    │
                    ▼
                  ROI
                    │
                    ▼
            DECISIÓN TEMPORAL
                    │
          ┌─────────┴─────────┐
          │                   │
      CONFIABLE            AMBIGUO
          │                   │
          ▼                   ▼
      AUTOMÁTICO        INTERVENCIÓN HUMANA
          │
          ▼
        SERIAL
          │
          ▼
      ARDUINO UNO
          │
          ▼
         SG90
          │
          ▼
   SEPARACIÓN FÍSICA
```
