import cv2
import numpy as np
from ultralytics import YOLO
import torch

# Verifica que la GPU esté disponible
assert torch.cuda.is_available(), "CUDA no está disponible. Verifica tu instalación de PyTorch y drivers."

# ----------------- ZONAS DE DETECCIÓN -----------------
zona_1 = np.array([[320, 0], [640, 0], [640, 480], [320, 480]])  # Lado derecho
zona_2 = np.array([[0, 0], [320, 0], [320, 480], [0, 480]])      # Lado izquierdo
zonas = [zona_1, zona_2]
colores = [(0, 255, 0), (0, 165, 255)]
conteos = [0, 0]

# Inicializa el modelo YOLOv8 en GPU
modelo = YOLO('YOLO/yolov8m.pt')
modelo.to('cuda')

# Clases relevantes
clases_validas = ['car', 'truck', 'bus']

cap = cv2.VideoCapture(0)
frame_counter = 0
warmup_frames = 60

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_counter += 1
    nuevos_conteos = [0, 0]

    resultados = modelo(frame, verbose=False)[0]

    for box in resultados.boxes:
        class_id = int(box.cls.item())
        class_name = modelo.names[class_id]
        if class_name in clases_validas:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            for z, zona in enumerate(zonas):
                if cv2.pointPolygonTest(zona, (cx, cy), False) >= 0:
                    nuevos_conteos[z] += 1

            label = f"{class_name}: {box.conf.item():.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    conteos = nuevos_conteos

    if frame_counter <= warmup_frames:
        cv2.putText(frame, "Cargando fondo...", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    for i, zona in enumerate(zonas):
        cv2.polylines(frame, [zona], True, colores[i], 2)
        cv2.putText(frame, f'Zona {i+1}: {conteos[i]}',
                    (zona[0][0] + 10, zona[0][1] + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, colores[i], 2)

    cv2.imshow("YOLOv8 GPU Vehiculos", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        conteos = [0, 0]
        frame_counter = 0

cap.release()
cv2.destroyAllWindows()
