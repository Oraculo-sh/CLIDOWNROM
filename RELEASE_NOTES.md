# CLI Download ROM - Release Notes

## v1.0.0-beta (2025-01-09)

### 🎉 First Beta Release

Este é o primeiro release beta do CLI Download ROM, um cliente avançado para a API CrocDB com múltiplas interfaces.

### ✨ Funcionalidades Principais

- **Interface CLI**: Interface de linha de comando completa
- **Interface Shell**: Modo interativo com comandos
- **Interface TUI**: Interface de texto (quando textual disponível)
- **Interface GUI**: Interface gráfica (quando PyQt6 disponível)
- **Suporte a Múltiplas Plataformas**: Windows, Linux, macOS
- **Internacionalização**: Suporte a Português e Inglês

### 🔧 Correções Implementadas

- ✅ Corrigidos erros de importação para dependências opcionais
- ✅ Implementadas classes dummy robustas para textual, PyQt6 e pygame
- ✅ Tratamento adequado de erros de versão
- ✅ Executável standalone funcional (55MB)
- ✅ Todas as funcionalidades CLI operacionais sem dependências opcionais

### 📦 Arquivos de Release

- `clidownrom.exe` - Executável standalone para Windows (55MB)
- `install_windows.bat` - Script de instalação para Windows
- `install_linux.sh` - Script de instalação para Linux
- `clidownrom-windows-amd64/` - Pacote completo para Windows

### 🚀 Como Usar

```bash
# Verificar versão
clidownrom.exe --version

# Ver ajuda
clidownrom.exe --help

# Buscar ROMs
clidownrom.exe search "mario"

# Usar interface específica
clidownrom.exe --interface shell
```

### 📋 Requisitos

- **Mínimo**: Nenhuma dependência adicional (executável standalone)
- **Opcional**: textual (para TUI), PyQt6 (para GUI), pygame (para joystick)
- **Python**: 3.12+ (apenas para execução do código fonte)

### 🐛 Problemas Conhecidos

- Mensagens do pygame aparecem no console (não afeta funcionalidade)
- Interfaces TUI e GUI requerem instalação manual das dependências

### 🔗 Links

- **Repositório**: https://github.com/Oraculo-sh/CLIDOWNROM
- **Documentação**: README.md
- **Licença**: GPL-3.0

---

**Autor**: Leonne Martins (@Oraculo-sh)  
**Data**: 09 de Janeiro de 2025  
**Tag**: v1.0.0-beta