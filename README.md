# CLI Download ROM

[![Status](https://img.shields.io/badge/status-beta-yellow.svg)](#)
[![Version](https://img.shields.io/badge/version-1.0.0b-blue.svg)](#)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Platforms](https://img.shields.io/badge/plataforma-Windows%20%7C%20Linux-lightgrey.svg)](#)
[![Interfaces](https://img.shields.io/badge/interfaces-CLI%20%7C%20Shell%20%7C%20TUI%20%7C%20GUI-8A2BE2.svg)](#)
[![Languages](https://img.shields.io/badge/i18n-EN%20%7C%20PT-brightgreen.svg)](#)

**CLIDOWNROM** is a cross-platform client that connects to the public CrocDB API to search and download ROMs with a high degree of relevance. It unifies CLI, interactive Shell, TUI, and GUI (with gamepad support) over the same search, filtering, and download services, displaying useful metadata and organizing transfers quickly, safely, and in an automatable way — ideal for enthusiasts, collectors, and integrators.

## 🎯 Key Features

- **4 Different Interfaces**: CLI, Interactive Shell, TUI, and GUI navigable by joystick
- **Smart Download**: Multiple connections, automatic retry, and integrity verification
- **Advanced Search**: Relevance algorithm with filters by platform, region, and year
- **Internationalization**: Full support for multiple languages
- **Smart Cache**: Local caching system to optimize performance
- **Detailed Logs**: Full logging system for debugging and auditing

## 🖥️ Available Interfaces

### 1. CLI (Command Line Interface)
Non-interactive interface ideal for scripts and automation:
```bash
clidownrom search "Super Mario" --platform snes --region USA
clidownrom download --id 12345 --output ./roms/
clidownrom random --platform nes --count 5
```

### 2. Interactive Shell
Advanced REPL with command history and autocomplete:
```bash
clidownrom --interface shell
> search "Zelda" --platform snes
> download 1
> history
```

### 3. TUI (Text User Interface)
Full-screen interface navigable by keyboard, inspired by htop:
```bash
clidownrom --interface tui
```

### 4. GUI (Graphical User Interface)
Graphical interface navigable by joystick/gamepad for TV usage:
```bash
clidownrom --interface gui
```

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10+ or Linux (Ubuntu 18.04+)

### Install via Git
```bash
git clone https://github.com/Oraculo-sh/CLIDOWNROM.git
cd CLIDOWNROM
pip install -r requirements.txt
```

### Standalone Executable
Download the precompiled executable from the [releases page](https://github.com/Oraculo-sh/CLIDOWNROM/releases).

## 🚀 Quick Start

### Search ROMs
```bash
# Busca básica
python main.py search "Super Mario Bros"

# Busca com filtros
python main.py search "Zelda" --platform snes --region USA --year 1991

# ROMs aleatórias
python main.py random --platform nes --count 10
```

### Download ROMs
```bash
# Download por ID
python main.py download --id 12345

# Download de resultados de busca
python main.py search "Metroid" --download

# Download com configurações específicas
python main.py download --id 12345 --no-boxart --output ./custom/
```

### ROM Information
```bash
# Visualizar detalhes
python main.py info --id 12345

# Formato JSON para scripts
python main.py info --id 12345 --format json
```

### Configuration
```bash
# Listar configurações
python main.py config --list

# Alterar configuração
python main.py config --set download.max_concurrent 5

# Resetar para padrões
python main.py config --reset
```

## ⚙️ Configuration

The `user_config.yml` file allows you to customize the application's behavior:

```yaml
api:
  base_url: "https://api.crocdb.net"
  timeout: 30
  max_retries: 3

download:
  max_concurrent: 3
  timeout: 30
  download_boxart: true
  verify_integrity: true

app:
  language: "en"  # ou "pt"
  
logging:
  level: "INFO"
  console_output: true
  file_output: true
```

## 🎮 Gamepad Controls (GUI)

| Button | Action |
|-------|------|
| A | Select/Confirm |
| B | Back/Cancel |
| X | Download |
| Y | Information |
| D-Pad | Navigate |
| Analog | Navigate (alternative) |

## 📁 Directory Structure

```
CLIDOWNLOAD/
├── ROMS/
│   ├── [platform]/
│   │   ├── *.rom
│   │   └── boxart/
│   │       └── *.jpg
├── temp/
│   ├── downloads/
│   ├── cache/
│   └── teste/
├── logs/
│   ├── lastlog.txt
│   └── session-*.log
└── config/
    └── config.yml
```

## 🌍 Currently Supported Languages

- English (en_us) - Default
- Portuguese (pt_br) - Brazilian
- Russian (ru) - Русский

To add new languages, create a YAML file in `src/locales/` using `en_us.yml` as a reference.
The system automatically detects and loads new language files when they are placed in the `src/locales/` directory, as long as the filename follows the standard locale code format (e.g., `fr_fr.yml`, `es_es.yml`, `de_de.yml`).

## 🔧 Development

### Environment Setup
```bash
git clone https://github.com/Oraculo-sh/CLIDOWNROM.git
cd CLIDOWNROM
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Run Tests
```bash
python -m pytest tests/
```

### Build Executable
```bash
pyinstaller --onefile --name clidownrom main.py
```

## 📊 Advanced Features

### Caching System
- Automatic caching of platform and region lists
- Configurable expiration time
- Automatic cleanup of old cache

### Smart Download
- Automatic mirror speed testing
- Download with multiple connections
- Hash-based integrity verification
- Automatic retry on failure

### Full Logging
- `lastlog.txt`: Full output of the last execution
- `session-*.log`: Detailed logs with timestamp
- Automatic rotation of old logs

## 🤝 Contributing

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow the existing code style
- Add tests for new functionality
- Update documentation when necessary
- Use descriptive commits

## 📝 Changelog

### v1.0.0 (In Development)
- ✅ Full CLI interface
- ✅ Interactive Shell interface
- ✅ TUI interface with Textual
- ✅ GUI interface with gamepad support
- ✅ Download system with multiple connections
- ✅ Smart cache
- ✅ Internationalization (EN/PT)
- ✅ Full logging system
- ✅ Configuration via YAML file

## 🐛 Known Issues

- Gamepad may not work on some Linux distributions without additional configuration
- TUI may have rendering issues in very old terminals
- Very fast downloads may overload some mirrors

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [CrocDB](https://crocdb.net/) for the ROMs API
- Python community for excellent libraries
- Contributors and testers

---

<p align="center">
  <strong>CLI Download ROM</strong> - Download your favorite ROMs in style! 🎮
</p>