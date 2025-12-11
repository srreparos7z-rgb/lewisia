"""
Processador de Comandos de Voz - Gerencia o fluxo de comandos por voz
"""

import asyncio
import re
from typing import Dict, List, Callable, Any
import logging

logger = logging.getLogger("Lewis.Voice")

class VoiceCommandProcessor:
    """Processa e gerencia comandos de voz"""
    
    def __init__(self, ai_core, hardware_interface, utils):
        self.ai_core = ai_core
        self.hardware = hardware_interface
        self.utils = utils
        self.command_patterns = self._load_command_patterns()
        self.is_processing = False
        
    def _load_command_patterns(self) -> Dict[str, Dict]:
        """Padrões de comandos de voz"""
        return {
            'saudacao': {
                'patterns': ['olá', 'oi (lewis|leuis)', 'bom dia', 'boa tarde', 'boa noite'],
                'action': 'responder_saudacao'
            },
            'pergunta': {
                'patterns': ['o que é (.*)', 'como (funciona|fazer) (.*)', 'por que (.*)'],
                'action': 'responder_pergunta'
            },
            'controle': {
                'patterns': ['(liga|desliga) (.*)', '(abre|fecha) (.*)', '(mostra|esconde) (.*)'],
                'action': 'executar_controle'
            },
            'informacao': {
                'patterns': ['que horas são', 'que dia é hoje', 'qual a temperatura', 'previsão do tempo'],
                'action': 'fornecer_informacao'
            },
            'sistema': {
                'patterns': ['(reinicia|desliga) o sistema', 'modo (silencioso|noturno)', 'volume (alto|baixo|mudo)'],
                'action': 'controle_sistema'
            },
            'conversa': {
                'patterns': ['(conta|me diga) (.*)', 'o que você acha (.*)', '(você|vc) (.*)'],
                'action': 'conversar'
            }
        }
    
    async def process_voice_command(self, command_text: str) -> Dict[str, Any]:
        """Processa um comando de voz recebido"""
        if not command_text or not command_text.strip():
            return {'error': 'Comando vazio'}
        
        logger.info(f"Processando comando de voz: {command_text}")
        
        # Normaliza texto
        text = command_text.lower().strip()
        
        # Remove a wake word se presente
        text = re.sub(r'^(lewis|leuis)\s*', '', text)
        
        # Identifica tipo de comando
        command_type, matches = self._identify_command(text)
        
        if command_type:
            # Executa ação correspondente
            result = await self._execute_command(command_type, text, matches)
            return result
        else:
            # Comando não reconhecido, envia para IA geral
            return await self.ai_core.process_command(text)
    
    def _identify_command(self, text: str):
        """Identifica o tipo de comando baseado em padrões"""
        for cmd_type, cmd_info in self.command_patterns.items():
            for pattern in cmd_info['patterns']:
                # Converte padrão simples para regex
                regex_pattern = pattern.replace('(.*)', '(.+)')
                match = re.match(regex_pattern, text)
                if match:
                    return cmd_type, match.groups()
        
        return None, None
    
    async def _execute_command(self, cmd_type: str, text: str, matches: tuple):
        """Executa o comando específico"""
        actions = {
            'saudacao': self._handle_greeting,
            'pergunta': self._handle_question,
            'controle': self._handle_control,
            'informacao': self._handle_information,
            'sistema': self._handle_system,
            'conversa': self._handle_conversation
        }
        
        if cmd_type in actions:
            return await actions[cmd_type](text, matches)
        
        return {'response': f"Comando '{text}' recebido, mas ação não implementada"}
    
    async def _handle_greeting(self, text: str, matches: tuple):
        """Lida com saudações"""
        import random
        
        greetings = [
            "Olá! Como posso ajudar?",
            "Oi! Em que posso ser útil hoje?",
            "Saudações! Estou aqui para o que precisar.",
            "Olá! Pronto para assistir você."
        ]
        
        response = random.choice(greetings)
        return {
            'voice_response': response,
            'action_needed': False,
            'command_type': 'greeting'
        }
    
    async def _handle_question(self, text: str, matches: tuple):
        """Lida com perguntas"""
        question = matches[0] if matches else text
        
        # Resposta da IA
        ai_response = await self.ai_core.process_command(f"Pergunta: {question}")
        
        return {
            'voice_response': ai_response['voice_response'],
            'action_needed': False,
            'command_type': 'question'
        }
    
    async def _handle_control(self, text: str, matches: tuple):
        """Lida com comandos de controle"""
        action = matches[0] if matches else ""
        target = matches[1] if len(matches) > 1 else ""
        
        # Mapeamento de comandos simples
        control_map = {
            'liga': 'ligar',
            'desliga': 'desligar',
            'abre': 'abrir',
            'fecha': 'fechar',
            'mostra': 'mostrar',
            'esconde': 'esconder'
        }
        
        action_pt = control_map.get(action, action)
        
        response = f"{action_pt} {target}"
        
        return {
            'voice_response': f"Executando: {response}",
            'action_needed': True,
            'action_type': 'control',
            'action_details': {'action': action_pt, 'target': target},
            'command_type': 'control'
        }
    
    async def _handle_information(self, text: str, matches: tuple):
        """Lida com pedidos de informação"""
        if 'horas' in text:
            time_info = await self.utils.get_time()
            response = f"São {time_info}"
        elif 'dia' in text:
            date_info = await self.utils.get_date()
            response = f"Hoje é {date_info}"
        elif 'temperatura' in text or 'previsão' in text:
            weather = await self.utils.get_weather_light()
            response = f"A temperatura é {weather['temp']}°C, {weather['desc']}"
        else:
            response = "Posso informar sobre horário, data ou clima. O que precisa?"
        
        return {
            'voice_response': response,
            'action_needed': False,
            'command_type': 'information'
        }
    
    async def _handle_system(self, text: str, matches: tuple):
        """Lida com comandos do sistema"""
        if 'reinicia' in text:
            return {
                'voice_response': "Reiniciando sistema em 3 segundos",
                'action_needed': True,
                'action_type': 'system_restart',
                'command_type': 'system'
            }
        elif 'desliga' in text and 'sistema' in text:
            return {
                'voice_response': "Desligando sistema em 3 segundos",
                'action_needed': True,
                'action_type': 'system_shutdown',
                'command_type': 'system'
            }
        elif 'volume' in text:
            if 'alto' in text:
                volume_action = 'volume_up'
                response = "Aumentando volume"
            elif 'baixo' in text:
                volume_action = 'volume_down'
                response = "Diminuindo volume"
            elif 'mudo' in text:
                volume_action = 'volume_mute'
                response = "Modo mudo ativado"
            else:
                volume_action = None
                response = "Controle de volume disponível"
            
            return {
                'voice_response': response,
                'action_needed': volume_action is not None,
                'action_type': volume_action,
                'command_type': 'system'
            }
        
        return {
            'voice_response': "Comando do sistema recebido",
            'action_needed': False,
            'command_type': 'system'
        }
    
    async def _handle_conversation(self, text: str, matches: tuple):
        """Lida com conversas gerais"""
        # Encaminha para a IA principal
        return await self.ai_core.process_command(text)