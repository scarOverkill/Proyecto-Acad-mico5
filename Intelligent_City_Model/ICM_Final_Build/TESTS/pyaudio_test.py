# === deteccion_sirena_doble.py ===
# Detección de sirenas desde dos micrófonos (zona 1 y zona 2) SIN conexión a Arduino

import sounddevice as sd
import numpy as np
import time
import threading
import keyboard

# === CONFIGURACIÓN ===
DURACION_VENTANA = 1.0   # segundos por bloque de audio
FREQ_MIN = 900           # frecuencia mínima esperada de sirena (Hz)
FREQ_MAX = 2500          # frecuencia máxima esperada de sirena (Hz)
UMBRAL_ZONA_1 = 8  # Razer Seiren Mini necesita menos sensibilidad
UMBRAL_ZONA_2 = 28  # Webcam detecta mejor con valores más altos

# Índices de los micrófonos según el listado
DISPOSITIVO_ZONA_1 = 1  # SteelSeries Arctis
DISPOSITIVO_ZONA_2 = 3  # Webcam

salir = False

def detectar_sirena(audio, samplerate, umbral):
    fft = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1/samplerate)
    indices = np.where((freqs >= FREQ_MIN) & (freqs <= FREQ_MAX))
    energia = np.mean(fft[indices])
    return energia > umbral, energia

def crear_callback(nombre_zona, indice_dispositivo, umbral_energia):
    def callback(indata, frames, time_info, status):
        if status:
            print(f"[{nombre_zona}] Status: {status}")
            return
        audio = indata[:, 0]
        samplerate = int(sd.query_devices(indice_dispositivo, 'input')['default_samplerate'])
        detectado, energia = detectar_sirena(audio, samplerate, umbral_energia)
        if detectado:
            print(f"⚠️ Sirena detectada en {nombre_zona} (energía: {energia:.2f})")
        else:
            print(f"--- Ruido normal en {nombre_zona} (energía: {energia:.2f})")
    return callback

def esperar_tecla_salida():
    global salir
    keyboard.wait('q')
    salir = True

print("Escuchando sirenas en ZONA 1 (SteelSeries) y ZONA 2 (Webcam)... (presiona 'q' para salir)")

threading.Thread(target=esperar_tecla_salida, daemon=True).start()

try:
    with sd.InputStream(device=DISPOSITIVO_ZONA_1, callback=crear_callback("ZONA 1", DISPOSITIVO_ZONA_1, UMBRAL_ZONA_1), channels=1, samplerate=44100, blocksize=int(44100 * DURACION_VENTANA)) as stream1, \
     sd.InputStream(device=DISPOSITIVO_ZONA_2, callback=crear_callback("ZONA 2", DISPOSITIVO_ZONA_2, UMBRAL_ZONA_2), channels=1, samplerate=44100, blocksize=int(44100 * DURACION_VENTANA)) as stream2:
        while not salir:
            time.sleep(0.1)
except Exception as e:
    print(f"Error: {e}")

print("\nFinalizado por el usuario")
