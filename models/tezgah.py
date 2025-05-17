"""
Tezgah modeli
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime

class Tezgah(Base):
    __tablename__ = 'tezgah'
    
    id = Column(Integer, primary_key=True)
    numarasi = Column(String(50), unique=True, nullable=False)
    aciklama = Column(String(255), nullable=True, comment='Tezgah açıklaması')
    durum = Column(String(20), default='aktif')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # İlişkiler
    bakimlar = relationship("Bakim", back_populates="tezgah", cascade="all, delete-orphan")
    pil_degisimler = relationship("PilDegisim", back_populates="tezgah", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tezgah(numarasi='{self.numarasi}', durum='{self.durum}')>"
