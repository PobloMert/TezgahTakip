from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime

class PilDegisim(Base):
    __tablename__ = 'pil_degisimler'
    
    id = Column(Integer, primary_key=True)
    tezgah_id = Column(Integer, ForeignKey('tezgah.id'))
    degisim_tarihi = Column(DateTime, default=datetime.now)
    degistiren_kisi = Column(String(100))
    aciklama = Column(String(255))
    
    tezgah = relationship("Tezgah", back_populates="pil_degisimler")
