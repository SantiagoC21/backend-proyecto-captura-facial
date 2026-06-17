from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class FotoBase(BaseModel):
    ruta_archivo: str

class FotoResponse(FotoBase):
    id:           int
    persona_id:   int
    capturado_en: datetime

    class Config:
        from_attributes = True


class PersonaCreate(BaseModel):
    nombre: str

class PersonaResponse(BaseModel):
    id:          int
    nombre:      str
    creado_en:   datetime
    total_fotos: Optional[int] = 0

    class Config:
        from_attributes = True


class CapturaResponse(BaseModel):
    mensaje:          str
    foto_id:          int
    ruta_archivo:     str
    total_capturas:   int
    limite_alcanzado: bool