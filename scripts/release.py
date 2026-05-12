#!/usr/bin/env python
"""
GitHub Release Script for ScoobyBench
Creates a release on GitHub with the built installer
"""
import os
import sys
import json
import subprocess
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def get_version():
    """Get version from package.json"""
    with open(FRONTEND_DIR / "package.json") as f:
        data = json.load(f)
    return data["version"]

def create_release(token, version, draft=True):
    """Create GitHub release"""
    repo = "yourusername/scoobybench"  # Update this
    url = f"https://api.github.com/repos/{repo}/releases"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "tag_name": f"v{version}",
        "name": f"ScoobyBench v{version}",
        "body": f"""## ScoobyBench v{version}

### What's New
- AI model benchmarking with ONNX Runtime
- Real-time system telemetry monitoring
- Hardware detection and model recommendations
- JSON report export and comparison

### Downloads
- **Installer**: ScoobyBench Setup {version}.exe (Recommended)
- **Portable**: ScoobyBench {version}.exe (No installation required)

### System Requirements
- Windows 10/11 64-bit
- 4GB RAM minimum (8GB recommended)
- Python 3.10+ (for development)

### Installation
1. Download the installer or portable version
2. Run the .exe file
3. The app will automatically start the backend server
4. Access via system tray or desktop shortcut
""",
        "draft": draft,
        "prerelease": False
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()["upload_url"]
    else:
        print(f"❌ Failed to create release: {response.status_code}")
        print(response.text)
        return None

def upload_asset(upload_url, file_path, token):
    """Upload asset to release"""
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/octet-stream"
    }

    name = Path(file_path).name
    url = upload_url.replace("{?name,label}", f"?name={name}")

    with open(file_path, "rb") as f:
        response = requests.post(url, headers=headers, data=f)

    if response.status_code == 201:
        print(f"✅ Uploaded {name}")
        return True
    else:
        print(f"❌ Failed to upload {name}: {response.status_code}")
        return False

def main():
    """Main release pipeline"""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN environment variable required")
        sys.exit(1)

    version = get_version()
    print(f"🚀 Creating release for v{version}")

    upload_url = create_release(token, version)
    if not upload_url:
        sys.exit(1)

    # Upload assets
    dist_dir = FRONTEND_DIR / "dist"
    assets = [
        dist_dir / f"ScoobyBench Setup {version}.exe",
        dist_dir / f"ScoobyBench {version}.exe",
    ]

    for asset in assets:
        if asset.exists():
            upload_asset(upload_url, str(asset), token)
        else:
            print(f"⚠️ Asset not found: {asset}")

    print(f"
🎉 Release v{version} created!")
    print(f"🔗 Check GitHub releases page")

if __name__ == "__main__":
    main()
