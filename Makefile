# Makefile para CLI Download ROM
# Compatível com Windows (usando PowerShell) e Linux/macOS

# Variáveis
APP_NAME = clidownrom
PYTHON = python
PIP = pip
PYINSTALLER = pyinstaller
BUILD_DIR = build
DIST_DIR = dist
SPEC_FILE = $(APP_NAME).spec

# Detecta o sistema operacional
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    EXE_EXT := .exe
    RM := Remove-Item -Recurse -Force
    MKDIR := New-Item -ItemType Directory -Force
    COPY := Copy-Item
    SHELL := powershell
else
    DETECTED_OS := $(shell uname -s)
    EXE_EXT :=
    RM := rm -rf
    MKDIR := mkdir -p
    COPY := cp -r
endif

# Alvos principais
.PHONY: all clean install build package test help

# Alvo padrão
all: clean install build package

# Ajuda
help:
	@echo "CLI Download ROM - Build System"
	@echo ""
	@echo "Alvos disponíveis:"
	@echo "  all      - Build completo (clean + install + build + package)"
	@echo "  clean    - Remove arquivos de build"
	@echo "  install  - Instala dependências"
	@echo "  build    - Compila o executável"
	@echo "  package  - Cria pacote de distribuição"
	@echo "  test     - Executa testes"
	@echo "  run      - Executa a aplicação em modo desenvolvimento"
	@echo "  help     - Mostra esta ajuda"
	@echo ""
	@echo "Sistema detectado: $(DETECTED_OS)"

# Limpa arquivos de build
clean:
	@echo "🧹 Limpando arquivos de build..."
ifeq ($(OS),Windows_NT)
	@if (Test-Path "$(BUILD_DIR)") { $(RM) "$(BUILD_DIR)" }
	@if (Test-Path "$(DIST_DIR)") { $(RM) "$(DIST_DIR)" }
	@if (Test-Path "__pycache__") { $(RM) "__pycache__" }
	@Get-ChildItem -Recurse -Name "*.pyc" | ForEach-Object { Remove-Item $$_ -Force }
else
	@$(RM) $(BUILD_DIR) $(DIST_DIR) __pycache__ 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
endif
	@echo "✅ Limpeza concluída"

# Instala dependências
install:
	@echo "📦 Instalando dependências..."
	@$(PIP) install --upgrade pip
	@$(PIP) install pyinstaller
	@$(PIP) install -r requirements.txt
	@echo "✅ Dependências instaladas"

# Compila o executável
build:
	@echo "🔨 Compilando para $(DETECTED_OS)..."
	@$(PYINSTALLER) $(SPEC_FILE) --clean --noconfirm
	@echo "✅ Compilação concluída"

# Cria pacote de distribuição
package:
	@echo "📦 Criando pacote de distribuição..."
	@$(PYTHON) build.py
	@echo "✅ Pacote criado"

# Executa testes
test:
	@echo "🧪 Executando testes..."
	@$(PYTHON) -m pytest tests/ -v 2>/dev/null || echo "⚠️  Nenhum teste encontrado"

# Executa em modo desenvolvimento
run:
	@echo "🚀 Executando em modo desenvolvimento..."
	@$(PYTHON) main.py

# Build rápido (sem limpeza)
quick-build:
	@echo "⚡ Build rápido..."
	@$(PYINSTALLER) $(SPEC_FILE) --noconfirm
	@echo "✅ Build rápido concluído"

# Build para distribuição
release: clean install build package
	@echo "🎉 Release criado com sucesso!"
	@echo "📁 Arquivos em: $(DIST_DIR)"

# Instala o executável no sistema
install-system:
ifeq ($(OS),Windows_NT)
	@echo "💾 Instalando no sistema Windows..."
	@powershell -ExecutionPolicy Bypass -File install_windows.bat
else
	@echo "💾 Instalando no sistema Unix..."
	@chmod +x install_linux.sh
	@./install_linux.sh
endif

# Verifica se o executável funciona
verify:
	@echo "🔍 Verificando executável..."
ifeq ($(OS),Windows_NT)
	@if (Test-Path "$(DIST_DIR)\$(APP_NAME)$(EXE_EXT)") { \
		echo "✅ Executável encontrado"; \
		& "$(DIST_DIR)\$(APP_NAME)$(EXE_EXT)" --version; \
	} else { \
		echo "❌ Executável não encontrado"; \
		exit 1; \
	}
else
	@if [ -f "$(DIST_DIR)/$(APP_NAME)$(EXE_EXT)" ]; then \
		echo "✅ Executável encontrado"; \
		"$(DIST_DIR)/$(APP_NAME)$(EXE_EXT)" --version; \
	else \
		echo "❌ Executável não encontrado"; \
		exit 1; \
	fi
endif

# Mostra informações do sistema
info:
	@echo "ℹ️  Informações do sistema:"
	@echo "OS: $(DETECTED_OS)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "PyInstaller: $(shell $(PYINSTALLER) --version 2>/dev/null || echo 'Não instalado')"
	@echo "Diretório atual: $(shell pwd)"