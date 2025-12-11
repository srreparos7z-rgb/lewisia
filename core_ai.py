"""
Módulo Core AI - Processamento de linguagem e personalidade
Implementação otimizada para hardware limitado
"""

import json
import re
import hashlib
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("Lewis.AI")

class AICore:
    """Núcleo de IA com personalidade Lewis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.personality = self.load_personality()
        self.context = []
        self.conversation_history = []
        
        # Cache otimizado para respostas frequentes
        self.response_cache = {}
        
    async def initialize(self):
        """Inicialização assíncrona"""
        logger.info("Inicializando núcleo de IA...")
        # Carrega modelos leves
        await self.load_minimal_models()
        
    async def load_minimal_models(self):
        """Carrega modelos minimizados para ARM"""
        # Modelo de intenções leve
        self.intent_patterns = {
            'saudacao': ['olá', 'oi', 'e ai', 'bom dia', 'boa tarde'],
            'pergunta': ['o que é', 'como funciona', 'por que', 'quando'],
            'acao': ['ligue', 'desligue', 'abra', 'feche', 'mostre'],
            'critica': ['está errado', 'não concordo', 'discordo'],
            'opiniao': ['o que você acha', 'qual sua opinião', 'você concorda']
        }
        
    def load_personality(self) -> Dict[str, Any]:
        """Carrega configuração de personalidade"""
        return {
            "name": "Lewis",
            "traits": {
                "assertive": True,
                "helpful": True,
                "critical": True,
                "empathetic": True,
                "humorous": False  # Pode ser ativado sob demanda
            },
            "response_style": {
                "agreement": ["Concordo", "Isso faz sentido", "Você tem razão"],
                "disagreement": ["Entendo seu ponto, mas...", "Discordo porque...", "Há um equívoco..."],
                "correction": ["Na verdade...", "Corrigindo...", "Vamos esclarecer..."],
                "question": ["Você já considerou...", "E se...", "O que você acha sobre..."]
            }
        }
    
    def check_wake_word(self, audio_data: bytes) -> bool:
        """Verificação leve de palavra de ativação"""
        # Implementação simplificada para baixo consumo
        import struct
        
        if len(audio_data) < 1024:
            return False
            
        # Análise simples de energia
        energy = sum(abs(struct.unpack('h', audio_data[i:i+2])[0]) 
                    for i in range(0, min(len(audio_data), 2048), 2))
        
        # Verificação básica (implementação real usaria modelo leve)
        return energy > 1000  # Threshold simplificado
    
    async def process_command(self, text: str) -> Dict[str, Any]:
        """Processa comando com personalidade Lewis"""
        logger.info(f"Processando: {text}")
        
        # Verifica cache primeiro
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]
        
        # Análise de intenção
        intent = self.analyze_intent(text)
        
        # Análise de sentimento
        sentiment = self.analyze_sentiment(text)
        
        # Geração de resposta com personalidade
        response = self.generate_response(text, intent, sentiment)
        
        # Atualiza contexto
        self.update_context(text, response)
        
        # Armazena em cache (tamanho limitado)
        if len(self.response_cache) < 100:
            self.response_cache[cache_key] = response
        
        return response
    
    def analyze_intent(self, text: str) -> str:
        """Análise leve de intenção"""
        text_lower = text.lower()
        
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return intent
        
        return "conversa"
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Análise simplificada de sentimento"""
        # Implementação leve para hardware limitado
        positive_words = ['bom', 'bem', 'ótimo', 'excelente', 'gosto', 'amo']
        negative_words = ['ruim', 'mal', 'péssimo', 'odeio', 'horrível', 'errado']
        
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        total = len(words)
        
        if total == 0:
            return {"positive": 0.5, "negative": 0.5, "neutral": 0.5}
        
        return {
            "positive": positive_count / total,
            "negative": negative_count / total,
            "neutral": (total - positive_count - negative_count) / total
        }
    
    def generate_response(self, text: str, intent: str, sentiment: Dict[str, float]) -> Dict[str, Any]:
        """Gera resposta com personalidade Lewis"""
        import random
        
        response = {
            "original_text": text,
            "intent": intent,
            "sentiment": sentiment,
            "needs_action": False,
            "action_type": None,
            "voice_response": "",
            "display_response": "",
            "personality_trait": "neutral"
        }
        
        # Lógica baseada em intenção
        if intent == "saudacao":
            greetings = ["Olá! Como posso ajudar?", "Oi! Tudo bem?", "Saudações! O que precisa?"]
            response["voice_response"] = random.choice(greetings)
            response["personality_trait"] = "friendly"
            
        elif intent == "critica" or sentiment["negative"] > 0.3:
            # Lewis não concorda automaticamente
            critical_responses = [
                "Entendo seu ponto, mas veja por este ângulo...",
                "Discordo um pouco. Vamos analisar...",
                "Há um equívoco nessa afirmação. Na verdade...",
                "Respeito sua opinião, mas os fatos mostram que..."
            ]
            response["voice_response"] = random.choice(critical_responses)
            response["personality_trait"] = "critical"
            
        elif intent == "pergunta":
            # Respostas mais detalhadas para perguntas
            response["voice_response"] = f"Excelente pergunta sobre '{text}'. Vou explicar de forma clara..."
            response["personality_trait"] = "helpful"
            
        else:
            # Resposta padrão conversacional
            conversational = [
                "Interessante. O que mais gostaria de saber?",
                "Compreendo. Vamos continuar nossa conversa.",
                "Percebi seu ponto. O que acha de discutirmos isso?"
            ]
            response["voice_response"] = random.choice(conversational)
            response["personality_trait"] = "empathetic"
        
        # Adiciona elementos de personalidade
        response["voice_response"] = self.add_personality_flavor(
            response["voice_response"], 
            response["personality_trait"]
        )
        
        response["display_response"] = f"🤖 Lewis: {response['voice_response']}"
        
        return response
    
    def add_personality_flavor(self, text: str, trait: str) -> str:
        """Adiciona sabor da personalidade à resposta"""
        if trait == "critical" and self.personality["traits"]["critical"]:
            return f"{text} (Isso é importante para tomarmos a melhor decisão.)"
        elif trait == "helpful" and self.personality["traits"]["helpful"]:
            return f"{text} Estou aqui para ajudar no que precisar."
        
        return text
    
    def update_context(self, user_input: str, response: Dict[str, Any]):
        """Atualiza contexto da conversa (mantém tamanho limitado)"""
        self.context.append({
            "user": user_input,
            "ai": response["voice_response"],
            "timestamp": self.get_timestamp()
        })
        
        # Mantém apenas últimos 10 itens para economizar memória
        if len(self.context) > 10:
            self.context.pop(0)
    
    def get_timestamp(self) -> str:
        """Timestamp leve"""
        import time
        return time.strftime("%H:%M:%S")