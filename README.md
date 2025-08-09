# CLI Download ROM

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/Oraculo-sh/CLIDOWNROM)

Um cliente avançado multiplataforma para a API CrocDB de ROMs de jogos, oferecendo múltiplas interfaces de usuário para diferentes casos de uso.

## 🎯 Características Principais

- **4 Interfaces Diferentes**: CLI, Shell Interativo, TUI e GUI navegável por joystick
- **Download Inteligente**: Múltiplas conexões, retry automático e verificação de integridade
- **Busca Avançada**: Algoritmo de relevância com filtros por plataforma, região e ano
- **Internacionalização**: Suporte completo para múltiplos idiomas
- **Cache Inteligente**: Sistema de cache local para otimizar performance
- **Logs Detalhados**: Sistema completo de logging para debugging e auditoria

## 🖥️ Interfaces Disponíveis

### 1. CLI (Command Line Interface)
Interface não-interativa ideal para scripts e automação:
```bash
clidownrom search "Super Mario" --platform snes --region USA
clidownrom download --id 12345 --output ./roms/
clidownrom random --platform nes --count 5
```

### 2. Shell Interativo
REPL avançado com histórico de comandos e autocompletar:
```bash
clidownrom --interface shell
> search "Zelda" --platform snes
> download 1
> history
```

### 3. TUI (Text User Interface)
Interface de tela completa navegável por teclado, inspirada no htop:
```bash
clidownrom --interface tui
```

### 4. GUI (Graphical User Interface)
Interface gráfica navegável por joystick/gamepad para uso em TV:
```bash
clidownrom --interface gui
```

## 📦 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Windows 10+ ou Linux (Ubuntu 18.04+)

### Instalação via Git
```bash
git clone https://github.com/Oraculo-sh/CLIDOWNROM.git
cd CLIDOWNROM
pip install -r requirements.txt
```

### Executável Standalone
Baixe o executável pré-compilado da [página de releases](https://github.com/Oraculo-sh/CLIDOWNROM/releases).

## 🚀 Uso Rápido

### Buscar ROMs
```bash
# Busca básica
python main.py search "Super Mario Bros"

# Busca com filtros
python main.py search "Zelda" --platform snes --region USA --year 1991

# ROMs aleatórias
python main.py random --platform nes --count 10
```

### Download de ROMs
```bash
# Download por ID
python main.py download --id 12345

# Download de resultados de busca
python main.py search "Metroid" --download

# Download com configurações específicas
python main.py download --id 12345 --no-boxart --output ./custom/
```

### Informações de ROM
```bash
# Visualizar detalhes
python main.py info --id 12345

# Formato JSON para scripts
python main.py info --id 12345 --format json
```

### Configuração
```bash
# Listar configurações
python main.py config --list

# Alterar configuração
python main.py config --set download.max_concurrent 5

# Resetar para padrões
python main.py config --reset
```

## ⚙️ Configuração

O arquivo `user_config.yml` permite personalizar o comportamento da aplicação:

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

## 🎮 Controles do Gamepad (GUI)

| Botão | Ação |
|-------|------|
| A | Selecionar/Confirmar |
| B | Voltar/Cancelar |
| X | Download |
| Y | Informações |
| D-Pad | Navegar |
| Analógico | Navegar (alternativo) |

## 📁 Estrutura de Diretórios

```
CLIDOWNLOAD/
├── ROMS/
│   ├── [platform]/
│   │   ├── *.rom
│   │   └── boxart/
│   │       └── *.jpg
├── TEMP/
│   ├── downloads/
│   └── teste/
├── logs/
│   ├── lastlog.txt
│   └── session-*.log
├── cache/
└── config/
    └── user_config.yml
```

## 🌍 Idiomas Suportados

- **Inglês** (en) - Padrão
- **Português** (pt) - Brasileiro

Para adicionar novos idiomas, crie um arquivo JSON em `src/locales/` seguindo o padrão dos existentes.

## 🔧 Desenvolvimento

### Configuração do Ambiente
```bash
git clone https://github.com/Oraculo-sh/CLIDOWNROM.git
cd CLIDOWNROM
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Executar Testes
```bash
python -m pytest tests/
```

### Compilar Executável
```bash
pyinstaller --onefile --name clidownrom main.py
```

## 📊 Funcionalidades Avançadas

### Sistema de Cache
- Cache automático de listas de plataformas e regiões
- Tempo de expiração configurável
- Limpeza automática de cache antigo

### Download Inteligente
- Teste automático de velocidade dos mirrors
- Download com múltiplas conexões
- Verificação de integridade por hash
- Retry automático em caso de falha

### Logging Completo
- `lastlog.txt`: Output completo da última execução
- `session-*.log`: Logs detalhados com timestamp
- Rotação automática de logs antigos

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes de Contribuição
- Siga o padrão de código existente
- Adicione testes para novas funcionalidades
- Atualize a documentação quando necessário
- Use commits descritivos

## 📝 Changelog

### v1.0.0 (Em Desenvolvimento)
- ✅ Interface CLI completa
- ✅ Interface Shell interativa
- ✅ Interface TUI com Textual
- ✅ Interface GUI com suporte a gamepad
- ✅ Sistema de download com múltiplas conexões
- ✅ Cache inteligente
- ✅ Internacionalização (EN/PT)
- ✅ Sistema completo de logging
- ✅ Configuração via arquivo YAML

## 🐛 Problemas Conhecidos

- Gamepad pode não funcionar em algumas distribuições Linux sem configuração adicional
- TUI pode ter problemas de renderização em terminais muito antigos
- Download muito rápido pode sobrecarregar alguns mirrors

## 📄 Licença

Este projeto está licenciado sob a GPL-3.0 License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**Leonne Martins** ([@Oraculo-sh](https://github.com/Oraculo-sh))

## 🙏 Agradecimentos

- [CrocDB](https://crocdb.net/) pela API de ROMs
- Comunidade Python pelas excelentes bibliotecas
- Contribuidores e testadores

## 📞 Suporte

- 🐛 [Issues](https://github.com/Oraculo-sh/CLIDOWNROM/issues)
- 💬 [Discussions](https://github.com/Oraculo-sh/CLIDOWNROM/discussions)
- 📧 Email: [seu-email@exemplo.com]

---

<p align="center">
  <strong>CLI Download ROM</strong> - Baixe suas ROMs favoritas com estilo! 🎮
</p>