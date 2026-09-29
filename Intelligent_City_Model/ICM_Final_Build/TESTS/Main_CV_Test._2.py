import cv2
import numpy as np

# ----------------- ZONAS DE DETECCIÓN -----------------
zona_1 = np.array([[320, 0], [640, 0], [640, 480], [320, 480]])  # Lado derecho
zona_2 = np.array([[0, 0], [320, 0], [320, 480], [0, 480]])      # Lado izquierdo
zonas = [zona_1, zona_2]
colores = [(0, 255, 0), (0, 165, 255)]
conteos = [0, 0]

cap = cv2.VideoCapture(0)
frame_counter = 0
warmup_frames = 60

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Cerrar contornos
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=1)

    frame_counter += 1
    nuevos_centros = []
    nuevos_conteos = [0, 0]

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if frame_counter > warmup_frames:
        for cnt in contours:
            area = cv2.contourArea(cnt)

            # --- FILTROS PERSONALIZADOS MEJORADOS ---
            if 1000 < area < 6000:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = w / float(h)

                # Evita formas cuadradas o muy alargadas
                if 1.2 < aspect_ratio < 3.2 and h < 100:
                    cx = x + w // 2
                    cy = y + h // 2

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                    cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1)

                    for i, zona in enumerate(zonas):
                        if cv2.pointPolygonTest(zona, (cx, cy), False) >= 0:
                            nuevo = True
                            for dcx, dcy in nuevos_centros:
                                if np.hypot(cx - dcx, cy - dcy) < 30:
                                    nuevo = False
                                    break
                            if nuevo:
                                nuevos_centros.append((cx, cy))
                                nuevos_conteos[i] += 1

        conteos = nuevos_conteos
    else:
        cv2.putText(frame, "Cargando fondo...", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Mostrar zonas
    for i, zona in enumerate(zonas):
        cv2.polylines(frame, [zona], True, colores[i], 2)
        cv2.putText(frame, f'Zona {i+1}: {conteos[i]}',
                    (zona[0][0], zona[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, colores[i], 2)

    cv2.imshow("Frame", frame)
    cv2.imshow("Contornos", edges)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        conteos = [0, 0]
        frame_counter = 0

cap.release()
cv2.destroyAllWindows()
