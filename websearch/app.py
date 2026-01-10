import os
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

from tools import tool1_weather, tool2_stock, tool3_general_search

# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- STREAMLIT CONFIG ----------------
st.set_page_config(
    page_title="Autonomous Multi-Tool Chatbot",
    layout="centered"
)

st.title("🤖 Autonomous Multi-Tool AI Chatbot")

# ---------------- API KEY (SAFE) ----------------
GROQ_API_KEY = (
    st.secrets.get("GROQ_API_KEY")
    if "GROQ_API_KEY" in st.secrets
    else os.getenv("GROQ_API_KEY")
)

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found. Add it to secrets.toml or .env")
    st.stop()

# ---------------- LLM ----------------
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

# ---------------- TOOLS REGISTRY ----------------
TOOLS = {
    "weather": tool1_weather,
    "stock": tool2_stock,
    "search": tool3_general_search
}

# ---------------- SESSION STATE ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------- HELPER FUNCTION ----------------
def display_message(content: str, is_user: bool = False):
    """
    Display chat message in Streamlit.
    Uses .text() for assistant to avoid Markdown enlarging font.
    """
    if is_user:
        st.chat_message("user").write(content)
    else:
        st.chat_message("assistant").text(content)  # plain text, no Markdown formatting

# ---------------- CHAT INPUT ----------------
user_input = st.chat_input("Ask about weather, stocks, or anything...")

if user_input:
    # Add user message
    st.session_state.chat_history.append(HumanMessage(content=user_input))

    with st.spinner("Thinking..."):
        # Router prompt to decide which tool to call
        router_prompt = f"""
You are an autonomous tool router.

Available tools:
- weather → weather related questions
- stock → stock price or market questions
- search → general knowledge or explanations

Respond ONLY in valid JSON.
No markdown. No explanation.

Format:
{{
  "tool": "weather | stock | search",
  "input": "rewritten user query"
}}

User question:
{user_input}
"""

        try:
            # Get LLM router decision
            response = llm.invoke(router_prompt).content.strip()

            # Clean JSON in case LLM adds extra text
            start = response.find("{")
            end = response.rfind("}") + 1
            response = response[start:end]

            decision = json.loads(response)
            tool_name = decision.get("tool")
            tool_input = decision.get("input", user_input)

            # Call the selected tool
            if tool_name in TOOLS:
                reply = TOOLS[tool_name].invoke(tool_input)
            else:
                reply = "❌ Router selected an unknown tool."

        except Exception as e:
            reply = f"⚠️ Routing error: {e}"

    # Add assistant message
    st.session_state.chat_history.append(AIMessage(content=reply))

# ---------------- DISPLAY CHAT ----------------
for msg in st.session_state.chat_history:
    if isinstance(msg, HumanMessage):
        display_message(msg.content, is_user=True)
    else:
        display_message(msg.content, is_user=False)
