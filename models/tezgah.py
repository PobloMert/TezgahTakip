"""
Tezgah modeli
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TezgahModel(Base):
    __tablename__ = 'tezgah'
    __table_args__ = {'extend_existing': True}  # Çakışmayı önle
    
    id = Column(Integer, primary_key=True)
    tezgah_no = Column(String(50), unique=True)
    lokasyon = Column(String(100))
    durum = Column(String(20))
    aciklama = Column(String(255), nullable=True, comment='Tezgah açıklaması')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # İlişkiler
    bakimlar = relationship("Bakim", back_populates="tezgah", cascade="all, delete-orphan")
    pil_degisimler = relationship("PilDegisim", back_populates="tezgah", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TezgahModel(tezgah_no='{self.tezgah_no}', durum='{self.durum}')>"
