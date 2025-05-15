import os
import subprocess
import sys

def create_virtual_env():
    """Sanal ortam oluştur"""
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

def install_dependencies():
    """Bağımlılıkları yükle"""
    pip_path = os.path.join("venv", "Scripts", "pip") if sys.platform == "win32" else os.path.join("venv", "bin", "pip")
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)

def run_migrations():
    """Veritabanı migrasyonlarını çalıştır"""
    alembic_path = os.path.join("venv", "Scripts", "alembic") if sys.platform == "win32" else os.path.join("venv", "bin", "alembic")
    subprocess.run([alembic_path, "upgrade", "head"], check=True)

def build_executable():
    """PyInstaller ile çalıştırılabilir dosya oluştur"""
    pyinstaller_path = os.path.join("venv", "Scripts", "pyinstaller") if sys.platform == "win32" else os.path.join("venv", "bin", "pyinstaller")
    subprocess.run([
        pyinstaller_path, 
        "--onefile", 
        "--windowed", 
        "--add-data", "arial.ttf:.", 
        "main.py"
    ], check=True)

def main():
    try:
        create_virtual_env()
        install_dependencies()
        run_migrations()
        build_executable()
        print("Build işlemi başarıyla tamamlandı!")
    except Exception as e:
        print(f"Build sırasında hata oluştu: {e}")

if __name__ == "__main__":
    main()
