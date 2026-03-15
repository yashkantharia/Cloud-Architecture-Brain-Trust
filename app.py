import asyncio
import requests
import os
import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai

SECURITY_A2A_URL = "http://localhost:9001/review"
COST_A2A_URL = "http://localhost:9002/review"
MCP_SERVER_SCRIPT = "phase2_mcp_server.py"

st.set_page_config(page_title="AWS Brain Trust", page_icon="☁️", layout="wide")

st.title("The Cloud Architecture Brain Trust ☁️🤖")
st.markdown("Interact with the Lead Architect, Security Specialist, and FinOps Engineer.")

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_api_key)
    if api_key_input:
        st.session_state.gemini_api_key = api_key_input
        os.environ["GEMINI_API_KEY"] = api_key_input
    
    st.markdown("Ensure your **Ollama servers** (`phase3_specialists.py`) are running.")

async def run_orchestrator(user_request: str):
    if not st.session_state.gemini_api_key:
        st.error("Please enter a Gemini API Key in the sidebar.")
        return None
        
    client = genai.Client()
    
    with st.status("Brain Trust is analyzing your request...", expanded=True) as status:
        
        # 1. MCP RAG Retrieval
        st.write("🕵️ **Lead Architect** is querying the RAG Database (MCP)...")
        server_params = StdioServerParameters(command="python", args=[MCP_SERVER_SCRIPT])
        rag_context = ""
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool("search_aws_guidelines", arguments={"query": user_request})
                    if result.content and len(result.content) > 0:
                        rag_context = result.content[0].text
                    else:
                        rag_context = str(result)
            st.info(f"**Retrieved Knowledge Base Context:**\n{rag_context}")
        except Exception as e:
            st.warning(f"MCP Server Error: Make sure `phase2_mcp_server.py` is working. Local knowledge skipped. Error: {e}")
            rag_context = "No specific local guidelines available."

        # 2. Drafting Architecture
        st.write("🏗️ **Lead Architect** is drafting initial blueprint...")
        prompt = f"""
        You are the Lead Cloud Solutions Architect.
        Based on the following user request and AWS guidelines retrieved from our RAG database, write an initial architecture draft.
        
        User Request: {user_request}
        
        AWS Guidelines (RAG):
        {rag_context}
        
        Draft an architecture report. Include components, data flow, and initial setup.
        """
        draft_response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        draft = draft_response.text
        
        with st.expander("View Architect's Initial Draft"):
            st.markdown(draft)

        # 3. Security Review
        st.write("🔒 **Security Specialist** is reviewing the draft via A2A...")
        try:
            sec_resp = requests.post(SECURITY_A2A_URL, json={"draft": draft})
            sec_feedback = sec_resp.json().get("feedback", "No feedback")
            with st.expander("View Security Requirements"):
                st.markdown(sec_feedback)
        except Exception as e:
            st.error(f"Security A2A Error. Is `phase3_specialists.py` running? {e}")
            sec_feedback = "Security Agent unreachable."

        # 4. Cost Review
        st.write("💰 **FinOps Engineer** is optimizing costs via A2A...")
        try:
            cost_resp = requests.post(COST_A2A_URL, json={"draft": draft})
            cost_feedback = cost_resp.json().get("feedback", "No feedback")
            with st.expander("View FinOps Recommendations"):
                st.markdown(cost_feedback)
        except Exception as e:
            st.error(f"Cost A2A Error. Is `phase3_specialists.py` running? {e}")
            cost_feedback = "Cost Agent unreachable."

        # 5. Final Compilation
        st.write("📝 **Lead Architect** is compiling the final secure, cost-optimized blueprint...")
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
        final_response = client.models.generate_content(model='gemini-2.5-flash', contents=final_prompt)
        final_report = final_response.text
        
        status.update(label="Architecture blueprint complete!", state="complete", expanded=False)
        return final_report

user_input = st.chat_input("Enter your architectural requirements (e.g., Deploy a scalable E-commerce site)")

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Run pipeline
    final_output = asyncio.run(run_orchestrator(user_input))
    
    if final_output:
        st.success("Final Architecture Ready")
        with st.chat_message("assistant"):
            st.markdown(final_output)
            
        with open("final_architecture.md", "w") as f:
            f.write(final_output)
        
        st.download_button(
            label="Download Final Architecture Markdown",
            data=final_output,
            file_name="final_architecture.md",
            mime="text/markdown"
        )
