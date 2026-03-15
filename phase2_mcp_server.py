from mcp.server.fastmcp import FastMCP
import chromadb
from ollama import Client
import json

OLLAMA_HOST = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"

mcp = FastMCP("AWS_RAG_Server")

@mcp.tool()
def search_aws_guidelines(query: str) -> str:
    """Searches the AWS guidelines local RAG database for a given query and returns relevant text chunks."""
    try:
        client = Client(host=OLLAMA_HOST)
        db = chromadb.PersistentClient(path="./chroma_db")
        collection = db.get_collection(name="aws_guidelines")
        
        emb_res = client.embeddings(model=EMBEDDING_MODEL, prompt=query)
        
        results = collection.query(
            query_embeddings=[emb_res['embedding']],
            n_results=3
        )
        
        if not results['documents'][0]:
            return "No relevant guidelines found."
        
        context = "\n- ".join(results['documents'][0])
        return f"AWS Guidelines matching '{query}':\n- {context}"
    except Exception as e:
        return f"Error connecting to RAG Vector DB: {e}"

if __name__ == "__main__":
    print("Starting MCP Server on stdio...")
    mcp.run()
