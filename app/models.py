from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.database import Base

class ResenaDB(Base):
    __tablename__ = "resenas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cliente = Column(String(100), nullable=False)
    correo = Column(String(120), nullable=False, index=True)
    puntuacion = Column(Integer, nullable=False)
    comentario = Column(Text, nullable=False)
    categoria = Column(String(50), default="General")
    alerta_critica = Column(Boolean, default=False)
    
    # Campos enriquecidos por la IA (Gemini AI / n8n)
    sentimiento = Column(String(20), default="Pendiente")     # Positivo, Neutro, Negativo
    categoria_ia = Column(String(50), default="Sin clasificar")
    resumen_ia = Column(Text, nullable=True)
    
    # Estado de gestión del equipo de soporte
    estado_gestion = Column(String(20), default="Pendiente") # Pendiente, Atendido
    fecha_creacion = Column(DateTime, default=datetime.utcnow)