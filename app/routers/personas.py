from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import Persona, Foto
from app.schemas.schemas import PersonaCreate, PersonaResponse

router = APIRouter(prefix="/personas", tags=["Personas"])


@router.post("/", response_model=PersonaResponse, status_code=201)
def crear_persona(datos: PersonaCreate, db: Session = Depends(get_db)):
    existente = db.query(Persona).filter(Persona.nombre == datos.nombre).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una persona con ese nombre.")

    persona = Persona(nombre=datos.nombre)
    db.add(persona)
    db.commit()
    db.refresh(persona)

    return PersonaResponse(
        id=persona.id,
        nombre=persona.nombre,
        creado_en=persona.creado_en,
        total_fotos=0
    )


@router.get("/", response_model=List[PersonaResponse])
def listar_personas(db: Session = Depends(get_db)):
    personas = db.query(Persona).all()
    resultado = []
    for p in personas:
        total = db.query(Foto).filter(Foto.persona_id == p.id).count()
        resultado.append(PersonaResponse(
            id=p.id,
            nombre=p.nombre,
            creado_en=p.creado_en,
            total_fotos=total
        ))
    return resultado


@router.get("/{persona_id}", response_model=PersonaResponse)
def obtener_persona(persona_id: int, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada.")

    total = db.query(Foto).filter(Foto.persona_id == persona_id).count()
    return PersonaResponse(
        id=persona.id,
        nombre=persona.nombre,
        creado_en=persona.creado_en,
        total_fotos=total
    )


@router.delete("/{persona_id}", status_code=204)
def eliminar_persona(persona_id: int, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada.")

    db.delete(persona)
    db.commit()


@router.get("/verificar/{nombre}")
def verificar_persona(nombre: str, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.nombre == nombre).first()
    if persona:
        return {"existe": True, "persona_id": persona.id, "total_fotos": db.query(Foto).filter(Foto.persona_id == persona.id).count()}
    return {"existe": False, "persona_id": None, "total_fotos": 0}