#!/usr/bin/env python3
"""
One-time setup script to create Pinecone index and ingest Shopify Q&A data.
Run this once before starting the chatbot.

Usage:
    python setup_pinecone.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config


def main():
    """Main setup function."""
    print("=" * 60)
    print("Shopify Support Chatbot - Pinecone Setup")
    print("=" * 60)
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check your .env file and try again.")
        sys.exit(1)
    
    print("\n✅ Configuration validated")
    print(f"  - Pinecone Index: {config.PINECONE_INDEX_NAME}")
    print(f"  - Embedding Model: {config.EMBEDDING_MODEL}")
    
    # Check if JSONL file exists
    jsonl_path = project_root / "shopify_complete_qa.jsonl"
    if not jsonl_path.exists():
        print(f"\n❌ JSONL file not found: {jsonl_path}")
        sys.exit(1)
    
    print(f"  - Data file: {jsonl_path.name}")
    
    # Run ingestion
    print("\n" + "-" * 60)
    print("Starting data ingestion...")
    print("-" * 60 + "\n")
    
    from rag.ingestion import ingest_shopify_data
    count = ingest_shopify_data(str(jsonl_path))
    
    # Test query
    print("\n" + "-" * 60)
    print("Testing retrieval...")
    print("-" * 60 + "\n")
    
    from rag.vector_store import query_similar
    
    test_query = "How do I add products to my Shopify store?"
    results = query_similar(test_query, k=2)
    
    print(f"Query: \"{test_query}\"")
    print(f"Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"  [{i}] Score: {result['score']:.4f}")
        print(f"      Topic: {result['metadata'].get('topic', 'N/A')}")
        print(f"      Text: {result['text'][:150]}...")
        print()
    
    print("=" * 60)
    print("✅ Setup complete! You can now run the chatbot with:")
    print("   streamlit run app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
