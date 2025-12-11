#!/usr/bin/env python3
"""
Módulo Principal - Lewis AI
Controle total por voz como Alexa/Jarvis
"""

import asyncio
import signal
import sys
import logging
from typing import Optional

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/lewis_voice.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LewisVoice")

class LewisVoiceAssistant:
    """Assistente por voz completo"""
    
    def __init__(self):
        self.running = True
        self.modules = {}
        
        # Configuração otimizada para TV Box
        self.config = {
            'wake_word': 'lewis',
            'audio_sample_rate': 16000,
            'audio_chunk_size': 1024,
            'vad_threshold': 300,
            'silence_duration': 1.5,
            'max_response_time': 10,
            'voice_gender': 'male',
            'voice_speed': 150
        }
        
        # Estado do assistente
        self.assistant_state = {
            'is_listening': False,
            'last_command': None,
            'conversation_mode': False,
            'volume_level': 70
        }
        
    async def initialize(self):
        """Inicializa todos os módulos"""
        logger.info("Inicializando Lewis - Modo Voz Total")
        
        # 1. Hardware de áudio
        from hardware_interface import AudioInterface
        self.modules['hardware'] = AudioInterface(self.config)
        await self.modules['hardware'].initialize()
        
        # 2. Núcleo de IA
        from core_ai import AICore
        self.modules['ai'] = AICore(self.config)
        await self.modules['ai'].initialize()
        
        # 3. Utilitários
        from assistente_utils import Utilitarios
        self.modules['utils'] = Utilitarios(self.config)
        
        # 4. Processador de comandos de voz
        from voice_command_processor import VoiceCommandProcessor
        self.modules['voice'] = VoiceCommandProcessor(
            self.modules['ai'],
            self.modules['hardware'],
            self.modules['utils']
        )
        
        # Configura callback para comandos reconhecidos
        self.modules['hardware'].set_command_callback(self._on_voice_command)
        
        # Sinal sonoro de inicialização
        await self._play_startup_sound()
        
        logger.info("Lewis pronto para comandos de voz. Diga 'Lewis' para ativar.")
    
    async def _play_startup_sound(self):
        """Toca som de inicialização"""
        try:
            # Toca um beep simples
            import subprocess
            subprocess.run(['beep', '-f', '800', '-l', '100'])
            await asyncio.sleep(0.1)
            subprocess.run(['beep', '-f', '1200', '-l', '100'])
        except:
            logger.info("🔊 Lewis iniciado")
    
    def _on_voice_command(self, command_text: str):
        """Callback chamado quando um comando é reconhecido"""
        asyncio.create_task(self._process_command_async(command_text))
    
    async def _process_command_async(self, command_text: str):
        """Processa comando de forma assíncrona"""
        try:
            logger.info(f"Comando recebido: {command_text}")
            
            # Toca som de confirmação
            await self._play_ack_sound()
            
            # Processa comando
            result = await self.modules['voice'].process_voice_command(command_text)
            
            # Executa ação se necessário
            if result.get('action_needed', False):
                await self.modules['utils'].execute_action(result)
            
            # Resposta por voz
            if 'voice_response' in result:
                await self.modules['hardware'].text_to_speech(
                    result['voice_response'],
                    voice='pt'
                )
            
            # Atualiza estado
            self.assistant_state['last_command'] = command_text
            
        except Exception as e:
            logger.error(f"Erro processando comando: {e}")
            await self.modules['hardware'].text_to_speech(
                "Desculpe, ocorreu um erro ao processar seu comando.",
                voice='pt'
            )
    
    async def _play_ack_sound(self):
        """Toca som de confirmação"""
        try:
            import subprocess
            subprocess.run(['beep', '-f', '1000', '-l', '50'])
        except:
            pass
    
    async def run(self):
        """Loop principal do assistente por voz"""
        logger.info("Lewis em execução - Aguardando comandos de voz")
        
        # Mantém o programa rodando
        while self.running:
            try:
                # Verifica estado periódicamente
                await self._check_system_status()
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Interrupção recebida")
                break
            except Exception as e:
                logger.error(f"Erro no loop principal: {e}")
                await asyncio.sleep(5)
    
    async def _check_system_status(self):
        """Verifica status do sistema periodicamente"""
        # Implemente verificações de saúde do sistema aqui
        pass
    
    async def shutdown(self):
        """Desligamento controlado"""
        logger.info("Encerrando Lewis...")
        self.running = False
        
        # Toca som de desligamento
        try:
            import subprocess
            subprocess.run(['beep', '-f', '1200', '-l', '100'])
            await asyncio.sleep(0.1)
            subprocess.run(['beep', '-f', '800', '-l', '100'])
        except:
            pass
        
        # Limpeza
        if 'hardware' in self.modules:
            self.modules['hardware'].cleanup()
        
        logger.info("Lewis encerrado com sucesso")

def main():
    """Função principal"""
    assistant = LewisVoiceAssistant()
    
    # Configura handlers de sinal
    def signal_handler(signum, frame):
        asyncio.create_task(assistant.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Inicializa e executa
        loop = asyncio.get_event_loop()
        loop.run_until_complete(assistant.initialize())
        loop.run_until_complete(assistant.run())
    except KeyboardInterrupt:
        loop.run_until_complete(assistant.shutdown())
    finally:
        logger.info("Programa terminado")

if __name__ == "__main__":
    # Otimiza para ARM
    try:
        import uvloop
        uvloop.install()
        logger.info("uvloop ativado para melhor performance")
    except ImportError:
        logger.info("uvloop não disponível, usando asyncio padrão")
    
    main()