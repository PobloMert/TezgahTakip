@echo off
setlocal

REM Gerekli paketlerin kurulumu
pip install pyinstaller

REM EXE oluşturma
pyinstaller --onefile --windowed ^
    --name "TezgahTakip" ^
    --icon "icon.ico" ^
    --add-data "data;data" ^
    --add-data "ui;ui" ^
    --add-data "utils;utils" ^
    --hidden-import "PyQt5.QtWidgets" ^
    --hidden-import "sqlalchemy" ^
    main.py

pause
