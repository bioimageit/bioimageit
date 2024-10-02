# -*- mode: python ; coding: utf-8 -*-
import platform

a = Analysis(
    ['bioimageit.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='bioimageit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['PyFlow/UI/resources/Logo.icns' if platform.system() == 'Darwin' else 'PyFlow/UI/resources/Logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='bioimageit',
)
app = BUNDLE(
    coll,
    name='BioImageIT.app',
    icon='PyFlow/UI/resources/Logo.icns',
    bundle_identifier=None,
)
