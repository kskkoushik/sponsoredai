"""
Vector Store module using ChromaDB for RAG-based ad retrieval.
Now uses a persistent ChromaDB client so the index survives restarts.
"""

import os

import chromadb
from chromadb.utils import embedding_functions
from ads_data import get_ads_for_embedding


# Use sentence-transformers for embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class AdVectorStore:
    """ChromaDB-based vector store for sponsored ads."""

    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize the vector store."""
        self.persist_directory = persist_directory

        # Ensure the persistence directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )

        # Initialize persistent ChromaDB client
        # This writes index data under self.persist_directory and reuses it
        # across process restarts.
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="sponsored_ads",
            embedding_function=self.embedding_function,
            metadata={"description": "Sponsored advertisements for RAG"},
        )

        # Initialize ads if collection is empty
        if self.collection.count() == 0:
            self._initialize_ads()
    
    def _initialize_ads(self):
        """Load ads into the vector store."""
        documents, metadatas, ids = get_ads_for_embedding()
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Initialized {len(documents)} ads in ChromaDB")
    
    def search_relevant_ads(self, query: str, n_results: int = 2) -> list[dict]:
        """
        Search for ads relevant to the query.
        
        Args:
            query: User's query text
            n_results: Number of ads to return
            
        Returns:
            List of relevant ad dictionaries
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["metadatas", "documents", "distances"]
        )
        
        relevant_ads = []
        if results and results["metadatas"]:
            for i, metadata in enumerate(results["metadatas"][0]):
                ad_info = {
                    "company": metadata["company"],
                    "category": metadata["category"],
                    "ad_text": metadata["ad_text"],
                    "relevance_score": 1 - results["distances"][0][i] if results["distances"] else 0
                }
                relevant_ads.append(ad_info)
        
        return relevant_ads


# Singleton instance
_vector_store = None


def get_vector_store() -> AdVectorStore:
    """Get or create the vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = AdVectorStore()
    return _vector_store


def search_ads(query: str, n_results: int = 2) -> list[dict]:
    """Convenience function to search ads."""
    store = get_vector_store()
    return store.search_relevant_ads(query, n_results)
