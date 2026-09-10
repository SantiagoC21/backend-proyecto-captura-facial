from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import Persona, Foto
from app.schemas.schemas import PersonaCreate, PersonaResponse, VerificarPersonaResponse

router = APIRouter(prefix="/personas", tags=["Personas"])


@router.post("/", response_model=PersonaResponse, status_code=201)
def crear_persona(datos: PersonaCreate, db: Session = Depends(get_db)):
    existente = db.query(Persona).filter(Persona.codigo == datos.codigo).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una persona con ese código UNI.")

    nombre_completo = f"{datos.apellidos} {datos.nombres}"
    persona = Persona(codigo=datos.codigo, nombre=nombre_completo, aula=datos.aula)
    db.add(persona)
    db.commit()
    db.refresh(persona)

    return PersonaResponse(
        id=persona.id,
        codigo=persona.codigo,
        nombre=persona.nombre,
        aula=persona.aula,
        creado_en=persona.creado_en,
        total_fotos=0
    )


@router.get("/", response_model=List[PersonaResponse])
def listar_personas(aula: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Persona)
    if aula:
        query = query.filter(Persona.aula == aula)
    personas = query.all()

    resultado = []
    for p in personas:
        total = db.query(Foto).filter(Foto.persona_id == p.id).count()
        resultado.append(PersonaResponse(
            id=p.id,
            codigo=p.codigo,
            nombre=p.nombre,
            aula=p.aula,
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
        codigo=persona.codigo,
        nombre=persona.nombre,
        aula=persona.aula,
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


@router.get("/verificar/{codigo}", response_model=VerificarPersonaResponse)
def verificar_persona(codigo: str, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.codigo == codigo).first()
    if persona:
        return VerificarPersonaResponse(
            existe=True,
            persona_id=persona.id,
            total_fotos=db.query(Foto).filter(Foto.persona_id == persona.id).count()
        )
    return VerificarPersonaResponse(existe=False, persona_id=None, total_fotos=0)