"""
Interface de Hardware - Áudio e periféricos
Otimizado para Linux Embarcado/ARM com foco em comando por voz
"""

import asyncio
import numpy as np
import struct
import threading
from collections import deque
from typing import Optional, Callable
import logging

logger = logging.getLogger("Lewis.Hardware")

class AudioInterface:
    """Interface de áudio com wake-word detection e buffer contínuo"""
    
    def __init__(self, config: dict):
        self.config = config
        self.audio_interface = None
        self.stream = None
        self.is_listening = False
        self.callback = None
        
        # Configurações otimizadas para voz
        self.SAMPLE_RATE = config.get('audio_sample_rate', 16000)
        self.CHUNK_SIZE = config.get('audio_chunk_size', 1024)
        self.FORMAT = 'int16'
        self.CHANNELS = 1
        
        # Buffer circular para análise de áudio
        self.audio_buffer = deque(maxlen=10)  # 10 chunks de buffer
        self.wake_word_buffer = deque(maxlen=20)  # Buffer para detecção de wake word
        
        # Wake word personalizada "Lewis"
        self.WAKE_WORD = "lewis"
        self.wake_word_detected = False
        self.command_in_progress = False
        
        # Configurações de VAD (Voice Activity Detection)
        self.energy_threshold = 500
        self.silence_duration = 1.0  # segundos de silêncio para fim de comando
        self.silence_counter = 0
        
    async def initialize(self):
        """Inicialização assíncrona do hardware de áudio"""
        logger.info("Inicializando interface de áudio para comando por voz...")
        
        try:
            # Tenta múltiplos backends de áudio
            backends = ['pyaudio', 'sounddevice', 'alsa']
            
            for backend in backends:
                try:
                    if backend == 'pyaudio':
                        import pyaudio
                        self.audio_interface = pyaudio.PyAudio()
                        self.using_pyaudio = True
                        logger.info(f"Backend {backend} inicializado com sucesso")
                        break
                        
                    elif backend == 'sounddevice':
                        import sounddevice as sd
                        self.audio_interface = sd
                        self.using_pyaudio = False
                        logger.info(f"Backend {backend} inicializado com sucesso")
                        break
                        
                    elif backend == 'alsa':
                        # Configuração direta ALSA para maior eficiência
                        import alsaaudio
                        self.audio_interface = alsaaudio
                        self.using_alsa = True
                        logger.info(f"Backend {backend} inicializado com sucesso")
                        break
                        
                except ImportError as e:
                    logger.debug(f"Backend {backend} não disponível: {e}")
                    continue
                    
            if not self.audio_interface:
                logger.warning("Nenhum backend de áudio disponível, usando modo simulador")
                self.simulator_mode = True
            else:
                self.simulator_mode = False
                
            # Inicia thread de captura contínua
            self.capture_thread = threading.Thread(target=self._continuous_capture, daemon=True)
            self.capture_thread.start()
            
            logger.info("Interface de áudio inicializada para captura contínua")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar áudio: {e}")
            self.simulator_mode = True
    
    def _continuous_capture(self):
        """Captura de áudio contínua em thread separada"""
        if self.simulator_mode:
            logger.info("Modo simulador ativado (sem hardware de áudio)")
            return
            
        try:
            if hasattr(self, 'using_pyaudio') and self.using_pyaudio:
                self._setup_pyaudio_stream()
            elif hasattr(self, 'using_alsa') and self.using_alsa:
                self._setup_alsa_stream()
            else:
                self._setup_sounddevice_stream()
                
        except Exception as e:
            logger.error(f"Erro na captura contínua: {e}")
    
    def _setup_pyaudio_stream(self):
        """Configura stream contínuo PyAudio"""
        import pyaudio
        
        self.stream = self.audio_interface.open(
            format=pyaudio.paInt16,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK_SIZE,
            stream_callback=self._audio_callback,
            input_device_index=self._find_input_device()
        )
        
        self.stream.start_stream()
        
        # Mantém o stream ativo
        while self.stream.is_active():
            import time
            time.sleep(0.1)
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback para processamento de áudio em tempo real"""
        if status:
            logger.warning(f"Status do áudio: {status}")
        
        # Adiciona ao buffer para análise
        self.audio_buffer.append(in_data)
        
        # Análise em tempo real para wake word
        if not self.command_in_progress:
            self._analyze_for_wake_word(in_data)
        
        # Se wake word detectada, começa a capturar comando
        if self.wake_word_detected and not self.command_in_progress:
            self.command_in_progress = True
            self.command_audio = bytearray()
            self.wake_word_detected = False
            logger.info("Wake word detectada, iniciando captura de comando...")
        
        # Captura áudio do comando
        if self.command_in_progress:
            self.command_audio.extend(in_data)
            
            # Detecta silêncio para fim de comando
            if self._is_silence(in_data):
                self.silence_counter += len(in_data) / (self.SAMPLE_RATE * 2)
                if self.silence_counter >= self.silence_duration:
                    self._process_complete_command()
            else:
                self.silence_counter = 0
        
        return (in_data, pyaudio.paContinue)
    
    def _analyze_for_wake_word(self, audio_data: bytes):
        """Análise simples de wake word (implementação leve)"""
        # Converte para array numpy para análise
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # 1. Verifica energia (filtra silêncio)
        energy = np.mean(np.abs(audio_array))
        if energy < self.energy_threshold:
            return False
        
        # 2. Análise espectral simples (implementação simplificada)
        # Em produção, usar modelo treinado como Snowboy ou Porcupine
        fft = np.fft.rfft(audio_array)
        frequencies = np.fft.rfftfreq(len(audio_array), 1/self.SAMPLE_RATE)
        
        # Procura padrões de voz humana (300-3400 Hz)
        voice_band = (frequencies > 300) & (frequencies < 3400)
        voice_energy = np.mean(np.abs(fft[voice_band]))
        
        if voice_energy > 1000:  # Threshold ajustável
            # Wake word detectada (simplificado)
            self.wake_word_detected = True
            return True
        
        return False
    
    def _is_silence(self, audio_data: bytes, threshold: int = 200) -> bool:
        """Detecta silêncio no chunk de áudio"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        energy = np.mean(np.abs(audio_array))
        return energy < threshold
    
    def _process_complete_command(self):
        """Processa comando completo quando detectado fim de fala"""
        if hasattr(self, 'command_audio') and len(self.command_audio) > 0:
            logger.info(f"Comando de voz capturado: {len(self.command_audio)} bytes")
            
            # Envia para processamento em thread separada
            threading.Thread(
                target=self._process_command_async,
                args=(bytes(self.command_audio),),
                daemon=True
            ).start()
        
        # Reseta estado
        self.command_in_progress = False
        self.silence_counter = 0
        if hasattr(self, 'command_audio'):
            del self.command_audio
    
    def _process_command_async(self, audio_data: bytes):
        """Processa comando de forma assíncrona"""
        try:
            # Converte áudio para texto
            text = asyncio.run(self.speech_to_text(audio_data))
            
            if text and text.strip():
                logger.info(f"Comando reconhecido: {text}")
                
                # Aqui você integraria com o módulo principal
                # Por exemplo: self.callback(text) se um callback estiver configurado
                
        except Exception as e:
            logger.error(f"Erro ao processar comando: {e}")
    
    def _find_input_device(self) -> int:
        """Encontra o dispositivo de entrada de áudio padrão"""
        if hasattr(self, 'using_pyaudio') and self.using_pyaudio:
            import pyaudio
            
            p = pyaudio.PyAudio()
            info = p.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            
            for i in range(numdevices):
                device_info = p.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels') > 0:
                    logger.info(f"Dispositivo de entrada: {device_info.get('name')}")
                    return i
            
            return 0  # Dispositivo padrão
    
    async def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """Converte áudio em texto usando engine offline leve"""
        try:
            # Opção 1: Vosk (offline, suporta ARM)
            try:
                import vosk
                
                if not hasattr(self, 'vosk_model'):
                    # Baixa modelo pequeno se não existir
                    model_path = self._ensure_vosk_model()
                    self.vosk_model = vosk.Model(model_path)
                    self.vosk_recognizer = vosk.KaldiRecognizer(
                        self.vosk_model, 
                        self.SAMPLE_RATE
                    )
                
                if self.vosk_recognizer.AcceptWaveform(audio_data):
                    result = self.vosk_recognizer.Result()
                    import json
                    text = json.loads(result).get('text', '')
                    return text if text else None
                    
            except ImportError:
                logger.warning("Vosk não disponível")
                
            # Opção 2: Whisper tiny (mais pesado mas mais preciso)
            try:
                import whisper
                
                if not hasattr(self, 'whisper_model'):
                    # Carrega modelo tiny (mais leve)
                    self.whisper_model = whisper.load_model("tiny")
                
                # Salva áudio temporariamente
                import tempfile
                import wave
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    with wave.open(f.name, 'wb') as wf:
                        wf.setnchannels(self.CHANNELS)
                        wf.setsampwidth(2)  # 16-bit
                        wf.setframerate(self.SAMPLE_RATE)
                        wf.writeframes(audio_data)
                    
                    # Transcreve
                    result = self.whisper_model.transcribe(f.name, language='pt')
                    return result['text']
                    
            except ImportError:
                logger.warning("Whisper não disponível")
                
            # Opção 3: PocketSphinx (muito leve)
            try:
                from pocketsphinx import LiveSpeech, get_model_path
                
                # Salva áudio para arquivo temporário
                import tempfile
                import wave
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    with wave.open(f.name, 'wb') as wf:
                        wf.setnchannels(self.CHANNELS)
                        wf.setsampwidth(2)
                        wf.setframerate(self.SAMPLE_RATE)
                        wf.writeframes(audio_data)
                    
                    # Configura decoder
                    config = {
                        'verbose': False,
                        'audio_file': f.name,
                        'buffer_size': 2048,
                        'no_search': False,
                        'full_utt': False,
                        'hmm': get_model_path('pt-br'),
                        'lm': get_model_path('pt-br.lm.bin'),
                        'dic': get_model_path('pt-br.dic')
                    }
                    
                    speech = LiveSpeech(**config)
                    for phrase in speech:
                        return str(phrase)
                        
            except ImportError:
                logger.warning("PocketSphinx não disponível")
                
        except Exception as e:
            logger.error(f"Erro STT: {e}")
        
        return None
    
    def _ensure_vosk_model(self) -> str:
        """Garante que o modelo Vosk está disponível"""
        import os
        import requests
        import tarfile
        
        model_dir = "/tmp/vosk-model-small-pt"
        model_url = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
        
        if not os.path.exists(model_dir):
            logger.info("Baixando modelo Vosk...")
            
            # Cria diretório
            os.makedirs(model_dir, exist_ok=True)
            
            # Baixa e extrai (simplificado)
            # Em produção, implementar download com progresso
            
        return model_dir
    
    async def text_to_speech(self, text: str, voice: str = 'pt'):
        """Síntese de fala com múltiplos backends"""
        try:
            # Prioridade: eSpeak NG (mais leve)
            try:
                import subprocess
                
                # Usa eSpeak com voz em português
                if voice == 'pt':
                    voice_param = 'pt-br'
                else:
                    voice_param = 'en'
                
                process = subprocess.Popen(
                    ['espeak-ng', '-v', voice_param, text],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                process.communicate()
                return
                
            except (ImportError, FileNotFoundError):
                pass
            
            # Opção 2: pyttsx3 (offline)
            try:
                import pyttsx3
                
                if not hasattr(self, 'tts_engine'):
                    self.tts_engine = pyttsx3.init()
                    
                    # Configurações para melhor qualidade
                    self.tts_engine.setProperty('rate', 150)
                    self.tts_engine.setProperty('volume', 1.0)
                    
                    # Tenta definir voz em português
                    voices = self.tts_engine.getProperty('voices')
                    for v in voices:
                        if 'portuguese' in v.name.lower() or 'brazil' in v.name.lower():
                            self.tts_engine.setProperty('voice', v.id)
                            break
                
                # Executa em thread separada
                def speak():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                
                threading.Thread(target=speak, daemon=True).start()
                
            except ImportError:
                pass
            
            # Opção 3: Festival TTS (se instalado)
            try:
                import subprocess
                subprocess.run(['festival', '--tts'], input=text.encode())
            except:
                pass
            
            # Fallback: apenas log
            logger.info(f"Lewis diria: {text}")
            
        except Exception as e:
            logger.error(f"Erro TTS: {e}")
    
    def set_command_callback(self, callback: Callable[[str], None]):
        """Define callback para quando um comando é reconhecido"""
        self.callback = callback
    
    def cleanup(self):
        """Limpeza de recursos"""
        self.is_listening = False
        
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if hasattr(self, 'audio_interface') and hasattr(self, 'using_pyaudio'):
            self.audio_interface.terminate()