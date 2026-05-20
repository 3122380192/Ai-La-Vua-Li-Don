# -*- mode: python ; coding: utf-8 -*-
import os

# Use local files from the project directory
PATCH_PRINT_EXE = os.path.abspath('A-PatchPrint.exe')
PS_AUTO_EXE     = os.path.abspath('PS_Auto_GUI1.exe')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[
        (PATCH_PRINT_EXE, 'tools'),
        (PS_AUTO_EXE,     'tools'),
    ],
    datas=[
        ('app_icon.png', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask.json',
        'werkzeug',
        'werkzeug.serving',
        'requests',
        'keyboard',
        'psutil',
        'yt_dlp',
        'pyautogui',
        'pyperclip',
        'bs4',
        'PIL',
        'PIL.Image',
        'win32gui',
        'win32con',
        'win32process',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt6'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TX_Embroider_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon='app_icon.png',
)
