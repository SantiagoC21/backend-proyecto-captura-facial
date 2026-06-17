from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Persona(Base):
    __tablename__ = "personas"

    id        = Column(Integer, primary_key=True, index=True)
    nombre    = Column(String(100), nullable=False, unique=True)
    creado_en = Column(DateTime, default=datetime.now)

    fotos = relationship("Foto", back_populates="persona", cascade="all, delete")


class Foto(Base):
    __tablename__ = "fotos"

    id           = Column(Integer, primary_key=True, index=True)
    persona_id   = Column(Integer, ForeignKey("personas.id"), nullable=False)
    ruta_archivo = Column(String(255), nullable=False)
    capturado_en = Column(DateTime, default=datetime.now)

    persona = relationship("Persona", back_populates="fotos")