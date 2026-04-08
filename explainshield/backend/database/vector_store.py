import os
import logging
from typing import Optional
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("chromadb not installed. Vector store will use fallback.")


class VectorStore:
    DEFAULT_PERSIST_DIR = "./data/chromadb"
    
    def __init__(self, persist_directory: Optional[str] = None):
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb not installed. Install with: pip install chromadb")
        
        self.persist_directory = persist_directory or self.DEFAULT_PERSIST_DIR
        os.makedirs(self.persist_directory, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB at: {self.persist_directory}")
        
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self._documents_collection = None
        self._claims_collection = None
    
    @property
    def documents_collection(self):
        if self._documents_collection is None:
            self._documents_collection = self.client.get_or_create_collection(
                name="claim_documents",
                metadata={"description": "Embedded claim documents for grounding"}
            )
        return self._documents_collection
    
    @property
    def claims_collection(self):
        if self._claims_collection is None:
            self._claims_collection = self.client.get_or_create_collection(
                name="claims",
                metadata={"description": "Processed claim features"}
            )
        return self._claims_collection
    
    def add_document(
        self,
        claim_id: str,
        document_text: str,
        embeddings: list,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Add a document with embeddings to the vector store.
        
        Args:
            claim_id: Unique identifier for the claim
            document_text: Raw text extracted from document
            embeddings: Float list of embeddings
            metadata: Optional additional metadata
            
        Returns:
            Document ID
        """
        doc_id = f"doc_{claim_id}_{uuid.uuid4().hex[:8]}"
        
        meta = metadata or {}
        meta.update({
            "claim_id": claim_id,
            "text_length": len(document_text),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.documents_collection.add(
            ids=[doc_id],
            embeddings=[embeddings],
            documents=[document_text],
            metadatas=[meta]
        )
        
        logger.info(f"Added document {doc_id} for claim {claim_id}")
        return doc_id
    
    def search_similar(
        self,
        query_embedding: list,
        claim_id: str,
        n_results: int = 5
    ) -> dict:
        """
        Search for similar document chunks within a claim's context.
        
        Args:
            query_embedding: Embedding to search for
            claim_id: Filter by claim_id
            n_results: Number of results to return
            
        Returns:
            dict with documents, distances, metadatas
        """
        results = self.documents_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"claim_id": claim_id}
        )
        
        return {
            "documents": results.get("documents", [[]])[0],
            "distances": results.get("distances", [[]])[0],
            "metadatas": results.get("metadatas", [{}])[0]
        }
    
    def get_document_by_claim(self, claim_id: str) -> dict:
        """
        Get all documents for a specific claim.
        """
        results = self.documents_collection.get(
            where={"claim_id": claim_id}
        )
        
        return {
            "documents": results.get("documents", []),
            "ids": results.get("ids", []),
            "metadatas": results.get("metadatas", [])
        }
    
    def delete_claim_documents(self, claim_id: str):
        """
        Delete all documents associated with a claim.
        """
        results = self.documents_collection.get(
            where={"claim_id": claim_id}
        )
        
        if results.get("ids"):
            self.documents_collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} documents for claim {claim_id}")
    
    def semantic_search_documents(
        self,
        query_text: str,
        company_id: str,
        n_results: int = 10
    ) -> dict:
        """
        Search across all documents for a company using text query.
        Uses ChromaDB's built-in embedding function.
        """
        results = self.documents_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"company_id": company_id}
        )
        
        return {
            "documents": results.get("documents", [[]])[0],
            "distances": results.get("distances", [[]])[0],
            "metadatas": results.get("metadatas", [{}])[0]
        }


# Global instance
_vector_store: Optional[VectorStore] = None


def get_vector_store(persist_directory: Optional[str] = None) -> VectorStore:
    """
    Get or create the global VectorStore instance.
    """
    global _vector_store
    
    if _vector_store is None:
        _vector_store = VectorStore(persist_directory)
    
    return _vector_store


def reset_vector_store():
    """Reset the global VectorStore instance."""
    global _vector_store
    _vector_store = None


if __name__ == "__main__":
    print("Vector Store module loaded.")
    if CHROMADB_AVAILABLE:
        print(f"Default persist directory: {VectorStore.DEFAULT_PERSIST_DIR}")