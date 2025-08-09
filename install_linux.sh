
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
    echo "export PATH="$INSTALL_DIR:\$PATH"" >> ~/.bashrc
    echo "export PATH="$INSTALL_DIR:\$PATH"" >> ~/.zshrc 2>/dev/null || true
fi

echo
echo "✅ Instalação concluída!"
echo "Reinicie o terminal ou execute: source ~/.bashrc"
echo "Depois use o comando 'clidownrom'"
echo
