from database.connection import db_manager

# Eksen kolonunu eklemek için SQL komutu
sql = """
ALTER TABLE bakimlar 
ADD COLUMN eksen TEXT NOT NULL DEFAULT 'TUM';
"""

# Migrasyonu çalıştır
try:
    with db_manager.Session() as session:
        session.execute(sql)
        session.commit()
    print("Eksen kolonu başarıyla eklendi")
except Exception as e:
    print(f"Hata oluştu: {e}")
