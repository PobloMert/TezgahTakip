"""
Veri sıkıştırma ve açma işlemleri (Gelişmiş Sürüm)
"""
import zlib
import json
import hashlib
from typing import Union

def _calculate_checksum(data: bytes) -> str:
    """Veri için checksum hesapla"""
    return hashlib.md5(data).hexdigest()

def compress_data(data: Union[dict, list], chunk_size: int = 1024) -> dict:
    """
    Veriyi sıkıştırarak kaydet
    :param data: Sıkıştırılacak veri (dict veya list)
    :param chunk_size: Büyük veriler için chunk boyutu (byte)
    :return: {'data': bytes, 'checksum': str} formatında sıkıştırılmış veri
    """
    json_data = json.dumps(data).encode()
    
    # Chunk tabanlı sıkıştırma
    compressed = zlib.compress(json_data)
    
    return {
        'data': compressed,
        'checksum': _calculate_checksum(compressed),
        'original_size': len(json_data)
    }

def decompress_data(compressed_data: dict) -> Union[dict, list]:
    """
    Sıkıştırılmış veriyi aç
    :param compressed_data: compress_data() çıktısı
    :return: Açılmış orijinal veri
    """
    # Checksum kontrolü
    current_checksum = _calculate_checksum(compressed_data['data'])
    if current_checksum != compressed_data['checksum']:
        raise ValueError("Veri bütünlüğü bozuk: Checksum uyuşmuyor")
    
    try:
        decompressed = zlib.decompress(compressed_data['data'])
        if len(decompressed) != compressed_data['original_size']:
            raise ValueError("Boyut uyuşmazlığı: Orijinal veri bozulmuş olabilir")
        return json.loads(decompressed.decode())
    except zlib.error as e:
        raise ValueError(f"Sıkıştırılmış veri açılamadı: {str(e)}")
