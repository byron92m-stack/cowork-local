"""
Cowork-Local: Cliente HTTP para DeepSeek Cloud (Supervisor).

DeepSeek usa una API compatible con OpenAI, por lo que podemos usar
la librería `openai` para comunicarnos.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """
    Cliente para interactuar con DeepSeek Cloud API.
    
    Se comunica con el endpoint compatible con OpenAI en:
    https://api.deepseek.com/v1
    
    Uso:
        client = DeepSeekClient()
        response = client.chat("Analiza este proyecto", system="Eres un supervisor...")
    
    La API key se lee automáticamente de la variable de entorno DEEPSEEK_API_KEY.
    También se puede pasar explícitamente: DeepSeekClient(api_key="tu-key")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-reasoner",
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ):
        """
        Inicializa el cliente DeepSeek.
        
        Args:
            api_key: API key de DeepSeek. Si es None, se lee de DEEPSEEK_API_KEY.
            base_url: URL base de la API.
            model: Nombre del modelo a usar.
            max_tokens: Máximo de tokens a generar.
            temperature: Temperatura (0.0-1.0). Más bajo = más determinístico.
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DeepSeek API key no encontrada. "
                "Configúrala en la variable de entorno DEEPSEEK_API_KEY "
                "o pásala como argumento."
            )
        
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Cliente OpenAI-compatible
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        logger.info(f"DeepSeekClient inicializado: model={model}, base_url={base_url}")

    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Envía un prompt a DeepSeek y devuelve la respuesta.
        
        Args:
            prompt: El mensaje del usuario.
            system: System prompt opcional.
            max_tokens: Override del máximo de tokens.
            temperature: Override de la temperatura.
            json_mode: Si es True, la respuesta debe ser JSON válido.
            
        Returns:
            El texto de respuesta del modelo.
        """
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "stream": False,
        }
        
        # DeepSeek soporta response_format para JSON mode
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        
        try:
            logger.debug(f"Llamando a DeepSeek: {len(prompt)} caracteres")
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content
            
            logger.debug(
                f"Respuesta DeepSeek: {len(content)} caracteres, "
                f"tokens={response.usage.total_tokens}"
            )
            
            return content
            
        except Exception as e:
            logger.error(f"Error en llamada a DeepSeek: {e}")
            raise

