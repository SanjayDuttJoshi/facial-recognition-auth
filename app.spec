# -*- mode: python ; coding: utf-8 -*-
import os

# Get the absolute path to the templates and static directories
project_dir = os.path.abspath('.')
templates_path = os.path.join(project_dir, 'templates')
static_path = os.path.join(project_dir, 'static')

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        ('face_recognition_models/models/shape_predictor_68_face_landmarks.dat', 'face_recognition_models/models'),
        ('templates', 'templates'),
        ('static', 'static'),
        ('face_auth.db', '.'),
    ],
    hiddenimports=[],
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
    a.datas,
    [],
    name='FaceRecognitionApp.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False to hide console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/favicon.ico' if os.path.exists('static/favicon.ico') else None,
) 