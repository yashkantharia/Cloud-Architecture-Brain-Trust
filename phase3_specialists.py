import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from ollama import Client

app_security = FastAPI(title="SecurityReviewer A2A Server")
app_cost = FastAPI(title="CostOptimizer A2A Server")

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen"

class ArchitectureDraft(BaseModel):
    draft: str

@app_security.post("/review")
def security_review(data: ArchitectureDraft):
    client = Client(host=OLLAMA_HOST)
    prompt = f"""
    You are an expert AWS Cloud Security Specialist.
    Review the following AWS architecture draft. Identify vulnerabilities (like missing encryption, overly permissive IAM, etc.) and mandate fixes.
    Return ONLY your updated security recommendations and fixes.
    
    Draft:
    {data.draft}
    """
    response = client.generate(model=MODEL_NAME, prompt=prompt)
    return {"feedback": response['response']}

@app_cost.post("/review")
def cost_review(data: ArchitectureDraft):
    client = Client(host=OLLAMA_HOST)
    prompt = f"""
    You are an expert AWS FinOps Engineer.
    Review the following AWS architecture draft for unnecessary costs. 
    Suggest cost optimization strategies like Spot Instances, serverless alternatives, or better sizing.
    Return ONLY your cost optimization recommendations.
    
    Draft:
    {data.draft}
    """
    response = client.generate(model=MODEL_NAME, prompt=prompt)
    return {"feedback": response['response']}

import multiprocessing

def run_security():
    uvicorn.run(app_security, host="0.0.0.0", port=9001)
    
def run_cost():
    uvicorn.run(app_cost, host="0.0.0.0", port=9002)

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_security)
    p2 = multiprocessing.Process(target=run_cost)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
