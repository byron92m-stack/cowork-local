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
        model: str = "deepseek-chat",
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

    def plan(
        self,
        user_query: str,
        project_context: Dict[str, Any],
        memory_context: Dict[str, Any] = None,
    ) -> str:
        """
        Genera un plan estructurado para la consulta del usuario.
        
        Args:
            user_query: La consulta original del usuario.
            project_context: Información del proyecto (archivos, estructura).
            memory_context: Contexto de memoria persistente (opcional).
            
        Returns:
            Respuesta del modelo con el plan.
        """
        system_prompt = """Eres un supervisor de desarrollo de software.
Tu tarea es crear un plan de acción detallado para la consulta del usuario.

Responde SIEMPRE en formato JSON con esta estructura:
{
  "plan": [
    {
      "id": "string",
      "description": "string",
      "assigned_to": "supervisor|executor|tools",
      "step_type": "analysis|code_generation|review|tool_call",
      "dependencies": []
    }
  ],
  "reasoning": "Explicación breve del plan"
}

Reglas:
1. Cada paso debe ser concreto y ejecutable.
2. Asigna cada paso al rol correcto (executor para código, tools para operaciones del sistema, supervisor para planificación/revisión).
3. No más de 7 pasos por plan.
4. Prioriza pasos de análisis antes que pasos de generación de código.
"""

        context_str = f"""
Proyecto: {project_context.get('path', 'No especificado')}
Estructura del proyecto: {project_context.get('structure', 'No disponible')}
Memoria previa: {memory_context or 'No hay memoria previa'}

Consulta del usuario: {user_query}
"""
        
        return self.chat(
            prompt=context_str,
            system=system_prompt,
            json_mode=True,
            temperature=0.1,
        )

    def review(
        self,
        original_query: str,
        step_description: str,
        step_result: str,
        artifacts: List[Dict[str, Any]],
    ) -> str:
        """
        Revisa el resultado de un paso y decide si es aceptable.
        
        Args:
            original_query: La consulta original del usuario.
            step_description: Descripción del paso ejecutado.
            step_result: Resultado del paso.
            artifacts: Lista de artefactos generados.
            
        Returns:
            Respuesta del modelo con la revisión.
        """
        system_prompt = """Eres un revisor de calidad de software.
Evalúa si el resultado de un paso de ejecución es satisfactorio.

Responde SIEMPRE en formato JSON:
{
  "status": "done|failed|needs_correction",
  "feedback": "string con observaciones",
  "corrections_needed": ["lista de correcciones si aplica"]
}
"""
        
        review_prompt = f"""
Consulta original: {original_query}

Paso ejecutado: {step_description}

Resultado obtenido: {step_result}

Artefactos generados: {artifacts}

Evalúa si el resultado cumple con lo solicitado en la consulta original.
"""
        
        return self.chat(
            prompt=review_prompt,
            system=system_prompt,
            json_mode=True,
            temperature=0.1,
        )
