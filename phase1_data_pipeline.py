import os
import json
import glob
import fitz  # PyMuPDF
import chromadb
from ollama import Client

import textwrap

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen"
EMBEDDING_MODEL = "nomic-embed-text"

def extract_text_from_pdf(pdf_path, max_pages=5):
    """Extracts text from the first few pages of the PDF for demonstration."""
def extract_text_from_pdf(pdf_path, max_pages=15):
    """Extracts text from the first few pages of the PDF for demonstration."""
    doc = fitz.open(pdf_path)
    text = ""
    for i in range(min(max_pages, len(doc))):
        page = doc[i]
        page_text = page.get_text()
        if page_text:
            text += page_text + "\n\n"
    return text

def agentic_chunking(text, client):
    """Uses the local LLM to extract architectural rules as a JSON array."""
def agentic_chunking(text, client):
    """Uses the local LLM to extract architectural rules as a JSON array."""
    
    # We add detailed instructions to prevent narrative text and force clean string elements.
    prompt = f"""
    You are an expert AWS Cloud Architect. I will provide you with a section of an AWS architectural document.
    Your task is to extract all self-contained architectural rules, best practices, guidelines, and core concepts from the text.
    
    CRITICAL INSTRUCTIONS:
    1. Extract the information as a pure JSON array of strings.
    2. Each string must be a distinct, self-contained rule or guideline that makes sense out of context.
    3. DO NOT include narrative text, tables of contents, glossaries, or meaningless fragments.
    4. If the text does not contain any useful architectural guidelines, return an empty array: []
    
    EXAMPLE OUTPUT FORMAT:
    [
      "Deploy highly available databases across multiple Availability Zones.",
      "Encrypt all data at rest using AWS KMS.",
      "Utilize spot instances for stateless, fault-tolerant workloads to optimize costs."
    ]
    
    TEXT TO PROCESS:
    {text}
    """
    
    print(f"Sending {len(text)} chars to {MODEL_NAME} for chunking...")
    
    try:
        # Enforce JSON output using Ollama's format parameter
        response = client.generate(model=MODEL_NAME, prompt=prompt, format="json")
        res_text = response['response'].strip()
        
        # If the model returned nothing or gibberish, return an empty list
        if not res_text or res_text == '[]' or res_text == '{}':
             return []
             
        chunks = json.loads(res_text)
        
        # Ensure we always return a clean list of valid, substantial strings
        extracted_rules = []
        if isinstance(chunks, list):
            for c in chunks:
                rule = str(c).strip()
                # Filter out very short meaningless gibberish (e.g., "e a b c")
                if len(rule) > 15:  
                    extracted_rules.append(rule)
            return extracted_rules
        elif isinstance(chunks, dict):
            # Sometimes models return a dict with a list inside
            for key, val in chunks.items():
                if isinstance(val, list):
                    for c in val:
                        rule = str(c).strip()
                        if len(rule) > 15:
                            extracted_rules.append(rule)
                    return extracted_rules
            # If it's just a dict without lists, try to convert the dict itself to a string
            rule = str(chunks).strip()
            if len(rule) > 15:
               return [rule]
        else:
            rule = str(chunks).strip()
            if len(rule) > 15:
               return [rule]
               
        return []

    except json.JSONDecodeError:
        print(f"Failed to parse JSON. Raw output: {res_text[:100]}...")
        return []
    except Exception as e:
        print(f"Unexpected error during chunking: {e}")
        return []

def create_vector_db(chunks, sources, client):
    print("Initializing ChromaDB...")
    db = chromadb.PersistentClient(path="./chroma_db")
    collection = db.get_or_create_collection(name="aws_guidelines")
    
    for i, (chunk, source) in enumerate(zip(chunks, sources)):
        if not chunk.strip():
            continue
        print(f"Embedding chunk {i+1}/{len(chunks)}...")
        # Get embedding from Ollama
        emb_res = client.embeddings(model=EMBEDDING_MODEL, prompt=chunk)
        embedding = emb_res['embedding']
        
        collection.add(
            # Create a more unique ID using the source and index
            ids=[f"rule_{source}_{i}"],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{"source": source}]
        )
    print(f"Successfully stored {len(chunks)} chunks in ChromaDB!")

def test_retrieval():
    print("Testing retrieval for query: 'database high availability'")
    db = chromadb.PersistentClient(path="./chroma_db")
    collection = db.get_collection(name="aws_guidelines")
    
    client = Client(host=OLLAMA_HOST)
    emb_res = client.embeddings(model=EMBEDDING_MODEL, prompt="database high availability")
    
    results = collection.query(
        query_embeddings=[emb_res['embedding']],
        n_results=2
    )
    print("Retrieval Results:")
    for doc in results['documents'][0]:
        print("-", doc)

def main():
    data_dir = "data"
    pdf_paths = glob.glob(os.path.join(data_dir, "*.pdf"))
    
    if not pdf_paths:
        print(f"Error: No PDF files found in {data_dir} directory.")
        return
    
    client = Client(host=OLLAMA_HOST)
    
    all_chunks = []
    chunk_sources = []
    
    for pdf_path in pdf_paths:
        print(f"\nProcessing {pdf_path}...")
        text = extract_text_from_pdf(pdf_path, max_pages=15)
        
        if not text.strip():
            print(f"Skipping {pdf_path}: No text extracted.")
            continue
            
        # Send text to agentic chunker in reasonable sizes (approx 3500 chars)
        text_blocks = textwrap.wrap(text, width=3500, break_long_words=False, replace_whitespace=False)
        
        pdf_chunks = []
        for j, block in enumerate(text_blocks):
            print(f"  -> Agent chunking block {j+1}/{len(text_blocks)}...")
            block_chunks = agentic_chunking(block, client)
            pdf_chunks.extend(block_chunks)
            
        print(f"Extracted {len(pdf_chunks)} architectural rules from {os.path.basename(pdf_path)}.")
        
        all_chunks.extend(pdf_chunks)
        chunk_sources.extend([os.path.basename(pdf_path)] * len(pdf_chunks))
    
    if all_chunks:
        # Before adding new chunks, let's clear out the old gibberish database completely so it's clean
        db = chromadb.PersistentClient(path="./chroma_db")
        try:
            db.delete_collection(name="aws_guidelines")
            print("Purged old vector database collection.")
        except Exception:
            pass # Collection probably didn't exist or was already deleted
            
        create_vector_db(all_chunks, chunk_sources, client)
    else:
        print("No architectural rules extracted from any PDFs.")
        
    test_retrieval()

if __name__ == "__main__":
    main()
