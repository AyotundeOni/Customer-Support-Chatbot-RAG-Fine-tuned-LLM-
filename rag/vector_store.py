"""
Pinecone vector store integration for RAG.
Handles indexing and querying of embedded documents.
"""
from pinecone import Pinecone, ServerlessSpec
from config import config
from rag.embeddings import get_embeddings


class VectorStore:
    """Pinecone vector store for document retrieval."""
    
    _instance = None
    _index = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Pinecone connection."""
        if self._index is None:
            print("Connecting to Pinecone...")
            self._pc = Pinecone(api_key=config.PINECONE_API_KEY)
            self._ensure_index_exists()
            self._index = self._pc.Index(config.PINECONE_INDEX_NAME)
    
    def _ensure_index_exists(self):
        """Create the index if it doesn't exist."""
        existing_indexes = [idx.name for idx in self._pc.list_indexes()]
        
        if config.PINECONE_INDEX_NAME not in existing_indexes:
            print(f"Creating index: {config.PINECONE_INDEX_NAME}")
            self._pc.create_index(
                name=config.PINECONE_INDEX_NAME,
                dimension=config.PINECONE_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print("Index created successfully!")
        else:
            print(f"Index {config.PINECONE_INDEX_NAME} already exists")
    
    def upsert_documents(
        self, 
        documents: list,
        batch_size: int = 100
    ) -> int:
        """Upsert documents to the vector store.
        
        Args:
            documents: List of dicts with 'id', 'text', and optional 'metadata'
            batch_size: Number of documents to upsert at once
            
        Returns:
            Total number of documents upserted
        """
        total = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Get embeddings for batch
            texts = [doc["text"] for doc in batch]
            print(f"  Generating embeddings for batch {i//batch_size + 1}...")
            embeddings = get_embeddings(texts, show_progress=True)
            
            # Prepare vectors for upsert
            vectors = []
            for doc, embedding in zip(batch, embeddings):
                vectors.append({
                    "id": doc["id"],
                    "values": embedding,
                    "metadata": {
                        "text": doc["text"][:1000],  # Truncate for metadata limit
                        **doc.get("metadata", {})
                    }
                })
            
            # Upsert batch
            print(f"  Upserting {len(batch)} vectors to Pinecone...")
            self._index.upsert(vectors=vectors)
            total += len(batch)
            print(f"✓ Upserted {total}/{len(documents)} documents")
        
        return total
    
    def query(
        self, 
        query_text: str, 
        top_k: int = None,
        filter: dict = None
    ) -> list[dict]:
        """Query the vector store for similar documents.
        
        Args:
            query_text: The query to search for
            top_k: Number of results to return (default from config)
            filter: Optional metadata filter
            
        Returns:
            List of matches with scores and metadata
        """
        if top_k is None:
            top_k = config.RAG_TOP_K
            
        # Get query embedding
        query_embedding = get_embeddings(query_text)
        
        # Query Pinecone
        results = self._index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        
        # Format results
        matches = []
        for match in results.matches:
            matches.append({
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "metadata": {k: v for k, v in match.metadata.items() if k != "text"}
            })
        
        return matches
    
    def delete_all(self):
        """Delete all vectors from the index."""
        self._index.delete(delete_all=True)
        print("All vectors deleted from index")
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        return self._index.describe_index_stats()


# Convenience functions
def query_similar(query: str, k: int = 3) -> list[dict]:
    """Query for similar documents."""
    store = VectorStore()
    return store.query(query, top_k=k)


def get_context_for_query(query: str, k: int = 3) -> str:
    """Get formatted context string for a query.
    
    Returns a string with the top-k most relevant documents
    formatted for use as context in a prompt.
    """
    results = query_similar(query, k)
    
    if not results:
        return "No relevant information found in the knowledge base."
    
    context_parts = []
    for i, result in enumerate(results, 1):
        source = result["metadata"].get("source_url", "Unknown source")
        topic = result["metadata"].get("topic", "General")
        context_parts.append(
            f"[Source {i}] (Topic: {topic})\n{result['text']}\n"
        )
    
    return "\n".join(context_parts)
