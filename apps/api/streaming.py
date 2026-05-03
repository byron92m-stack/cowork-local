"""Streaming endpoints with Server-Sent Events (SSE).

Provides real-time token streaming like Claude Cowork.
Tokens appear one by one as the model generates them.
"""
import sys
import os
import json
import asyncio
from pathlib import Path
from typing import AsyncGenerator

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

class StreamRequest(BaseModel):
    query: str
    project_path: str = "."

async def stream_deepseek_tokens(prompt: str, system: str = "") -> AsyncGenerator[str, None]:
    """Stream tokens from DeepSeek API."""
    from models.deepseek_client import DeepSeekClient
    
    client = DeepSeekClient()
    
    # Usar el cliente OpenAI subyacente para streaming
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    try:
        stream = client.client.chat.completions.create(
            model=client.model,
            messages=messages,
            max_tokens=client.max_tokens,
            temperature=client.temperature,
            stream=True,
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'token': token})}\n\n"
        
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def stream_qwen_tokens(prompt: str, system: str = "") -> AsyncGenerator[str, None]:
    """Stream tokens from Qwen via Ollama."""
    import httpx
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "qwen2.5:14b",
                    "messages": messages,
                    "stream": True,
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                token = data["message"]["content"]
                                yield f"data: {json.dumps({'token': token})}\n\n"
                            if data.get("done"):
                                yield f"data: {json.dumps({'done': True})}\n\n"
                                break
                        except json.JSONDecodeError:
                            continue
    
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def stream_agent_progress(user_query: str, project_path: str) -> AsyncGenerator[str, None]:
    """Stream the entire agentic workflow step by step."""
    from graph.state import CoworkState
    from graph.graph import build_graph
    
    # Fase 1: Planning
    yield f"data: {json.dumps({'status': 'planning', 'message': 'Generating plan with DeepSeek...'})}\n\n"
    
    system_prompt = """You are a supervisor. Create a plan in JSON format.
Respond ONLY with valid JSON: {"plan": [{"id": "1", "description": "...", "assigned_to": "executor", "step_type": "analysis"}]}"""
    
    async for chunk in stream_deepseek_tokens(user_query, system_prompt):
        yield chunk
    
    # Fase 2: Execution
    yield f"data: {json.dumps({'status': 'executing', 'message': 'Running with Qwen GPU...'})}\n\n"
    
    executor_prompt = f"Execute this task: {user_query}. Be concise and direct."
    async for chunk in stream_qwen_tokens(executor_prompt):
        yield chunk
    
    # Fase 3: Done
    yield f"data: {json.dumps({'status': 'complete', 'message': 'Task completed'})}\n\n"


def setup_streaming_routes(app: FastAPI):
    """Add streaming endpoints to the FastAPI app."""
    
    @app.post("/stream/run")
    async def stream_run(request: StreamRequest):
        """Stream a complete agentic workflow."""
        return StreamingResponse(
            stream_agent_progress(
                request.query,
                request.project_path
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    @app.post("/stream/chat")
    async def stream_chat(request: StreamRequest):
        """Stream a simple chat with DeepSeek."""
        return StreamingResponse(
            stream_deepseek_tokens(request.query),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    @app.post("/stream/qwen")
    async def stream_qwen(request: StreamRequest):
        """Stream a chat with local Qwen GPU."""
        return StreamingResponse(
            stream_qwen_tokens(request.query),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    @app.get("/stream/demo")
    async def stream_demo():
        """Demo endpoint that shows how SSE works."""
        async def demo():
            import asyncio
            message = "Hello! This is streaming like Claude Cowork. Each token appears in real-time."
            for word in message.split():
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return StreamingResponse(
            demo(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    return app
