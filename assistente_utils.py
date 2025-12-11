"""
Módulo de Utilitários - Funcionalidades e integrações
Otimizado para baixo consumo de recursos
"""

import asyncio
import aiohttp
import os
import json
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("Lewis.Utils")

class Utilitarios:
    """Classe de utilitários com funcionalidades leves"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.actions = self.load_actions()
        self.external_apis = self.load_api_configs()
        
    def load_actions(self) -> Dict[str, Any]:
        """Carrega ações disponíveis"""
        return {
            "system": {
                "shutdown": self.system_shutdown,
                "restart": self.system_restart,
                "status": self.system_status
            },
            "information": {
                "time": self.get_time,
                "date": self.get_date,
                "weather": self.get_weather_light
            },
            "entertainment": {
                "joke": self.get_joke,
                "quote": self.get_quote,
                "fact": self.get_fact
            }
        }
    
    def load_api_configs(self) -> Dict[str, Any]:
        """Carrega configurações de API (se existirem)"""
        config_path = "/tmp/lewis_apis.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    async def execute_action(self, response: Dict[str, Any]):
        """Executa ação baseada na resposta da IA"""
        if not response.get("needs_action", False):
            return
        
        action_type = response.get("action_type")
        
        if action_type in self.actions["system"]:
            await self.actions["system"][action_type]()
        elif action_type in self.actions["information"]:
            info = await self.actions["information"][action_type]()
            response["additional_info"] = info
        elif action_type in self.actions["entertainment"]:
            entertainment = await self.actions["entertainment"][action_type]()
            response["additional_info"] = entertainment
    
    # ========== SISTEMA ==========
    async def system_shutdown(self):
        """Desligamento controlado"""
        logger.info("Executando desligamento...")
        os.system("sudo shutdown -h now")
    
    async def system_restart(self):
        """Reinicialização"""
        logger.info("Reiniciando sistema...")
        os.system("sudo reboot")
    
    async def system_status(self) -> Dict[str, Any]:
        """Status do sistema (leve)"""
        import psutil
        
        return {
            "cpu": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory().percent,
            "temperature": self.get_cpu_temp()
        }
    
    def get_cpu_temp(self) -> Optional[float]:
        """Obtém temperatura da CPU (para ARM)"""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read().strip()) / 1000.0
            return temp
        except:
            return None
    
    # ========== INFORMAÇÕES ==========
    async def get_time(self) -> str:
        """Obtém hora atual"""
        import time
        return time.strftime("%H:%M")
    
    async def get_date(self) -> str:
        """Obtém data atual"""
        import time
        return time.strftime("%d/%m/%Y")
    
    async def get_weather_light(self) -> Dict[str, Any]:
        """Clima simplificado (sem API pesada)"""
        try:
            async with aiohttp.ClientSession() as session:
                # Usando API pública leve
                async with session.get('http://wttr.in/?format=j1', timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "temp": data['current_condition'][0]['temp_C'],
                            "desc": data['current_condition'][0]['weatherDesc'][0]['value']
                        }
        except:
            pass
        
        return {"temp": "N/A", "desc": "Não disponível"}
    
    # ========== ENTRETENIMENTO ==========
    async def get_joke(self) -> str:
        """Piada local (sem internet)"""
        jokes = [
            "Por que o Python foi dormir? Porque estava sem 'tuplas'!",
            "O que o assistente virtual disse para o usuário? 'Estou aqui para ajudar, não para fazer café!'",
            "Por que o computador foi ao médico? Porque tinha um vírus!"
        ]
        import random
        return random.choice(jokes)
    
    async def get_quote(self) -> str:
        """Citação inspiradora"""
        quotes = [
            "A tecnologia deve melhorar a vida, não substituí-la.",
            "A inteligência artificial não é sobre máquinas pensantes, mas sobre máquinas úteis.",
            "O maior perigo da IA não é que ela se rebela, mas que faz exatamente o que pedimos."
        ]
        import random
        return random.choice(quotes)
    
    async def get_fact(self) -> str:
        """Fato interessante"""
        facts = [
            "Seu TV Box tem mais poder de processamento que os computadores da Apollo 11.",
            "A primeira assistente virtual foi criada em 1966 no MIT.",
            "Lewis é otimizado para usar menos de 50MB de RAM."
        ]
        import random
        return random.choice(facts)