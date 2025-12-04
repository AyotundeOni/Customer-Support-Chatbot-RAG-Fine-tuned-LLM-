"""
Data ingestion pipeline for JSONL Q&A data.
Parses the Shopify Q&A dataset and prepares it for vector store ingestion.
"""
import json
from pathlib import Path


def load_jsonl(file_path: str) -> list[dict]:
    """Load JSONL file and return list of records.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        List of parsed JSON records
    """
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def parse_qa_for_rag(records: list[dict]) -> list[dict]:
    """Parse Q&A records into documents suitable for RAG.
    
    Creates a document for each Q&A pair that combines the question
    and answer for better retrieval, with the answer as the primary text.
    
    Args:
        records: List of Q&A records from JSONL
        
    Returns:
        List of documents ready for vector store
    """
    documents = []
    
    for i, record in enumerate(records):
        messages = record.get("messages", [])
        metadata = record.get("metadata", {})
        
        # Extract user question and assistant answer
        question = ""
        answer = ""
        
        for msg in messages:
            if msg.get("role") == "user":
                question = msg.get("content", "")
            elif msg.get("role") == "assistant":
                answer = msg.get("content", "")
        
        if not question or not answer:
            continue
        
        # Create document with combined Q&A for better semantic matching
        # The text includes both so it matches user queries
        combined_text = f"Question: {question}\n\nAnswer: {answer}"
        
        documents.append({
            "id": f"shopify-qa-{i}",
            "text": combined_text,
            "metadata": {
                "question": question[:500],  # Truncate for metadata limits
                "source_url": metadata.get("source_url", ""),
                "topic": metadata.get("topic", "General"),
                "date_scraped": metadata.get("date_scraped", "")
            }
        })
    
    return documents


def ingest_shopify_data(jsonl_path: str = "shopify_complete_qa.jsonl") -> int:
    """Main ingestion function to load and index Shopify Q&A data.
    
    Args:
        jsonl_path: Path to the JSONL file
        
    Returns:
        Number of documents indexed
    """
    from rag.vector_store import VectorStore
    
    # Load and parse data
    print(f"Loading data from {jsonl_path}...")
    records = load_jsonl(jsonl_path)
    print(f"Loaded {len(records)} records")
    
    # Parse for RAG
    print("Parsing Q&A pairs for RAG...")
    documents = parse_qa_for_rag(records)
    print(f"Prepared {len(documents)} documents")
    
    # Index documents
    print("Indexing documents to Pinecone...")
    store = VectorStore()
    count = store.upsert_documents(documents)
    
    print(f"\n✅ Successfully indexed {count} documents!")
    return count
