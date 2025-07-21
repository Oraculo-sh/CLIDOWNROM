# CLIDOWNROM

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](http://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[Leia isto em Português / Read this in Portuguese](README.pt_br.md)

---

A powerful and autonomous command-line tool (CLI) to search and download game ROMs using the CrocDB database API.

## ✨ Features

* **Hybrid Interface:** Works as a standard CLI for automation and also as a user-friendly Interactive Shell for guided use.
* **Fully Autonomous:** Manages its own dependencies, including Python packages and the `aria2c` download engine, automatically.
* **High-Speed Downloads:** Uses `aria2c` to download files with multiple connections for maximum speed.
* **Intelligent Search:** Fetches results from multiple pages and uses a powerful local relevance ranking to show you the best matches first. Supports filtering by platform, region, slug, and ROM ID.
* **Polished UX:** Features detailed help, tab completion for commands and arguments, interactive menus, flexible download destinations, and more.

## 🚀 Installation and First Run

**Prerequisites:**
* Python 3.8+ ([https://www.python.org/downloads/](https://www.python.org/downloads/))
* Git ([https://git-scm.com/downloads/](https://git-scm.com/downloads/))

1.  **Get the project:**
    ```bash
    git clone [https://github.com/Oraculo-adm/CLIDOWNROM.git](https://github.com/Oraculo-adm/CLIDOWNROM.git)
    cd CLIDOWNROM
    ```
2.  **Run the Launcher:**
    * **Windows:** `start.bat`
    * **Linux/macOS:** `chmod +x start.sh && ./start.sh`

The first time you run it, the script will set up everything you need.

## USAGE

### Interactive Shell Mode
Run `start.bat` or `./start.sh` with no arguments.
Downloader> search "Mario Kart 64" -p n64
Downloader> download --slug super-mario-64-n64-us --noaria2c
Downloader> download-list list/my_favorites.json

### Standard CLI Mode
```bash
start.bat search "Zelda Ocarina of Time" --platform n64
start.bat download --rom_id NUS-NZLE-USA