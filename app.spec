# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Ensure database exists
if not os.path.exists('face_auth.db'):
    import sqlite3
    conn = sqlite3.connect('face_auth.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, face_encoding BLOB NOT NULL)')
    conn.close()

# Define model file paths
model_paths = [
    ('face_recognition_models/models/shape_predictor_68_face_landmarks.dat', 'face_recognition_models/models'),
    ('shape_predictor_68_face_landmarks.dat', '.'),
    ('models/shape_predictor_68_face_landmarks.dat', 'models'),
]

# Filter out non-existent paths
valid_model_paths = [(src, dst) for src, dst in model_paths if os.path.exists(src)]

if not valid_model_paths:
    raise FileNotFoundError("Could not find shape_predictor_68_face_landmarks.dat in any of the expected locations")

a = Analysis(
    ['app.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        *valid_model_paths,  # Include all valid model paths
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
) 