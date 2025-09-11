#!/usr/bin/env python3
"""
Script de build para compilar CLI Download ROM para Windows e Linux
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Configurações
APP_NAME = "clidownrom"
MAIN_SCRIPT = "main.py"
BUILD_DIR = "build"
DIST_DIR = "dist"
ICON_FILE = None  # Adicione o caminho do ícone se tiver

def clean_build():
    """Remove diretórios de build anteriores"""
    print("🧹 Limpando builds anteriores...")
    for dir_name in [BUILD_DIR, DIST_DIR, "__pycache__"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removido: {dir_name}")

def install_dependencies():
    """Instala dependências necessárias para o build"""
    print("📦 Instalando dependências de build...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

def build_executable():
    """Compila o executável usando PyInstaller"""
    print(f"🔨 Compilando para {platform.system()}...")
    
    # Comando base do PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", APP_NAME,
        "--clean",
        "--noconfirm",
        "--add-data", "src;src",
        "--hidden-import", "src",
        "--hidden-import", "src.api",
        "--hidden-import", "src.core",
        "--hidden-import", "src.download",
        "--hidden-import", "src.interfaces",
        "--hidden-import", "src.locales",
        "--hidden-import", "src.utils",
    ]
    
    # Adiciona ícone se disponível
    if ICON_FILE and os.path.exists(ICON_FILE):
        cmd.extend(["--icon", ICON_FILE])
    
    # Adiciona script principal
    cmd.append(MAIN_SCRIPT)
    
    # Executa PyInstaller
    subprocess.run(cmd, check=True)
    print("✅ Compilação concluída!")

def create_install_scripts():
    """Cria scripts de instalação para adicionar ao PATH"""
    print("📝 Criando scripts de instalação...")
    
    # Script para Windows
    windows_script = """
@echo off
echo Instalando CLI Download ROM...

set "INSTALL_DIR=%USERPROFILE%\\clidownrom"
set "EXE_PATH=%~dp0clidownrom.exe"

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy "%EXE_PATH%" "%INSTALL_DIR%\\"

echo Adicionando ao PATH...
setx PATH "%PATH%;%INSTALL_DIR%"

echo.
echo ✅ Instalação concluída!
echo Reinicie o terminal para usar o comando 'clidownrom'
echo.
pause
"""
    
    with open("install_windows.bat", "w", encoding="utf-8") as f:
        f.write(windows_script)
    
    # Script para Linux
    linux_script = """
#!/bin/bash
echo "Instalando CLI Download ROM..."

INSTALL_DIR="$HOME/.local/bin"
EXE_PATH="$(dirname "$0")/clidownrom"

# Cria diretório se não existir
mkdir -p "$INSTALL_DIR"

# Copia executável
cp "$EXE_PATH" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/clidownrom"

# Adiciona ao PATH se não estiver
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo "export PATH=\"$INSTALL_DIR:\\$PATH\"" >> ~/.bashrc
    echo "export PATH=\"$INSTALL_DIR:\\$PATH\"" >> ~/.zshrc 2>/dev/null || true
fi

echo
echo "✅ Instalação concluída!"
echo "Reinicie o terminal ou execute: source ~/.bashrc"
echo "Depois use o comando 'clidownrom'"
echo
"""
    
    with open("install_linux.sh", "w", encoding="utf-8") as f:
        f.write(linux_script)
    
    # Torna o script Linux executável
    if platform.system() != "Windows":
        os.chmod("install_linux.sh", 0o755)
    
    print("   Criado: install_windows.bat")
    print("   Criado: install_linux.sh")

def create_readme_build():
    """Cria README específico para o build"""
    readme_content = """
# CLI Download ROM - Executável

## Instalação

### Windows
1. Execute `install_windows.bat` como administrador
2. Reinicie o terminal
3. Use o comando `clidownrom`

### Linux
1. Execute `chmod +x install_linux.sh && ./install_linux.sh`
2. Reinicie o terminal ou execute `source ~/.bashrc`
3. Use o comando `clidownrom`

## Uso

```bash
# Buscar ROMs
clidownrom search "Super Mario" --platform snes

# Download
clidownrom download --id 12345

# Interface interativa
clidownrom --interface shell

# Ajuda
clidownrom --help
```

## Desinstalação

### Windows
Remova a pasta `%USERPROFILE%\\clidownrom` e edite as variáveis de ambiente para remover do PATH.

### Linux
Remova o arquivo `~/.local/bin/clidownrom` e edite `~/.bashrc` para remover a linha do PATH.
"""
    
    with open(os.path.join(DIST_DIR, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)

def package_release():
    """Empacota o release final"""
    print("📦 Empacotando release...")
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # Nome do pacote
    package_name = f"clidownrom-{system}-{arch}"
    package_dir = os.path.join(DIST_DIR, package_name)
    
    # Cria diretório do pacote
    os.makedirs(package_dir, exist_ok=True)
    
    # Copia executável
    exe_name = f"{APP_NAME}.exe" if system == "windows" else APP_NAME
    exe_path = os.path.join(DIST_DIR, exe_name)
    
    if os.path.exists(exe_path):
        shutil.copy2(exe_path, package_dir)
    
    # Copia scripts de instalação
    if system == "windows":
        shutil.copy2("install_windows.bat", package_dir)
    else:
        shutil.copy2("install_linux.sh", package_dir)
    
    # Copia README
    shutil.copy2(os.path.join(DIST_DIR, "README.txt"), package_dir)
    
    print(f"✅ Pacote criado: {package_dir}")

def main():
    """Função principal do build"""
    print("🚀 Iniciando build do CLI Download ROM")
    print(f"Sistema: {platform.system()} {platform.machine()}")
    print()
    
    try:
        clean_build()
        install_dependencies()
        build_executable()
        create_install_scripts()
        create_readme_build()
        package_release()
        
        print()
        print("🎉 Build concluído com sucesso!")
        print(f"📁 Arquivos em: {os.path.abspath(DIST_DIR)}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro durante o build: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()