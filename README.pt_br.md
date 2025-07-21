# CLIDOWNROM

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](http://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[Read this in English / Leia isto em Inglês](README.md)

---

Uma ferramenta de linha de comando (CLI) poderosa e autônoma para pesquisar e baixar ROMs de jogos usando a API do banco de dados CrocDB.

## ✨ Funcionalidades

* **Interface Híbrida:** Funciona como um CLI padrão para automação e também como um Shell Interativo amigável para uso guiado.
* **Totalmente Autônoma:** Gere as suas próprias dependências, incluindo pacotes Python e o motor de download `aria2c`, automaticamente.
* **Downloads de Alta Velocidade:** Usa o `aria2c` para baixar ficheiros com múltiplas conexões para velocidade máxima.
* **Busca Inteligente:** Coleta resultados de múltiplas páginas e usa um poderoso ranking de relevância local para mostrar os melhores resultados primeiro. Suporta filtros por plataforma, região, slug e ROM ID.
* **Experiência de Usuário Polida:** Possui ajuda detalhada, autocompletar com `Tab`, menus interativos, destinos de download flexíveis e mais.

## 🚀 Instalação e Primeira Execução

**Pré-requisitos:**
* Python 3.8+ ([https://www.python.org/downloads/](https://www.python.org/downloads/))
* Git ([https://git-scm.com/downloads/](https://git-scm.com/downloads/))

1.  **Obtenha o projeto:**
    ```bash
    git clone [https://github.com/Oraculo-adm/CLIDOWNROM.git](https://github.com/Oraculo-adm/CLIDOWNROM.git)
    cd CLIDOWNROM
    ```
2.  **Execute o Lançador:**
    * **Windows:** `start.bat`
    * **Linux/macOS:** `chmod +x start.sh && ./start.sh`

Na primeira vez que você executar, o script irá configurar tudo o que precisa.

## USO

### Modo Shell Interativo
Execute `start.bat` ou `./start.sh` sem argumentos.
Downloader> search "Mario Kart 64" -p n64
Downloader> download --slug super-mario-64-n64-us --noaria2c
Downloader> download-list list/my_favorites.json


### Modo CLI Padrão
```bash
start.bat search "Zelda Ocarina of Time" --platform n64
start.bat download --rom_id NUS-NZLE-USA