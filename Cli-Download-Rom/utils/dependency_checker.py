import logging
import subprocess
import sys
import shutil
import requests
import zipfile
import io
import platform
from pathlib import Path
from .localization import t

def _get_aria2c_executable_name():
    return "aria2c.exe" if sys.platform == "win32" else "aria2c"

def _is_command_installed(command):
    local_bin_path = Path(__file__).parent.parent / 'bin'
    if (local_bin_path / command).exists():
        return True
    return shutil.which(command) is not None

def _download_and_install_aria2c_windows():
    print(f"ℹ️ {t.get_string('ARIA2C_AUTOINSTALL_START')}")
    is_64bit = platform.machine().endswith('64')
    url = (
        "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
        if is_64bit
        else "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-32bit-build1.zip"
    )
    bin_dir = Path(__file__).parent.parent / 'bin'
    bin_dir.mkdir(exist_ok=True)
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            for member in zf.infolist():
                if member.filename.endswith('aria2c.exe'):
                    with zf.open(member) as source, open(bin_dir / 'aria2c.exe', 'wb') as target:
                        shutil.copyfileobj(source, target)
                    print(f"✔️ {t.get_string('ARIA2C_AUTOINSTALL_SUCCESS')}")
                    return True
        raise FileNotFoundError("aria2c.exe not found in the downloaded archive.")
    except Exception as e:
        logging.error(f"Falha no download automático do aria2c: {e}")
        print(f"❌ {t.get_string('ARIA2C_AUTOINSTALL_FAILED')}")
        return False

def check_system_dependencies():
    if not _is_command_installed('git'):
        print(f"❌ {t.get_string('ERROR_GIT_NOT_FOUND')}")
        print(f"   {t.get_string('ERROR_GIT_NOT_FOUND_INSTRUCTIONS')}")
        sys.exit(1)
    executable_name = _get_aria2c_executable_name()
    if not _is_command_installed(executable_name):
        if sys.platform == "win32":
            if not _download_and_install_aria2c_windows():
                sys.exit(1)
        elif sys.platform == "linux":
            print(f"❌ {t.get_string('ERROR_ARIA2C_NOT_FOUND')}")
            print(f"   {t.get_string('ERROR_ARIA2C_LINUX_INSTRUCTIONS')}")
            sys.exit(1)
        elif sys.platform == "darwin":
            print(f"❌ {t.get_string('ERROR_ARIA2C_NOT_FOUND')}")
            print(f"   {t.get_string('ERROR_ARIA2C_MACOS_INSTRUCTIONS')}")
            sys.exit(1)
        else:
            print(f"❌ Sistema operacional '{sys.platform}' não suportado para instalação automática do aria2c.")
            sys.exit(1)