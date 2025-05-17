# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Ana dizini belirle
main_dir = os.path.abspath(SPECPATH)

# Ek dosyaları topla
added_files = [
    ('database/*.db', 'database'),
    ('resources/icons/*', 'resources/icons'),
    ('resources/fonts/*', 'resources/fonts'),
]

# PyQt5 bağımlılıklarını dahil et
qt_plugins = [
    ('PyQt5/Qt5/plugins/platforms', 'platforms'),
    ('PyQt5/Qt5/plugins/imageformats', 'imageformats'),
    ('PyQt5/Qt5/plugins/styles', 'styles'),
]

a = Analysis(
    [os.path.join(main_dir, 'main.py')],
    pathex=[main_dir],
    binaries=[],
    datas=added_files + qt_plugins,
    hiddenimports=['PyQt5.sip'] + collect_submodules('sqlalchemy'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TezgahTakip',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=os.path.join(main_dir, 'resources', 'icons', 'app_icon.ico') if os.path.exists(os.path.join(main_dir, 'resources', 'icons', 'app_icon.ico')) else None,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
