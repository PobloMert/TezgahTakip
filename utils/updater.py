import os
import sys
import logging
import requests
import tempfile
import subprocess
import json
import time
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox
from packaging import version
from ui.update_animation import UpdateAnimation

class AutoUpdater:
    def __init__(self, github_username, repo_name, current_version):
        self.github_username = github_username
        self.repo_name = repo_name
        self.current_version = current_version
        self.settings_path = Path(__file__).parent.parent / 'settings.json'
        self.last_check = 0
        self.animation = UpdateAnimation()
        
    def should_check_for_updates(self):
        """Son kontrol zamanını kontrol eder"""
        try:
            with open(self.settings_path, 'r') as f:
                settings = json.load(f)
            
            last_check = settings.get('last_update_check', 0)
            interval = settings.get('update_check_interval', 86400)  # Varsayılan: 24 saat
            
            return (time.time() - last_check) > interval
        except Exception:
            return True  # Hata durumunda kontrol yap

    def update_last_check_time(self):
        """Son kontrol zamanını günceller"""
        try:
            with open(self.settings_path, 'r+') as f:
                settings = json.load(f)
                settings['last_update_check'] = int(time.time())
                f.seek(0)
                json.dump(settings, f, indent=4)
                f.truncate()
        except Exception as e:
            logging.error(f"Ayarlar güncellenirken hata: {e}")

    def check_for_updates(self, force=False):
        """
        GitHub'dan en son sürümü kontrol eder
        :param force: Güncelleme kontrolünü zorla yap (varsayılan: False)
        :return: (update_available: bool, latest_version: str)
        """
        try:
            if not force and (time.time() - self.last_check) < 3600:  # 1 saatten azsa atla
                return {'update_available': False}
            
            self.last_check = time.time()
            headers = {'Accept': 'application/vnd.github.v3+json'}
            url = f'https://api.github.com/repos/{self.github_username}/{self.repo_name}/releases/latest'
            
            # API isteği
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Version kontrol
            latest_version = response.json().get('tag_name', '').lstrip('v')
            if not latest_version:
                return {'update_available': False}
                
            # Versiyon karşılaştırma
            if version.parse(latest_version) > version.parse(self.current_version):
                return {
                    'update_available': True,
                    'latest_version': latest_version,
                    'release_notes': response.json().get('body', '')
                }
            return {'update_available': False}
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"Güncelleme kontrolü başarısız: {str(e)}")
            return {'update_available': False}
        except Exception as e:
            logging.error(f"Beklenmeyen güncelleme hatası: {str(e)}")
            return {'update_available': False}

    def _find_download_url(self, release_info):
        for asset in release_info["assets"]:
            if asset["name"].endswith(".exe"):
                return asset["browser_download_url"]
        return None

    def _prompt_update(self, new_version, download_url, description):
        reply = QMessageBox.question(
            None, 
            "Güncelleme Mevcut", 
            f"Yeni sürüm {new_version} mevcut!\n\nDeğişiklikler:\n{description}\n\nŞimdi güncellemek ister misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.download_update({'assets': [{'browser_download_url': download_url}]})

    def download_update(self, release_info):
        try:
            self.animation.start_animation()
            
            # İndirme işlemleri
            download_url = self._find_download_url(release_info)
            
            # İndirme tamamlandığında
            self.animation.stop_animation(
                "Güncelleme başarıyla indirildi!\nUygulama kapanıp yeniden başlatılacak",
                is_success=True
            )
            
            # Kurulum işlemleri...
            self._install_update(download_url)
            
        except Exception as e:
            self.animation.stop_animation(
                f"Güncelleme hatası:\n{str(e)}",
                is_success=False
            )
            logging.error(f"Güncelleme hatası: {e}")

    def _install_update(self, download_url):
        current_executable = sys.executable
        app_name = os.path.basename(current_executable)
        temp_dir = tempfile.gettempdir()
        new_exe_path = os.path.join(temp_dir, f"TezgahTakip_update.exe")

        # İndirme işlemi
        response = requests.get(download_url, stream=True, timeout=60)
        
        if response.status_code == 200:
            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Güncelleme batch dosyası
            batch_path = os.path.join(temp_dir, "update_tezgahtakip.bat")
            batch_content = f"""@echo off
echo Tezgah Takip Programı güncelleniyor...
timeout /t 2 /nobreak > nul

:: Uygulamayı kapat
taskkill /F /IM "{app_name}" > nul 2>&1
timeout /t 1 /nobreak > nul

:: Yeni sürümü yükle
copy /Y "{new_exe_path}" "{current_executable}" > nul
if not exist "{current_executable}" (
    echo Güncelleme hatası! Orijinal uygulama bulunamadı.
    pause
    exit /b 1
)

:: Geçici dosyaları temizle
del "{new_exe_path}" > nul 2>&1

:: Uygulamayı başlat
start "" "{current_executable}"

:: Bu batch dosyasını sil
del "%~f0" > nul
"""
            with open(batch_path, 'w') as f:
                f.write(batch_content)

            subprocess.Popen(batch_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)
