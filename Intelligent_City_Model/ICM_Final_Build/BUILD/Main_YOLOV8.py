# === IMPORTS NECESARIOS ===
# Para el funcionamiento de este sistema se utiliza un modelo de inferencia de Machine Learning preentrenado (YOLOv8).
# Este modelo corre exclusivamente con aceleración por GPU para un rendimiento adecuado.
# Se recomienda usar una GPU NVIDIA de la serie 2060 en adelante para obtener buenos resultados en tiempo real.
import cv2                        # OpenCV: procesamiento y visualización de imágenes. Es lo que maneja la vision
import numpy as np                # Numpy: operaciones matemáticas (vectores, arrays). Facilita el manejo de datos, máscaras, contornos y comunicación estructurada.
import sounddevice as sd          # SoundDevice: captura de audio en tiempo real (detección de sirenas)
import serial                     # Serial: comunicación serial con Arduino (via USB)
import threading                  # Threading: ejecución en paralelo (procesamiento + envío serial + audio), necesario para el manejo de inputs audio/video e instrucciones arduino
import time                       # Time: manejo de tiempos, delays y timestamps, principalmente necesario para la deteccion de audio
from ultralytics import YOLO      # YOLOv8: modelo preentrenado para detección de objetos
import torch                      # PyTorch: backend que acelera la inferencia con la GPU

# === CONFIGURACIONES GENERALES ===
# Verifica que la GPU esté activa y compatible. Evita que la deteccion recaiga en la CPU y genere cuellos de botella
assert torch.cuda.is_available(), "CUDA no está disponible. Verifica tu instalación de PyTorch y drivers."

# Parámetros del sistema
CAMARA_ID = 0                   # Índice de la cámara (0 para webcam interna, 1+ para cámaras USB), este indice cambia segun la camara que se vaya a usar
DISPOSITIVO_ZONA_1 = 1          # Índice del micrófono para Zona 1, cambia segun el input que se quiera usar
DISPOSITIVO_ZONA_2 = 3          # Índice del micrófono para Zona 2, cambia segun el input que se quiera usar
SERIAL_PORT = 'COM3'            # Puerto de conexión del Arduino
BAUDIOS = 9600                  # Velocidad de transmisión serial
INTERVALO_ENVIO = 1.0           # Frecuencia de envío de datos al Arduino (cada 1 segundo)
DURACION_VENTANA_AUDIO = 1.0    # Duración de la ventana de audio (en segundos)
FREQ_MIN = 900                  # Frecuencia mínima para detección de sirenas
FREQ_MAX = 2500                 # Frecuencia máxima para detección de sirenas
UMBRAL_ZONA_1 = 10              # Sensibilidad de la detección de audio para Zona 1
UMBRAL_ZONA_2 = 30              # Sensibilidad para Zona 2 (usualmente más rígido si el micrófono es más débil)

# Variables globales de conteo y control
conteo_z1 = 0
conteo_z2 = 0
salir = False                  # Bandera de salida para detener hilos
arduino = None                 # Instancia del puerto serial con Arduino

