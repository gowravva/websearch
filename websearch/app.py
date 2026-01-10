import os
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

from tools import tool1_weather, tool2_stock, tool3_general_search

load_dotenv()

st.set_page_config(page_title="Autonomous Multi-Tool Chatbot")
st.title("🤖 Autonomous Multi-Tool AI Chatbot")

# ---- API KEY (SAFE) ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY missing in .env")
    st.stop()

# ---- LLM ----
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

TOOLS = {
    "weather": tool1_weather,
    "stock": tool2_stock,
    "search": tool3_general_search
}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("Ask about weather, stocks, or anything...")

if user_input:
    st.session_state.chat_history.append(HumanMessage(content=user_input))

    router_prompt = f"""
You are an autonomous tool router.

Tools:
- weather
- stock
- search

Return ONLY JSON:
{{
  "tool": "weather | stock | search",
  "input": "rewritten query"
}}

User query:
{user_input}
"""

    try:
        response = llm.invoke(router_prompt).content
        response = response[response.find("{"):response.rfind("}")+1]
        decision = json.loads(response)

        tool = decision["tool"]
        query = decision.get("input", user_input)

        reply = TOOLS[tool].invoke(query)

    except Exception as e:
        reply = f"⚠️ Error: {e}"

    st.session_state.chat_history.append(AIMessage(content=reply))

for msg in st.session_state.chat_history:
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    else:
        st.chat_message("assistant").text(msg.content)
