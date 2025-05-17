"""
Önceden tanımlı hızlı rapor şablonları (Güvenli Sürüm)
"""
from database.connection import db_manager
from typing import Dict, Any, Optional
import logging

class QuickReportGenerator:
    report_templates = {
        'daily_maintenance': {
            'query': "SELECT * FROM bakimlar WHERE tarih = :date",
            'title': "Günlük Bakım Raporu",
            'params': {'date': 'CURRENT_DATE'}
        },
        'weekly_battery': {
            'query': """
                SELECT t.tezgah_no, p.tarih, p.aciklama 
                FROM pil_degisimler p
                JOIN tezgahlar t ON p.tezgah_id = t.id
                WHERE p.tarih >= DATE(:start_date)
                ORDER BY p.tarih DESC
            """,
            'title': "Son 7 Gün Pil Değişimleri",
            'params': {'start_date': 'now, -7 days'}
        }
    }
    
    @classmethod
    def generate(cls, report_type: str, custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Hızlı rapor oluştur
        :param report_type: report_templates'de tanımlı rapor tipi
        :param custom_params: Varsayılan parametreleri override edecek değerler
        :return: {'title': str, 'data': list} formatında rapor
        """
        if report_type not in cls.report_templates:
            raise ValueError(f"Geçersiz rapor tipi: {report_type}")
            
        template = cls.report_templates[report_type]
        params = template.get('params', {}).copy()
        
        # Özel parametreleri birleştir
        if custom_params:
            params.update(custom_params)
        
        try:
            # Parametre binding ile güvenli sorgu
            results = db_manager.execute_query(
                template['query'],
                params=params,
                safe=True
            )
            return {
                'title': template['title'],
                'data': results,
                'params': params
            }
        except Exception as e:
            logging.error(f"Rapor oluşturma hatası ({report_type}): {str(e)}")
            return {
                'title': template['title'],
                'data': [],
                'error': str(e)
            }
