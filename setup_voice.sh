#!/bin/bash
# Script de instalação para Lewis - Modo Voz Total

echo "🔊 Instalando Lewis AI com controle total por voz..."

# 1. Atualiza sistema
sudo apt-get update
sudo apt-get upgrade -y

# 2. Instala dependências do sistema
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    espeak-ng \
    festival \
    festival-pt \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    pulseaudio \
    beep \
    git \
    wget \
    curl \
    libatlas-base-dev \
    libblas-dev \
    liblapack-dev \
    libopenblas-dev

# 3. Instala modelo Vosk (reconhecimento offline)
echo "📥 Baixando modelo de voz Vosk (português)..."
mkdir -p /tmp/models
cd /tmp/models
wget https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip
unzip vosk-model-small-pt-0.3.zip
mv vosk-model-small-pt-0.3 /usr/share/vosk-model-pt
rm vosk-model-small-pt-0.3.zip

# 4. Clona ou copia o código
cd ~
if [ -d "lewis-ai-voice" ]; then
    echo "📁 Atualizando repositório existente..."
    cd lewis-ai-voice
    git pull
else
    echo "📁 Clonando repositório..."
    git clone https://github.com/seu-usuario/lewis-ai-voice.git
    cd lewis-ai-voice
fi

# 5. Instala dependências Python
echo "🐍 Instalando dependências Python..."
pip3 install -r requirements_voice.txt

# 6. Configura permissões de áudio
echo "🎵 Configurando permissões de áudio..."
sudo usermod -a -G audio $USER
sudo chmod 666 /dev/snd/*

# 7. Configura serviço systemd
echo "⚙️ Configurando serviço autoinicializável..."
sudo tee /etc/systemd/system/lewis-voice.service > /dev/null << EOF
[Unit]
Description=Lewis AI Voice Assistant
After=network.target sound.target
Requires=pulseaudio.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="DISPLAY=:0"
Environment="PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native"
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 8. Habilita e inicia serviço
sudo systemctl daemon-reload
sudo systemctl enable lewis-voice.service
sudo systemctl start lewis-voice.service

# 9. Configura atalhos de teclado (opcional)
echo "⌨️ Configurando atalhos de teclado..."
mkdir -p ~/.config/openbox
echo '<!-- Atalho para microfone (Ctrl+Alt+L) -->
<keybind key="C-A-L">
  <action name="Execute">
    <command>pactl set-source-mute @DEFAULT_SOURCE@ toggle</command>
  </action>
</keybind>' | sudo tee -a ~/.config/openbox/lxde-rc.xml

# 10. Reinicia Openbox
openbox --reconfigure

echo ""
echo "✅ Instalação completa!"
echo ""
echo "🎯 Lewis está rodando como serviço de voz"
echo ""
echo "Comandos úteis:"
echo "  sudo systemctl status lewis-voice    # Verifica status"
echo "  sudo journalctl -u lewis-voice -f    # Acompanha logs"
echo "  sudo systemctl restart lewis-voice   # Reinicia serviço"
echo ""
echo "🎤 Para usar:"
echo "  1. Diga 'Lewis' para ativar"
echo "  2. Aguarde o som de confirmação"
echo "  3. Fale seu comando"
echo "  4. Lewis responderá por voz"
echo ""
echo "🔧 Para testar o áudio:"
echo "  arecord --format=S16_LE --rate=16000 --file-type=raw | aplay"
echo ""