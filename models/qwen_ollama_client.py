"""
Cowork-Local: Cliente HTTP para Qwen 2.5 vía Ollama (Executor).

Ollama expone una API REST en http://127.0.0.1:11434.
Usamos httpx para comunicarnos.
"""

import logging
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class QwenOllamaClient:
    """
    Cliente para interactuar con Qwen 2.5 vía Ollama local.
    
    Uso:
        client = QwenOllamaClient()
        response = client.generate("Genera un script de Python que...")
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5:14b",
        max_tokens: int = 2048,
        temperature: float = 0.2,
        num_ctx: int = 4096,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.num_ctx = num_ctx
        self._check_connection()
        logger.info(f"QwenOllamaClient inicializado: model={model}, base_url={base_url}")

    def _check_connection(self) -> None:
        """Verifica que Ollama esté respondiendo."""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            if self.model not in model_names:
                logger.warning(f"Modelo '{self.model}' no encontrado. Disponibles: {model_names}")
            else:
                logger.info(f"Ollama OK. Modelo '{self.model}' disponible.")
        except httpx.ConnectError:
            raise ConnectionError(f"No se pudo conectar a Ollama en {self.base_url}.")
        except Exception as e:
            logger.warning(f"Verificación de Ollama: {e}")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Genera texto usando Qwen vía Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "num_ctx": self.num_ctx,
            }
        }
        if system:
            payload["system"] = system
        
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()
            content = result.get("response", "")
            if "eval_count" in result:
                eval_count = result.get("eval_count", 0)
                eval_duration = result.get("eval_duration", 1)
                tokens_per_sec = eval_count / (eval_duration / 1e9) if eval_duration > 0 else 0
                logger.debug(f"Ollama stats: tokens={eval_count}, duration={eval_duration/1e9:.2f}s, rate={tokens_per_sec:.1f} t/s")
            return content
        except httpx.TimeoutException:
            logger.error("Timeout en llamada a Ollama (>120s)")
            raise
        except Exception as e:
            logger.error(f"Error en llamada a Ollama: {e}")
            raise

    def analyze_code(
        self, code: str, file_path: str = "", analysis_type: str = "general"
    ) -> str:
        """Analiza código fuente."""
        system_prompt = (
            "Eres un ingeniero de software experto en análisis de código. "
            "Proporciona análisis claros y estructurados."
        )
        prompt = f"Archivo: {file_path or 'No especificado'}\nTipo: {analysis_type}\n\n```\n{code}\n```\n\nProporciona un análisis detallado."
        return self.generate(prompt=prompt, system=system_prompt, temperature=0.1)

    def generate_code(
        self, task: str, language: str = "python", context: str = ""
    ) -> str:
        """Genera código según una tarea."""
        system_prompt = (
            f"Eres un ingeniero de software experto en {language}. "
            "Genera código limpio, con type hints y docstrings. "
            "NO incluyas explicaciones fuera del código."
        )
        prompt = f"Tarea: {task}\nContexto: {context or 'Ninguno'}\n\nGenera el código en {language}."
        return self.generate(prompt=prompt, system=system_prompt, temperature=0.1)

    def generate_diff(
        self, original_code: str, changes_requested: str, file_path: str = ""
    ) -> str:
        """Genera un diff unificado."""
        system_prompt = (
            "Eres un ingeniero de software experto. Genera parches en formato diff unificado. "
            "Usa formato estándar (- para quitar, + para agregar). NO incluyas explicaciones."
        )
        prompt = (
            f"Archivo: {file_path or 'archivo'}\n\n"
            f"Código original:\n```\n{original_code}\n```\n\n"
            f"Cambios solicitados: {changes_requested}\n\n"
            "Genera un diff unificado."
        )
        return self.generate(prompt=prompt, system=system_prompt, temperature=0.1)
