import re
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List, Optional

CODIGO_UNI_REGEX = re.compile(r"^20\d{6}[A-Za-z]$")
NOMBRE_SEGMENTO_REGEX = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(\s[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)?$")


class FotoBase(BaseModel):
    ruta_archivo: str

class FotoResponse(FotoBase):
    id:           int
    persona_id:   int
    capturado_en: datetime

    class Config:
        from_attributes = True


class PersonaCreate(BaseModel):
    codigo:    str
    apellidos: str
    nombres:   str
    aula:      str

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        v = v.strip().upper()
        if not CODIGO_UNI_REGEX.match(v):
            raise ValueError(
                "El código UNI debe tener el formato 20XXXXXXY "
                "(empieza con 20, seis dígitos y termina en una letra)."
            )
        return v

    @field_validator("apellidos", "nombres")
    @classmethod
    def validar_nombre_segmento(cls, v: str) -> str:
        v = " ".join(v.strip().split())
        if not NOMBRE_SEGMENTO_REGEX.match(v):
            raise ValueError(
                "Solo se permiten letras y espacios, con una o dos palabras "
                "(ej. 'García' o 'García López')."
            )
        return v.title()

    @field_validator("aula")
    @classmethod
    def validar_aula(cls, v: str) -> str:
        return v.strip().upper()


class PersonaResponse(BaseModel):
    id:          int
    codigo:      str
    nombre:      str
    aula:        str
    creado_en:   datetime
    total_fotos: Optional[int] = 0

    class Config:
        from_attributes = True


class VerificarPersonaResponse(BaseModel):
    existe:      bool
    persona_id:  Optional[int] = None
    total_fotos: int = 0


class CapturaResponse(BaseModel):
    mensaje:          str
    foto_id:          int
    ruta_archivo:     str
    total_capturas:   int
    limite_alcanzado: bool