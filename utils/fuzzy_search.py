"""
Bulanık eşleştirme ile arama fonksiyonları
"""
from fuzzywuzzy import fuzz

def fuzzy_search(query, choices, threshold=70, processor=None):
    """
    Bulanık arama yapar
    :param query: Arama kelimesi
    :param choices: Arama yapılacak liste
    :param threshold: Eşleşme eşik değeri (0-100)
    :param processor: Veri ön işleme fonksiyonu
    :return: Eşleşen sonuçlar
    """
    if processor:
        processed_query = processor(query)
        processed_choices = [processor(item) for item in choices]
    else:
        processed_query = str(query).lower()
        processed_choices = [str(item).lower() for item in choices]
    
    results = []
    for i, item in enumerate(processed_choices):
        score = fuzz.partial_ratio(processed_query, item)
        if score > threshold:
            results.append((choices[i], score))
    
    # Skora göre sırala
    return [item[0] for item in sorted(results, key=lambda x: x[1], reverse=True)]
