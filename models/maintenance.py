from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import sqlalchemy

Base = declarative_base()

# BaseModel removed to match existing database structure

class Tezgah(Base):
    id = Column(Integer, primary_key=True)
    __tablename__ = 'tezgah'
    __table_args__ = (
        # Eski veritabanı için indeks kaldırıldı
    )

    numarasi = Column(String, unique=True, nullable=False, index=True)
    # Eski veritabanı yapısı için kaldırıldı
    bakimlar = relationship("Bakim", back_populates="tezgah", cascade="all, delete-orphan")
    pil_degisimleri = relationship("PilDegisim", back_populates="tezgah", cascade="all, delete-orphan")

class Bakim(Base):
    __tablename__ = 'bakimlar'
    
    id = Column(Integer, primary_key=True)
    tezgah_id = Column(Integer, ForeignKey('tezgah.id', ondelete='CASCADE'), nullable=False, index=True)
    tarih = Column(DateTime, default=datetime.now, nullable=False, index=True)
    bakim_yapan = Column(String, nullable=False, index=True)
    aciklama = Column(String)
    durum = Column(String, default='Bekliyor', nullable=False, index=True)

    tezgah = relationship("Tezgah", back_populates="bakimlar")

class PilDegisim(Base):
    id = Column(Integer, primary_key=True)
    __tablename__ = 'pil_degisim'
    __table_args__ = (
        Index('idx_pil_degisim_tarih', 'tarih'),
        Index('idx_pil_degisim_tezgah_eksen', 'tezgah_id', 'eksen'),
    )

    tezgah_id = Column(Integer, ForeignKey('tezgah.id', ondelete='CASCADE'), nullable=False, index=True)
    eksen = Column(String, nullable=False, index=True)
    pil_modeli = Column(String, nullable=False, index=True)
    tarih = Column(String, nullable=False, index=True)
    bakim_yapan = Column(String, nullable=False, index=True)


    tezgah = relationship("Tezgah", back_populates="pil_degisimleri")
