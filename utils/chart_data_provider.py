"""
Grafik verilerini hazırlayan modül.
Veritabanından verileri çeker, işler ve görselleştirme için hazırlar.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from models.bakim import Bakim, PilDegisim, Tezgah  # Doğru import yolu

class ChartDataProvider:
    """Grafikler için veri sağlayan sınıf."""
    
    @staticmethod
    def get_basic_stats(session: Session) -> Dict[str, Any]:
        """
        Temel istatistikleri hesaplar.
        
        Args:
            session (Session): Veritabanı oturumu
            
        Returns:
            Dict[str, Any]: İstatistikler
        """
        stats = {}
        
        # Toplam tezgah sayısı
        stats['toplam_tezgah'] = session.query(Tezgah).count()
        
        # Toplam bakım sayısı
        stats['toplam_bakim'] = session.query(Bakim).count()
        
        # Toplam pil değişim sayısı
        stats['toplam_pil_degisim'] = session.query(PilDegisim).count()
        
        # Son bakım tarihi
        son_bakim = session.query(Bakim).order_by(Bakim.tarih.desc()).first()
        stats['son_bakim_tarihi'] = son_bakim.tarih if son_bakim else '-'
        
        # Son pil değişim tarihi
        son_pil_degisim = session.query(PilDegisim).order_by(PilDegisim.tarih.desc()).first()
        stats['son_pil_degisim'] = son_pil_degisim.tarih if son_pil_degisim else '-'
        
        # Ortalama bakım sayısı (tezgah başına)
        if stats['toplam_tezgah'] > 0:
            stats['ortalama_bakim'] = round(stats['toplam_bakim'] / stats['toplam_tezgah'], 1)
        else:
            stats['ortalama_bakim'] = 0
            
        # Son güncelleme zamanı
        stats['son_guncelleme'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return stats
    
    @staticmethod
    def get_maintenance_by_month(session: Session, months: int = 12) -> Tuple[List[str], List[int]]:
        """
        Belirtilen ay sayısı kadar geçmiş aylar için aylık bakım sayılarını döndürür.
        
        Args:
            session (Session): Veritabanı oturumu
            months (int, optional): Kaç aylık veri getirileceği. Varsayılan 12.
            
        Returns:
            Tuple[List[str], List[int]]: (ay_etiketleri, bakım_sayıları)
        """
        # Başlangıç ve bitiş tarihlerini hesapla
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30*months)
        
        # Aylık bakım sayılarını sorgula
        results = session.query(
            func.strftime('%Y-%m', Bakim.tarih).label('month'),
            func.count(Bakim.id).label('count')
        ).filter(Bakim.tarih.between(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        ).group_by('month').order_by('month').all()
        
        # Boş ay listesi oluştur (son 12 ay için)
        all_months = []
        month_counts = {}
        
        # Son N ayı listeye ekle
        for i in range(months, 0, -1):
            month_date = end_date - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            all_months.append(month_key)
            month_counts[month_key] = 0
            
        # Veritabanından gelen verileri eşleştir
        for month, count in results:
            if month in month_counts:
                month_counts[month] = count
                
        # Görsel için etiketleri iyileştir (sadece ay)
        month_labels = []
        for month_key in all_months:
            year, month = month_key.split('-')
            month_labels.append(f"{month}/{year[2:]}")
            
        # Veriyi sıralanmış şekilde döndür
        return month_labels, [month_counts[month] for month in all_months]
        
    @staticmethod
    def get_top_tezgahlar_by_maintenance(session: Session, limit: int = 10) -> Tuple[List[str], List[int]]:
        """
        En çok bakım yapılan tezgahları döndürür.
        
        Args:
            session (Session): Veritabanı oturumu
            limit (int, optional): Kaç tezgah getirileceği. Varsayılan 10.
            
        Returns:
            Tuple[List[str], List[int]]: (tezgah_numaraları, bakım_sayıları)
        """
        # En çok bakım yapılan tezgahları sorgula
        results = session.query(
            Tezgah.numarasi,
            func.count(Bakim.id).label('bakim_count')
        ).join(Bakim).group_by(Tezgah.id).order_by(desc('bakim_count')).limit(limit).all()
        
        # Sonuçları ayır
        tezgah_numaralari = [str(result[0]) for result in results]
        bakim_sayilari = [result[1] for result in results]
        
        return tezgah_numaralari, bakim_sayilari
        
    @staticmethod
    def get_battery_change_by_month(session: Session, months: int = 12) -> Tuple[List[str], List[int]]:
        """
        Belirtilen ay sayısı kadar geçmiş aylar için aylık pil değişim sayılarını döndürür.
        
        Args:
            session (Session): Veritabanı oturumu
            months (int, optional): Kaç aylık veri getirileceği. Varsayılan 12.
            
        Returns:
            Tuple[List[str], List[int]]: (ay_etiketleri, pil_değişim_sayıları)
        """
        # Başlangıç ve bitiş tarihlerini hesapla
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30*months)
        
        # Aylık pil değişim sayılarını sorgula
        results = session.query(
            func.strftime('%Y-%m', PilDegisim.tarih).label('month'),
            func.count(PilDegisim.id).label('count')
        ).filter(PilDegisim.tarih.between(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        ).group_by('month').order_by('month').all()
        
        # Boş ay listesi oluştur (son N ay için)
        all_months = []
        month_counts = {}
        
        # Son N ayı listeye ekle
        for i in range(months, 0, -1):
            month_date = end_date - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            all_months.append(month_key)
            month_counts[month_key] = 0
            
        # Veritabanından gelen verileri eşleştir
        for month, count in results:
            if month in month_counts:
                month_counts[month] = count
                
        # Görsel için etiketleri iyileştir (sadece ay)
        month_labels = []
        for month_key in all_months:
            year, month = month_key.split('-')
            month_labels.append(f"{month}/{year[2:]}")
            
        # Veriyi sıralanmış şekilde döndür
        return month_labels, [month_counts[month] for month in all_months]
        
    @staticmethod
    def get_maintenance_distribution_by_tezgah(session: Session) -> Tuple[List[str], List[float]]:
        """
        Tezgah başına bakım dağılımını yüzde olarak hesaplar.
        
        Args:
            session (Session): Veritabanı oturumu
            
        Returns:
            Tuple[List[str], List[float]]: (tezgah_numaraları, yüzdeler)
        """
        # Toplam bakım sayısı
        total_maintenance = session.query(Bakim).count()
        if total_maintenance == 0:
            return [], []
            
        # Tezgah numaralarına göre bakım sayıları
        results = session.query(
            Tezgah.numarasi,
            func.count(Bakim.id).label('count')
        ).join(Bakim).group_by(Tezgah.numarasi).all()
        
        # En fazla 8 tezgah göster, geri kalanı "Diğer" olarak grupla
        results = sorted(results, key=lambda x: x[1], reverse=True)
        
        top_results = results[:8] if len(results) > 8 else results
        other_count = sum(count for _, count in results[8:]) if len(results) > 8 else 0
        
        # Sonuçları yüzdelere dönüştür
        categories = []
        percentages = []
        
        for tezgah_no, count in top_results:
            categories.append(f"Tezgah {tezgah_no}")
            percentages.append(round((count / total_maintenance) * 100, 1))
        
        # Diğer tezgahları ekle
        if other_count > 0:
            categories.append("Diğer Tezgahlar")
            percentages.append(round((other_count / total_maintenance) * 100, 1))
            
        return categories, percentages
