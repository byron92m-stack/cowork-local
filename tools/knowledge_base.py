"""Knowledge Base with vector search for Cowork-Local."""
import os
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, storage_dir: str = "data/knowledge"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"
        self.documents = self._load_index()
    
    def _load_index(self) -> List[Dict]:
        if self.index_file.exists():
            with open(self.index_file) as f:
                return json.load(f)
        return []
    
    def _save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump(self.documents, f, indent=2)
    
    def add_document(self, content: str, metadata: Dict = None):
        doc = {
            "id": str(len(self.documents) + 1),
            "content": content,
            "metadata": metadata or {},
            "added_at": str(__import__('datetime').datetime.now())
        }
        self.documents.append(doc)
        self._save_index()
        return doc["id"]
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        # Búsqueda simple por palabras clave
        results = []
        query_words = query.lower().split()
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            score = sum(1 for word in query_words if word in content_lower)
            if score > 0:
                results.append({"score": score, "document": doc})
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return [r["document"] for r in results[:top_k]]

kb = KnowledgeBase()
print(f"Knowledge Base ready with {len(kb.documents)} documents")
