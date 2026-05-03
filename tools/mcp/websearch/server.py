"""Web Search MCP Server - Real-time internet search via Tavily."""
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def call_tool(tool_name: str, arguments: Dict[str, Any]):
    """Execute web search operations."""
    
    if tool_name == "search":
        query = arguments.get("query", "")
        # Usar ddgs para búsqueda real
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                formatted = []
                for r in results:
                    formatted.append(f"Title: {r.get('title', '')}\nURL: {r.get('href', '')}\nSnippet: {r.get('body', '')}\n")
                return [type('obj', (object,), {'text': '\n'.join(formatted)})()]
        except ImportError:
            return [type('obj', (object,), {'text': f"Search results for: {query} (install ddgs for real results)"})()]
    
    elif tool_name == "news":
        query = arguments.get("query", "")
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=5))
                formatted = []
                for r in results:
                    formatted.append(f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nDate: {r.get('date', '')}\n")
                return [type('obj', (object,), {'text': '\n'.join(formatted)})()]
        except ImportError:
            return [type('obj', (object,), {'text': f"News results for: {query}"})()]
    
    elif tool_name == "fetch_page":
        url = arguments.get("url", "")
        try:
            import httpx
            response = httpx.get(url, timeout=10)
            return [type('obj', (object,), {'text': response.text[:5000]})()]
        except Exception as e:
            return [type('obj', (object,), {'text': f"Error fetching {url}: {e}"})()]
    
    else:
        return [type('obj', (object,), {'text': f"Unknown search tool: {tool_name}"})()]
