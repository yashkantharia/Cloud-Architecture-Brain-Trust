import chromadb

def main():
    print("Connecting to local ChromaDB...")
    try:
        db = chromadb.PersistentClient(path="./chroma_db")
        collection = db.get_collection(name="aws_guidelines")
        
        # Get all entries from DB
        data = collection.get()
        
        ids = data.get("ids", [])
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])
        
        print(f"\n--- Found {len(ids)} embedded chunks in Vector DB ---\n")
        
        for i in range(len(ids)):
            print(f"[{i+1}] ID: {ids[i]}")
            
            source = metadatas[i].get('source', 'Unknown') if metadatas and metadatas[i] else 'Unknown'
            print(f"    Source: {source}")
            
            # Print a snippet of the document
            doc_snippet = documents[i].replace('\n', ' ')
            if len(doc_snippet) > 100:
                doc_snippet = doc_snippet[:100] + "..."
            print(f"    Content snippet: {doc_snippet}\n")
            
    except Exception as e:
        print(f"Error reading vector DB: {e}")

if __name__ == "__main__":
    main()
