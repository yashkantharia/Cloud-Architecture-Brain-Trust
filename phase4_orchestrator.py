import asyncio
import requests
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai

SECURITY_A2A_URL = "http://localhost:9001/review"
COST_A2A_URL = "http://localhost:9002/review"
MCP_SERVER_SCRIPT = "phase2_mcp_server.py"

async def run_orchestrator(user_request: str):
    print("User Request:", user_request)

    if not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = input("Please enter your GEMINI_API_KEY: ")

    client = genai.Client()
    
    print("\n[Step 1] Calling RAG Database via MCP Tool...")
    server_params = StdioServerParameters(
        command="python",
        args=[MCP_SERVER_SCRIPT]
    )
    
    rag_context = ""
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # Calling the MCP Phase 2 Tool
                result = await session.call_tool("search_aws_guidelines", arguments={"query": user_request})
                # Result structure in MCP
                if result.content and len(result.content) > 0:
                    rag_context = result.content[0].text
                else:
                    rag_context = str(result)
    except Exception as e:
        print("MCP Server Error (Make sure phase2_mcp_server.py runs properly):", e)
        rag_context = "Fallback: Use highly available databases (RDS Multi-AZ) and Spot Instances for cost saving."

    print("RAG Context Retrieved:", rag_context[:200], "...")

    print("\n[Step 2] Lead Architect generating initial draft...")
    prompt = f"""
    You are the Lead Cloud Solutions Architect.
    Based on the following user request and AWS guidelines retrieved from our RAG database, write an initial architecture draft.
    
    User Request: {user_request}
    
    AWS Guidelines (RAG):
    {rag_context}
    
    Draft an architecture report. Include components, data flow, and initial setup.
    """
    
    draft_response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    draft = draft_response.text
    print("\n--- Initial Draft Preview ---")
    print(draft[:300], "...")

    print("\n[Step 3] Passing draft to SecurityReviewer (A2A)...")
    try:
        sec_resp = requests.post(SECURITY_A2A_URL, json={"draft": draft})
        sec_feedback = sec_resp.json().get("feedback", "No feedback")
        print("Security Feedback received.")
    except Exception as e:
        print("A2A connection failed. Ensure phase3_specialists.py is running. Error:", e)
        sec_feedback = "Security Agent unreachable."

    print("\n[Step 4] Passing draft to CostOptimizer (A2A)...")
    try:
        cost_resp = requests.post(COST_A2A_URL, json={"draft": draft})
        cost_feedback = cost_resp.json().get("feedback", "No feedback")
        print("Cost Feedback received.")
    except Exception as e:
        print("A2A connection failed. Ensure phase3_specialists.py is running. Error:", e)
        cost_feedback = "Cost Agent unreachable."

    print("\n[Step 5] Compiling final, unified markdown report...")
    final_prompt = f"""
    You are the Lead Cloud Solutions Architect.
    Update your initial draft by integrating the feedback from our Security and Cost specialists.
    Output ONLY the final markdown report. Focus strongly on practical AWS solutions.

    Initial Draft:
    {draft}

    Security Specialist Mandates:
    {sec_feedback}

    FinOps (Cost) Engineer Recommendations:
    {cost_feedback}
    """
    
    final_response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=final_prompt,
    )
    final_report = final_response.text
    
    print("\n================ FINAL REPORT ================\n")
    print(final_report)
    
    with open("final_architecture.md", "w") as f:
        f.write(final_report)
    print("\nReport saved to final_architecture.md")

if __name__ == "__main__":
    user_req = "I want to deploy a highly available PostgreSQL database and a scalable web tier for an e-commerce platform on AWS."
    asyncio.run(run_orchestrator(user_req))
