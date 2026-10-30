"""
FastAPI Backend - Analizador Inteligente de Respuestas de Clientes
Módulo principal de la API para recibir, validar, procesar y persistir las opiniones de los clientes.
"""

from typing import List, Optional, Dict
from datetime import datetime
import os

from fastapi import FastAPI, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ==========================================
# 1. Configuración de la Base de Datos (SQLite / MySQL)
# ==========================================
# Permite conectar a MySQL en Docker o a SQLite localmente si no hay URL definida.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./feedback.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de Tabla Relacional (SQLAlchemy)
class ResenaDB(Base):
    __tablename__ = "resenas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cliente = Column(String(100), nullable=False)
    correo = Column(String(120), nullable=False, index=True)
    puntuacion = Column(Integer, nullable=False)
    comentario = Column(Text, nullable=False)
    categoria = Column(String(50), default="General")
    alerta_critica = Column(Boolean, default=False)
    
    # Campos enriquecidos por IA (Gemini AI / n8n)
    sentimiento = Column(String(20), default="Pendiente")  # Positivo, Neutro, Negativo
    categoria_ia = Column(String(50), default="Sin clasificar")
    resumen_ia = Column(Text, nullable=True)
    
    # Estado de gestión del soporte técnico
    estado_gestion = Column(String(20), default="Pendiente")  # Pendiente, Atendido
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Dependencia para obtener la sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. Esquemas de Datos (Pydantic Models)
# ==========================================

class ResenaCreate(BaseModel):
    """Esquema de entrada para registrar una nueva reseña (Validación Pydantic)."""
    cliente: str = Field(..., min_length=2, max_length=100, description="Nombre del cliente")
    correo: EmailStr = Field(..., description="Correo electrónico válido")
    puntuacion: int = Field(..., ge=1, le=5, description="Puntuación de 1 a 5 estrellas")
    comentario: str = Field(..., min_length=3, description="Comentario o opinión en texto libre")
    categoria: Optional[str] = Field("General", max_length=50, description="Categoría inicial del producto/servicio")

class ResenaPatch(BaseModel):
    """Esquema de actualización para enriquecer con datos de IA o cambiar estado."""
    sentimiento: Optional[str] = Field(None, description="Positivo, Neutro o Negativo")
    categoria_ia: Optional[str] = Field(None, description="Categoría identificada por la IA")
    resumen_ia: Optional[str] = Field(None, description="Resumen o hallazgo redactado por la IA")
    estado_gestion: Optional[str] = Field(None, description="Estado: Pendiente o Atendido")

class ResenaResponse(BaseModel):
    """Esquema de salida estructurada de la reseña."""
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

class MetricasResponse(BaseModel):
    """Esquema para las métricas consolidadas del dashboard."""
    total_resenas: int
    promedio_satisfaccion: float
    porcentaje_insatisfechos: float
    alertas_criticas_activas: int
    distribucion_puntuaciones: Dict[int, int]
    resenas_pendientes_atencion: int

# ==========================================
# 3. Inicialización de la Aplicación FastAPI
# ==========================================

app = FastAPI(
    title="API Analizador Inteligente de Respuestas de Clientes",
    description="Backend en FastAPI para validación Pydantic, cálculo determinista de alertas y persistencia de métricas de feedback.",
    version="1.0.0"
)

# ==========================================
# 4. Endpoints REST
# ==========================================

@app.get("/salud", tags=["Mantenimiento"])
def verificar_salud():
    """Endpoint de verificación de estado (Healthcheck)."""
    return {"estado": "saludable", "fecha": datetime.utcnow()}

@app.post(
    "/analizar-reseña",
    response_model=ResenaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Opiniones"]
)
def analizar_y_registrar_reseña(resena: ResenaCreate, db: Session = Depends(get_db)):
    """
    Recibe y valida la reseña del cliente mediante Pydantic.
    Aplica la regla determinista en Python: si puntuación <= 2, se activa alerta_critica.
    Guarda el registro inicial en la base de datos y retorna la respuesta.
    """
    # Regla determinista dura en Python (Punto 3 del TP2)
    es_alerta_critica = resena.puntuacion <= 2

    # Creación del objeto DB
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

@app.get("/metricas", response_model=MetricasResponse, tags=["Dashboard"])
def obtener_metricas_dashboard(db: Session = Depends(get_db)):
    """
    Calcula determinísticamente las métricas agregadas de satisfacción
    para alimentar los componentes del dashboard en Streamlit.
    """
    resenas = db.query(ResenaDB).all()
    total = len(resenas)

    if total == 0:
        return MetricasResponse(
            total_resenas=0,
            promedio_satisfaccion=0.0,
            porcentaje_insatisfechos=0.0,
            alertas_criticas_activas=0,
            distribucion_puntuaciones={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            resenas_pendientes_atencion=0
        )

    suma_puntuaciones = sum(r.puntuacion for r in resenas)
    promedio = round(suma_puntuaciones / total, 2)
    
    insatisfechos = sum(1 for r in resenas if r.puntuacion <= 2)
    pct_insatisfechos = round((insatisfechos / total) * 100, 2)
    
    alertas_activas = sum(1 for r in resenas if r.alerta_critica and r.estado_gestion == "Pendiente")
    
    distribucion = {i: 0 for i in range(1, 6)}
    for r in resenas:
        if 1 <= r.puntuacion <= 5:
            distribucion[r.puntuacion] += 1

    pendientes = sum(1 for r in resenas if r.estado_gestion == "Pendiente")

    return MetricasResponse(
        total_resenas=total,
        promedio_satisfaccion=promedio,
        porcentaje_insatisfechos=pct_insatisfechos,
        alertas_criticas_activas=alertas_activas,
        distribucion_puntuaciones=distribucion,
        resenas_pendientes_atencion=pendientes
    )

@app.get("/reseñas", response_model=List[ResenaResponse], tags=["Opiniones"])
def listar_reseñas(
    sentimiento: Optional[str] = Query(None, description="Filtrar por sentimiento"),
    estado_gestion: Optional[str] = Query(None, description="Filtrar por estado_gestion"),
    db: Session = Depends(get_db)
):
    """Consulta la lista de reseñas con soporte para filtros de consulta (Punto 9 del TP2)."""
    query = db.query(ResenaDB)
    
    if sentimiento:
        query = query.filter(ResenaDB.sentimiento == sentimiento)
    if estado_gestion:
        query = query.filter(ResenaDB.estado_gestion == estado_gestion)
        
    return query.order_by(ResenaDB.fecha_creacion.desc()).all()

@app.patch("/reseñas/{resena_id}", response_model=ResenaResponse, tags=["Opiniones"])
def actualizar_reseña(
    resena_id: int,
    datos_actualizacion: ResenaPatch,
    db: Session = Depends(get_db)
):
    """
    Permite actualizar las etiquetas generadas por la IA o cambiar el estado de gestión (Punto 9 del TP2).
    """
    resena = db.query(ResenaDB).filter(ResenaDB.id == resena_id).first()
    if not resena:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reseña con ID {resena_id} no encontrada."
        )

    datos = datos_actualizacion.model_dump(exclude_unset=True)
    for clave, valor in datos.items():
        setattr(resena, clave, valor)

    db.commit()
    db.refresh(resena)
    return resena
