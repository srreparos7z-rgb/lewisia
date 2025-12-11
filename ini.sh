# Após instalação, teste rápido:
cd ~/lewis-ai-voice
python3 main.py

# Ou inicie como serviço:
sudo systemctl start lewis-voice
sudo journalctl -u lewis-voice -f