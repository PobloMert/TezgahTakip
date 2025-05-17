@echo off
setlocal

REM Gerekli paketler
pip install pyinstaller

REM Temizleme
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM EXE oluşturma
pyinstaller --onefile --windowed ^
    --name "TezgahTakip" ^
    --icon "ui/assets/app_icon.ico" ^
    --add-data "ui/assets;ui/assets" ^
    --add-data "database;database" ^
    --add-data "models;models" ^
    --add-data "ui;ui" ^
    --add-data "utils;utils" ^
    --hidden-import "PyQt5.QtWidgets" ^
    --hidden-import "sqlalchemy" ^
    --clean ^
    main.py

REM EXE'yi ana dizine kopyala
copy "dist\TezgahTakip.exe" .

pause
