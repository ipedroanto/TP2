from typing import List, Optional, Dict
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import ResenaDB

# Crear las tablas automáticamente en MySQL al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Analizador Inteligente de Respuestas de Clientes",
    description="Backend para validación Pydantic, alertas deterministas y métricas de feedback.",
    version="1.0.0"
)

# --- Esquemas de Pydantic ---
class ResenaCreate(BaseModel):
    cliente: str = Field(..., min_length=2, max_length=100)
    correo: EmailStr
    puntuacion: int = Field(..., ge=1, le=5)
    comentario: str = Field(..., min_length=3)
    categoria: Optional[str] = Field("General", max_length=50)

class ResenaPatch(BaseModel):
    sentimiento: Optional[str] = None
    categoria_ia: Optional[str] = None
    resumen_ia: Optional[str] = None
    estado_gestion: Optional[str] = None

class ResenaResponse(BaseModel):
    id: int
    cliente: str
    correo: str
    puntuacion: int
    comentario: str
    categoria: str
    alerta_critica: bool
    sentimiento: str
    categoria_ia: str
    resumen_ia: Optional[str] = None
    estado_gestion: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True

# --- Endpoints REST ---
@app.get("/salud", tags=["Mantenimiento"])
def verificar_salud():
    return {"estado": "saludable", "fecha": datetime.utcnow()}

@app.get("/metricas", tags=["Opiniones"])
def obtener_metricas(db: Session = Depends(get_db)):
    total_resenas = db.query(ResenaDB).count()
    promedio = db.query(func.avg(ResenaDB.puntuacion)).scalar()
    total_insatisfechas = db.query(ResenaDB).filter(ResenaDB.puntuacion <= 2).count()
    alertas_criticas_activas = (
        db.query(ResenaDB)
        .filter(
            ResenaDB.alerta_critica.is_(True),
            ResenaDB.estado_gestion == "Pendiente",
        )
        .count()
    )
    pendientes = (
        db.query(ResenaDB)
        .filter(ResenaDB.estado_gestion == "Pendiente")
        .count()
    )
    distribucion_consultada = dict(
        db.query(ResenaDB.puntuacion, func.count(ResenaDB.id))
        .group_by(ResenaDB.puntuacion)
        .all()
    )

    return {
        "promedio_satisfaccion": round(float(promedio or 0), 2),
        "total_resenas": total_resenas,
        "porcentaje_insatisfechos": (
            round(total_insatisfechas / total_resenas * 100, 2)
            if total_resenas
            else 0
        ),
        "alertas_criticas_activas": alertas_criticas_activas,
        "resenas_pendientes_atencion": pendientes,
        "distribucion_puntuaciones": {
            puntuacion: distribucion_consultada.get(puntuacion, 0)
            for puntuacion in range(1, 6)
        },
    }

@app.post("/analizar-reseña", response_model=ResenaResponse, status_code=status.HTTP_201_CREATED, tags=["Opiniones"])
def analizar_y_registrar_reseña(resena: ResenaCreate, db: Session = Depends(get_db)):
    # Regla determinista en Python: Alerta crítica si puntuación <= 2
    es_alerta_critica = resena.puntuacion <= 2

    nueva_resena = ResenaDB(
        cliente=resena.cliente,
        correo=resena.correo,
        puntuacion=resena.puntuacion,
        comentario=resena.comentario,
        categoria=resena.categoria or "General",
        alerta_critica=es_alerta_critica,
        sentimiento="Pendiente",
        estado_gestion="Pendiente"
    )
    db.add(nueva_resena)
    db.commit()
    db.refresh(nueva_resena)
    return nueva_resena

@app.get("/reseñas", response_model=List[ResenaResponse], tags=["Opiniones"])
def listar_reseñas(
    sentimiento: Optional[str] = Query(None),
    estado_gestion: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ResenaDB)
    if sentimiento:
        query = query.filter(ResenaDB.sentimiento == sentimiento)
    if estado_gestion:
        query = query.filter(ResenaDB.estado_gestion == estado_gestion)
    return query.order_by(ResenaDB.fecha_creacion.desc()).all()

@app.patch("/reseñas/{resena_id}", response_model=ResenaResponse, tags=["Opiniones"])
def actualizar_reseña(resena_id: int, datos_actualizacion: ResenaPatch, db: Session = Depends(get_db)):
    resena = db.query(ResenaDB).filter(ResenaDB.id == resena_id).first()
    if not resena:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    
    for clave, valor in datos_actualizacion.model_dump(exclude_unset=True).items():
        setattr(resena, clave, valor)
    
    db.commit()
    db.refresh(resena)
    return resena