# === DETECCIÓN DE VEHÍCULOS CON YOLOv8m ===
def detectar_vehiculos():
    global conteo_z1, conteo_z2, salir

    cap = cv2.VideoCapture(CAMARA_ID)   # Abre la cámara especificada
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara") #Manejo de error de deteccion de camara
        salir = True
        return

    modelo = YOLO('YOLO/yolov8m.pt')    # Carga el modelo YOLOv8m
    modelo.to('cuda')                   # Usa la GPU para la inferencia

    # Define la geometría de las zonas (separadas por la mitad)
    zona_ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    zona_alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    mitad = zona_ancho // 2
    colores = [(255, 0, 0), (0, 0, 255)]

    frame_counter = 0
    warmup_frames = 60                  # Frames de "calentamiento" antes de iniciar conteo real, el conteo no inicia inmediato a que se abra la camara
    clases_validas = ['car', 'truck', 'bus']  # Clases que sí cuentan como vehículos, es el tipo de clases que el modelo va a reconocer

    while not salir:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_counter += 1
        nuevos_conteos = [0, 0]

        resultados = modelo(frame, verbose=False)[0]  # Ejecuta inferencia (YOLOv8m), se aplica de esta forma para que la consola no imprima todo lo que reconoce

        for box in resultados.boxes:
            class_id = int(box.cls.item())                   # ID de la clase
            class_name = modelo.names[class_id]              # Nombre textual, hace un reconocimiento de todo lo enfocado
            if class_name in clases_validas:                 # Solo considera clases de vehículos, filtro para el proyecto
                x1, y1, x2, y2 = map(int, box.xyxy[0])        # Coordenadas de la caja
                cx = int((x1 + x2) / 2)                       # Centro en X
                cy = int((y1 + y2) / 2)                       # Centro en Y
                zona = 0 if cx > mitad else 1                # Determina la zona por posición horizontal
                nuevos_conteos[zona] += 1

                # Dibuja cajas y etiquetas en el frame, dibuja la forma en objeto reconocido e indica que es
                label = f"{class_name}: {box.conf.item():.2f}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        conteo_z1, conteo_z2 = nuevos_conteos

        #Vizualicion de OpenCV
        # Mensaje de inicio
        if frame_counter <= warmup_frames:
            cv2.putText(frame, "Cargando fondo...", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Visualización de zonas y conteo
        cv2.line(frame, (mitad, 0), (mitad, zona_alto), (0, 0, 255), 2)
        cv2.putText(frame, f"Zona 1: {nuevos_conteos[0]}", (mitad + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, colores[0], 2)
        cv2.putText(frame, f"Zona 2: {nuevos_conteos[1]}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, colores[1], 2)

        cv2.imshow("Monitoreo de Vehiculos", frame)

        #Funcionalidad para detener la deteccion
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            salir = True
            break

    cap.release()
    cv2.destroyAllWindows()

# === DETECCIÓN DE SIRENAS (por análisis de frecuencia) ===
def detectar_sirena(audio, samplerate, umbral):
    # Aplica FFT (Transformada Rápida de Fourier) para extraer la energía por frecuencia
    fft = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1 / samplerate)
    indices = np.where((freqs >= FREQ_MIN) & (freqs <= FREQ_MAX))
    energia = np.mean(fft[indices])
    return energia > umbral  # Si la energía supera el umbral, se considera una sirena

# Crea el callback de audio que detecta en tiempo real por zona
# Se maneja diferentes umbrales debido a la capacidad de deteccion de cada microfono
def crear_callback(zona, umbral):
    def callback(indata, frames, time_info, status):
        if status:
            print(f"[ZONA {1 if zona == DISPOSITIVO_ZONA_1 else 2}] Status: {status}")
            return
        audio = indata[:, 0]
        samplerate = int(sd.query_devices(zona, 'input')['default_samplerate'])
        if detectar_sirena(audio, samplerate, umbral):
            print(f"⚠️ Sirena detectada en Zona {1 if zona == DISPOSITIVO_ZONA_1 else 2}")
            if arduino:
                mensaje = f"EMERGENCIA:{1 if zona == DISPOSITIVO_ZONA_1 else 2}\n"
                arduino.write(mensaje.encode())
    return callback

# === ENVÍO SERIAL PERIÓDICO A ARDUINO ===
def ciclo_envio_serial():
    global conteo_z1, conteo_z2
    while not salir:
        if arduino:
            mensaje = f"Z1:{conteo_z1},Z2:{conteo_z2}\n"
            arduino.write(mensaje.encode())
            print(f"Enviado a Arduino: {mensaje.strip()}")
        time.sleep(INTERVALO_ENVIO)

# === FUNCIÓN PRINCIPAL ===
def main():
    global arduino, salir
    try:
        # Conexión inicial con Arduino
        try:
            arduino = serial.Serial(SERIAL_PORT, BAUDIOS, timeout=1)
            time.sleep(2)
            print("✅ Conexión con Arduino establecida")
        except Exception as e:
            print(f"⚠️ No se pudo abrir el puerto serial: {e}")

        # Inicia los hilos en paralelo
        threading.Thread(target=detectar_vehiculos, daemon=True).start()
        threading.Thread(target=ciclo_envio_serial, daemon=True).start()

        # Inicia captura de sonido por zona
        with sd.InputStream(device=DISPOSITIVO_ZONA_1, callback=crear_callback(DISPOSITIVO_ZONA_1, UMBRAL_ZONA_1),
                            channels=1, samplerate=44100, blocksize=int(44100 * DURACION_VENTANA_AUDIO)) as s1, \
            sd.InputStream(device=DISPOSITIVO_ZONA_2, callback=crear_callback(DISPOSITIVO_ZONA_2, UMBRAL_ZONA_2),
                            channels=1, samplerate=44100, blocksize=int(44100 * DURACION_VENTANA_AUDIO)) as s2:
            print("🟢 Sistema iniciado. Presiona Q para salir")

            while not salir:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n⏹ Sistema detenido por el usuario")
        salir = True
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if arduino:
            arduino.close()
        print("✅ Recursos liberados correctamente")

# Punto de entrada
if __name__ == '__main__':
    main()
