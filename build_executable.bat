@echo off
echo Tezgah Takip Uygulamasi EXE formatina donusturuluyor...

:: PyInstaller komutu
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --clean ^
    --name=TezgahTakip ^
    --hidden-import=PyQt5.QtChart ^
    --hidden-import=PyQt5.sip ^
    --hidden-import=sqlalchemy.sql.default_comparator ^
    main.py

echo.
echo Islemi tamamlamak icin bir tusa basin...
pause > nul
