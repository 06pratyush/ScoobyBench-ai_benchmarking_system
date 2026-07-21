#!/usr/bin/env python
"""
ScoobyBench Build Script
Builds the complete application for Windows distribution:
1. Package Python backend with PyInstaller
2. Build Electron frontend
3. Package everything into single installer
"""
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

def clean_build():
    """Clean previous build artifacts"""
    print("Cleaning build directories...")
    for d in [DIST_DIR, BUILD_DIR, BACKEND_DIR / "dist", FRONTEND_DIR / "dist"]:
        if d.exists():
            shutil.rmtree(d)
    print("Clean complete")

def build_backend():
    """Package Python backend with PyInstaller"""
    print("Building Python backend...")

    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

a = Analysis(
    ['{BACKEND_DIR / "run.py"}'],
    pathex=['{BACKEND_DIR}'],
    binaries=[],
    datas=[
        ('{BACKEND_DIR / "app"}', 'app'),
        ('{PROJECT_ROOT / "config"}', 'config'),
    ],
    hiddenimports=[
        'uvicorn',
        'fastapi',
        'pydantic',
        'psutil',
        'numpy',
        'wmi',
        'cpuinfo',
        'onnxruntime',
        'pynvml',
        'websockets',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'PIL', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='scoobybench-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

    spec_path = BUILD_DIR / "backend.spec"
    spec_path.parent.mkdir(exist_ok=True)
    with open(spec_path, 'w') as f:
        f.write(spec_content)

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec_path), "--clean", "--noconfirm"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("ERROR: Backend build failed:")
        print(result.stderr)
        return False

    print("Backend built successfully")
    return True

def build_frontend():
    """Build Electron frontend"""
    print("Building Electron frontend...")

    result = subprocess.run(
        ["npm", "install"],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("ERROR: npm install failed:")
        print(result.stderr)
        return False

    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("ERROR: Frontend build failed:")
        print(result.stderr)
        return False

    print("Frontend built successfully")
    return True

def package_app():
    """Package complete application with electron-builder"""
    print("Packaging application...")

    backend_dist = PROJECT_ROOT / "dist" / "backend"
    backend_dist.mkdir(parents=True, exist_ok=True)

    pyinstaller_dist = PROJECT_ROOT / "dist" / "scoobybench-backend"
    if pyinstaller_dist.exists():
        shutil.copytree(pyinstaller_dist, backend_dist, dirs_exist_ok=True)

    result = subprocess.run(
        ["npm", "run", "dist:win"],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("ERROR: Packaging failed:")
        print(result.stderr)
        return False

    print("Application packaged successfully")
    return True

def main():
    """Main build pipeline"""
    print("ScoobyBench Build Pipeline")
    print("=" * 40)

    clean_build()

    if not build_backend():
        sys.exit(1)

    if not build_frontend():
        sys.exit(1)

    if not package_app():
        sys.exit(1)

    print("\nBuild complete!")
    print(f"Output: {FRONTEND_DIR / 'dist'}")
    print(f"Installer: {FRONTEND_DIR / 'dist' / 'ScoobyBench Setup.exe'}")
    print(f"Portable: {FRONTEND_DIR / 'dist' / 'ScoobyBench.exe'}")

if __name__ == "__main__":
    main()
