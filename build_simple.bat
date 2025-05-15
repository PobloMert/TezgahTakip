@echo off
echo Tezgah Takip uygulaması derleniyor (basit yöntem)...

:: PyInstaller ile basit derleme
pyinstaller --onefile --windowed --icon=resources\icons\app_icon.ico --name=TezgahTakip main.py

echo Derleme tamamlandı! Exe dosyası "dist" klasöründe oluşturulmuş olmalı.
pause
