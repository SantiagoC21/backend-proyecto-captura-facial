from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import asyncio
import time
import os
from app.database import get_db
from app.models.models import Persona, Foto
from app.schemas.schemas import CapturaResponse
from app.services.capturas_service import procesar_imagen

load_dotenv()

MAX_FOTOS = int(os.getenv("MAX_FOTOS_POR_PERSONA", 10))

router = APIRouter(prefix="/capturas", tags=["Capturas"])


@router.post("/{persona_id}", response_model=CapturaResponse, status_code=201)
async def capturar_foto(
    persona_id: int,
    request: Request,
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    t_total = time.time()

    # BD - verificar persona
    t0      = time.time()
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada.")
    total_actual = db.query(Foto).filter(Foto.persona_id == persona_id).count()
    print(f"⏱ BD consulta:        {(time.time()-t0)*1000:.1f}ms")

    if total_actual >= MAX_FOTOS:
        raise HTTPException(status_code=400, detail="Límite de fotos alcanzado.")

    # Leer imagen
    t0           = time.time()
    imagen_bytes = await imagen.read()
    print(f"⏱ Leer imagen:        {(time.time()-t0)*1000:.1f}ms ({len(imagen_bytes)/1024:.1f}KB)")

    # Procesar imagen en hilo separado
    t0       = time.time()
    loop     = asyncio.get_event_loop()
    executor = request.app.state.executor
    resultado = await loop.run_in_executor(
        executor,
        procesar_imagen,
        imagen_bytes,
        persona.nombre,
        total_actual
    )
    print(f"⏱ Procesar imagen:    {(time.time()-t0)*1000:.1f}ms")

    if resultado["ruta"] is None:
        return CapturaResponse(
            mensaje="No se detectó ningún rostro, intenta de nuevo.",
            foto_id=-1,
            ruta_archivo="",
            total_capturas=total_actual,
            limite_alcanzado=False
        )

    # Guardar en BD
    t0   = time.time()
    foto = Foto(persona_id=persona_id, ruta_archivo=resultado["ruta"])
    db.add(foto)
    db.commit()
    db.refresh(foto)
    print(f"⏱ BD insertar:        {(time.time()-t0)*1000:.1f}ms")

    nuevo_total = total_actual + 1
    print(f"⏱ TOTAL endpoint:     {(time.time()-t_total)*1000:.1f}ms")
    print(f"─────────────────────────────────")

    return CapturaResponse(
        mensaje="Rostro capturado correctamente.",
        foto_id=foto.id,
        ruta_archivo=foto.ruta_archivo,
        total_capturas=nuevo_total,
        limite_alcanzado=(nuevo_total >= MAX_FOTOS)
    )


@router.get("/foto/{foto_id}/imagen", tags=["Capturas"])
def servir_foto(foto_id: int, db: Session = Depends(get_db)):
    foto = db.query(Foto).filter(Foto.id == foto_id).first()
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada.")
    if not os.path.exists(foto.ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo de imagen no encontrado en disco.")
    return FileResponse(foto.ruta_archivo, media_type="image/jpeg")


@router.get("/{persona_id}", tags=["Capturas"])
def listar_fotos(persona_id: int, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada.")
    fotos = db.query(Foto).filter(Foto.persona_id == persona_id).all()
    return {
        "persona": persona.nombre,
        "total": len(fotos),
        "fotos": [{"id": f.id, "ruta": f.ruta_archivo, "fecha": f.capturado_en} for f in fotos]
    }