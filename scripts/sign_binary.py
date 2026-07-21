#!/usr/bin/env python
"""
Code signing script for Windows executables
Requires: Windows SDK, valid code signing certificate
"""
import sys
import subprocess
from pathlib import Path

def sign_binary(exe_path, cert_path=None, cert_password=None):
    """Sign a Windows executable"""

    # Use signtool from Windows SDK
    signtool = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"

    if not Path(signtool).exists():
        print("❌ signtool.exe not found. Install Windows SDK.")
        return False

    cmd = [
        signtool,
        "sign",
        "/fd", "sha256",
        "/tr", "http://timestamp.digicert.com",
        "/td", "sha256",
    ]

    if cert_path and cert_password:
        cmd.extend(["/f", cert_path, "/p", cert_password])
    else:
        # Use certificate store
        cmd.append("/a")

    cmd.append(str(exe_path))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Signed: {exe_path}")
        return True
    else:
        print(f"❌ Signing failed: {result.stderr}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sign_binary.py <path_to_exe> [cert_path] [cert_password]")
        sys.exit(1)

    exe = sys.argv[1]
    cert = sys.argv[2] if len(sys.argv) > 2 else None
    password = sys.argv[3] if len(sys.argv) > 3 else None

    sign_binary(exe, cert, password)
