#!/bin/bash
# Script de instalação para TV Box ARM

echo "Instalando Lewis AI em TV Box..."

# Atualiza sistema
sudo apt-get update
sudo apt-get upgrade -y

# Dependências básicas
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    espeak \
    git \
    libatlas-base-dev  # Para numpy em ARM

# Clona repositório (se aplicável)
git clone https://github.com/srreparos7z-rgb/lewisia
cd lewisia

# Instala dependências Python
pip3 install -r requirements.txt

# Configura serviço systemd
sudo cat > /etc/systemd/system/lewis.service << EOF
[Unit]
Description=Lewis AI Assistant
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilita e inicia serviço
sudo systemctl daemon-reload
sudo systemctl enable lewis.service
sudo systemctl start lewis.service

echo "Instalação completa!"
echo "Lewis está rodando como serviço."
echo "Comandos:"
echo "  sudo systemctl status lewis"
echo "  sudo journalctl -u lewis -f"
