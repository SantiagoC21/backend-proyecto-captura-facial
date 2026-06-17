import cv2
import imutils
import numpy as np
import os
import time
from dotenv import load_dotenv
from app.services.drive_service import subir_foto_drive

load_dotenv()

FOTOS_DIR    = os.getenv("FOTOS_DIR", "./fotos")
FACE_SIZE    = 112
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

faceClassif = cv2.CascadeClassifier(CASCADE_PATH)


def _get_person_path(nombre_persona: str) -> str:
    path = os.path.join(FOTOS_DIR, nombre_persona)
    os.makedirs(path, exist_ok=True)
    return path


def _detectar_rostro(frame):
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceClassif.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=6,
        minSize=(60, 60)
    )
    if len(faces) > 0:
        return frame, faces

    for angulo in [90, 180, 270]:
        rotado = imutils.rotate_bound(frame, angulo)
        gray_r = cv2.cvtColor(rotado, cv2.COLOR_BGR2GRAY)
        faces  = faceClassif.detectMultiScale(
            gray_r,
            scaleFactor=1.1,
            minNeighbors=6,
            minSize=(60, 60)
        )
        if len(faces) > 0:
            print(f"  ✅ Rostro detectado con rotación {angulo}°")
            return rotado, faces

    return frame, []


def _seleccionar_mejor_rostro(faces):
    return max(faces, key=lambda f: f[2] * f[3])


def procesar_imagen(imagen_bytes: bytes, nombre_persona: str, count: int) -> dict:
    t_total = time.time()

    # Decodificar
    t0    = time.time()
    nparr = np.frombuffer(imagen_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    print(f"  ⏱ Decodificar:      {(time.time()-t0)*1000:.1f}ms")

    if frame is None:
        print("  ❌ No se pudo decodificar la imagen")
        raise ValueError("No se pudo decodificar la imagen recibida.")

    # Resize
    t0    = time.time()
    frame = imutils.resize(frame, width=800)
    print(f"  ⏱ Resize:           {(time.time()-t0)*1000:.1f}ms")

    # Detección de rostro
    t0           = time.time()
    frame, faces = _detectar_rostro(frame)
    print(f"  ⏱ Detectar rostro:  {(time.time()-t0)*1000:.1f}ms — {len(faces)} rostros")

    if len(faces) == 0:
        print(f"  ⏱ Total servicio:   {(time.time()-t_total)*1000:.1f}ms — sin rostro")
        return {"ruta": None, "rostros_detectados": 0}

    # Recorte y CLAHE
    t0         = time.time()
    x, y, w, h = _seleccionar_mejor_rostro(faces)
    margen     = int(max(w, h) * 0.20)
    x1 = max(0, x - margen)
    y1 = max(0, y - margen)
    x2 = min(frame.shape[1], x + w + margen)
    y2 = min(frame.shape[0], y + h + margen)
    rostro = frame[y1:y2, x1:x2]
    rostro = cv2.resize(rostro, (FACE_SIZE, FACE_SIZE), interpolation=cv2.INTER_LANCZOS4)

    lab     = cv2.cvtColor(rostro, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe   = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    l       = clahe.apply(l)
    lab     = cv2.merge((l, a, b))
    rostro  = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    print(f"  ⏱ Recorte+CLAHE:    {(time.time()-t0)*1000:.1f}ms")

    # Guardar local
    t0          = time.time()
    person_path = _get_person_path(nombre_persona)
    filename    = f"rostro_{count}.jpg"
    full_path   = os.path.join(person_path, filename)
    _, buffer   = cv2.imencode(".jpg", rostro, [cv2.IMWRITE_JPEG_QUALITY, 95])
    rostro_bytes = buffer.tobytes()
    cv2.imwrite(full_path, rostro, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"  ⏱ Guardar local:    {(time.time()-t0)*1000:.1f}ms")

    # Subir a Drive
    t0         = time.time()
    drive_link = subir_foto_drive(rostro_bytes, nombre_persona, filename)
    print(f"  ⏱ Subir Drive:      {(time.time()-t0)*1000:.1f}ms")

    print(f"  ⏱ Total servicio:   {(time.time()-t_total)*1000:.1f}ms")

    return {
        "ruta":               full_path,
        "drive_link":         drive_link,
        "rostros_detectados": len(faces)
    }