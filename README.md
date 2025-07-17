# CLIDOWNROM

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](http://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[Leia isto em Português / Read this in Portuguese](README.pt_br.md)

---

A powerful and autonomous command-line tool (CLI) to search and download game ROMs using the CrocDB database.

## ✨ Features

* **Hybrid Interface:** Works as a standard CLI for automation and also as a user-friendly Interactive Shell for guided use.
* **Self-Installation:** Automatically manages its own dependencies (Python and Git) on the first run.
* **Automatic Updates:** Checks and updates the CrocDB database to keep ROM information current.
* **Multiple Sources:** Searches for ROMs via the online CrocDB API as well as a local database for faster batch operations.
* **Intelligent Mirror Testing:** Tests the download speed of mirrors and prioritizes the fastest one to optimize download speed.
* **Robust Download Manager:** Includes progress bars, automatic retries, file size validation, and automatic organization into platform folders.
* **Detailed Logging:** Records all operations, successes, errors, and crashes in log files for easy debugging.
* **Multi-Language Support:** The interface adapts to the system language (initial support for en_us and pt_br).

## 🚀 Installation and First Run

The tool is designed to be as simple as possible to install and use.

**Prerequisites:**

* Python 3.8+ ([https://www.python.org/downloads/](https://www.python.org/downloads/))
* Git ([https://git-scm.com/downloads/](https://git-scm.com/downloads/))

With the prerequisites installed, follow these steps:

1.  **Get the project:**
    ```bash
    git clone [https://github.com/Oraculo-adm/CLIDOWNROM.git](https://github.com/Oraculo-adm/CLIDOWNROM.git)
    cd CLIDOWNROM
    ```
2.  **Run the Launcher:**
    Simply run the launcher script corresponding to your operating system.

    * **On Windows:**
        ```bash
        start.bat
        ```
        (You can also double-click the `start.bat` file)
    * **On Linux or macOS:**
        ```bash
        chmod +x start.sh  # Give execute permission (only needed the first time)
        ./start.sh
        ```

The first time you run it, the script will automatically create a virtual environment, install Python dependencies, and download the necessary CrocDB databases. Subsequent runs will start the application instantly.

## ⚙️ Configuration

The tool's behavior can be adjusted through two main files in the `Cli-Download-Rom/` folder:

* **`config.yml`**: The main configuration file. Here you can enable/disable mirror testing, set the number of download retries, change default directories, and more.
* **`.env`**: Used for credentials. Copy the `.env.example` file to `.env` and add your Internet Archive username and password if you need to download restricted files.

## USAGE

The tool can be used in two ways:

### Interactive Shell Mode (Guided Use)

Run the launcher without arguments (`start.bat` or `./start.sh`) to enter the interactive mode.

Welcome to the Interactive Shell. Type 'help' for a list of commands or 'exit' to quit.
Downloader> search "Super Mario World"
Downloader> download-list list/my_favorites.json
Downloader> exit

### Standard CLI Mode (Automation and Scripts)

Pass commands directly to the launcher. The tool will execute the task and exit.

* **Search for a ROM using the API:**
    ```bash
    start.bat search "Sonic The Hedgehog 2"
    ```
* **Download a list of ROMs:**
    ```bash
    start.bat download-list list/snes_collection.json
    ```

## 🙏 Acknowledgements and Dependencies

This tool fundamentally relies on the excellent work of the **CrocDB** team. The following projects are used as dependencies:

* **crocdb-db** ([https://github.com/cavv-dev/crocdb-db](https://github.com/cavv-dev/crocdb-db)) (GNU General Public License v3.0)
* **crocdb-api** ([https://github.com/cavv-dev/crocdb-api](https://github.com/cavv-dev/crocdb-api)) (GNU General Public License v3.0)

We thank them for providing such a valuable resource to the game preservation community.

## ⚖️ License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. See the [LICENSE.md](LICENSE.md) file for more details.
