@echo off
echo Tezgah Takip uygulaması derleniyor...

:: PyInstaller ile derle
pyinstaller --clean tezgah_takip.spec

echo Derleme tamamlandı! Exe dosyası "dist" klasöründe oluşturuldu.
echo Uygulamanın güncellemelerini GitHub'da yayınlamak için şu adımları izleyin:

echo 1. GitHub'da TezgahTakip reposuna gidin
echo 2. "Releases" bölümüne tıklayın
echo 3. "Draft a new release" butonuna tıklayın
echo 4. Sürüm etiketi olarak (örn: v1.0.0) girin
echo 5. Sürüm başlığı ve açıklaması ekleyin
echo 6. "dist\TezgahTakip.exe" dosyasını sürücüye yükleyin
echo 7. "Publish release" butonuna tıklayın

pause
