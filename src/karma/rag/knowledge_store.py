"""
Knowledge Store - Simple ChromaDB wrapper for one knowledge domain
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from .embeddings import Embeddings


class KnowledgeStore:
    """
    One knowledge store = one ChromaDB collection.
    Handles add, query, delete operations.
    """
    
    def __init__(
        self,
        name: str,
        persist_dir: str = None,
        embeddings: Embeddings = None
    ):
        """
        Create a knowledge store.
        
        Args:
            name: Store name (e.g., "market_insights", "trade_history")
            persist_dir: Directory to persist data. In-memory if None.
            embeddings: Embeddings instance. Creates default if None.
        """
        self.name = name
        self.embeddings = embeddings
        
        # Setup ChromaDB
        if persist_dir:
            self.persist_dir = os.path.join(persist_dir, name)
            os.makedirs(self.persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_dir)
        else:
            self.client = chromadb.Client(Settings(allow_reset=True))
        
        self.collection = self.client.get_or_create_collection(name=name)
    
    def add(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ) -> List[str]:
        """
        Add documents to the store.
        
        Args:
            texts: List of text documents
            metadatas: Optional metadata for each document
            ids: Optional IDs. Auto-generated if None.
        
        Returns:
            List of document IDs
        """
        if not texts:
            return []
        
        # Generate IDs
        if ids is None:
            offset = self.collection.count()
            ids = [f"{self.name}_{offset + i}" for i in range(len(texts))]
        
        # Generate embeddings
        embeddings = None
        if self.embeddings:
            embeddings = self.embeddings.embed_batch(texts)
        
        # Default metadata
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the store.
        
        Args:
            query_text: Search query
            n_results: Number of results
            where: Optional filter
        
        Returns:
            List of results with document, metadata, similarity
        """
        # Get query embedding
        query_embedding = None
        if self.embeddings:
            query_embedding = self.embeddings.embed(query_text)
        
        results = self.collection.query(
            query_embeddings=[query_embedding] if query_embedding else None,
            query_texts=[query_text] if not query_embedding else None,
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                formatted.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        
        return formatted
    
    def count(self) -> int:
        """Get document count."""
        return self.collection.count()
    
    def clear(self):
        """Delete all documents."""
        all_ids = self.collection.get()["ids"]
        if all_ids:
            self.collection.delete(ids=all_ids)
