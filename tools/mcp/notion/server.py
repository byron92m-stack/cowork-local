from typing import Dict, Any
"""Notion MCP Server - Database and page operations."""
import os
import logging

logger = logging.getLogger(__name__)

async def call_tool(tool_name: str, arguments: Dict[str, Any]):
    """Execute Notion operations."""
    
    if tool_name == "create_page":
        title = arguments.get("title", "New Page")
        content = arguments.get("content", "")
        database_id = arguments.get("database_id", "")
        
        try:
            from notion_client import Client
            token = os.getenv("NOTION_TOKEN")
            if not token:
                return [type('obj', (object,), {'text': "Notion not configured. Set NOTION_TOKEN"})()]
            
            notion = Client(auth=token)
            
            if database_id:
                notion.pages.create(
                    parent={"database_id": database_id},
                    properties={
                        "title": {"title": [{"text": {"content": title}}]}
                    },
                    children=[{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"text": {"content": content}}]}
                    }]
                )
            else:
                notion.pages.create(
                    parent={"type": "workspace"},
                    properties={
                        "title": {"title": [{"text": {"content": title}}]}
                    }
                )
            
            return [type('obj', (object,), {'text': f"Page created: {title}"})()]
        except ImportError:
            return [type('obj', (object,), {'text': "Install notion-client: pip install notion-client"})()]
    
    elif tool_name == "search_pages":
        query = arguments.get("query", "")
        return [type('obj', (object,), {'text': f"Search results for: {query}"})()]
    
    else:
        return [type('obj', (object,), {'text': f"Unknown notion tool: {tool_name}"})()]
