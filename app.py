import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tools import tool1_weather, tool2_stock, tool3_general_qa

load_dotenv()

# -----------------------------
# Initialize LLM (replace with active model)
# -----------------------------
llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")  # Update if decommissioned

tools = [tool1_weather, tool2_stock, tool3_general_qa]

# The LangChain agents API changed across releases; try to use `initialize_agent` when available
try:
    from langchain.agents import initialize_agent, AgentType
    AGENT_API = "initialize_agent"
except Exception:
    AGENT_API = None

# If `initialize_agent` is available, use it. Otherwise raise a clear error asking to pin langchain.
if AGENT_API == "initialize_agent":
    agent_executor = initialize_agent(
        llm=llm,
        tools=tools,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )
else:
    raise RuntimeError(
        "The installed 'langchain' package does not expose 'initialize_agent'.\n"
        "Please pin a compatible 'langchain' release in requirements.txt (run pip freeze locally and update requirements.txt),\n"
        "or upgrade langchain in the deployment environment. Example: add a line like 'langchain>=0.1.16' to requirements.txt and redeploy."
    )

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Multi-Tool AI Chatbot", layout="centered")
st.title("🤖 Multi-Tool AI Chatbot")
st.markdown("Ask about weather, stock prices, or general questions!")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))

    with st.spinner("🤔 Thinking..."):
        bot_reply = None
        try:
            # Prefer keyword-style call; fallback to positional if signature differs across versions
            try:
                bot_reply = agent_executor.run(input=user_input, handle_parsing_errors=True)
            except TypeError:
                bot_reply = agent_executor.run(user_input)
        except Exception as e:
            err_msg = str(e)
            # If it's an output parsing error, call the general QA tool directly as a deterministic fallback.
            if 'parsing' in err_msg.lower() or 'output parsing' in err_msg.lower():
                try:
                    fallback = tool3_general_qa(user_input)
                    bot_reply = f"⚠️ Agent parsing error - returning fallback answer:\n\n{fallback}"
                except Exception as ex:
                    bot_reply = f"⚠️ Error during fallback: {str(ex)}"
            else:
                bot_reply = f"⚠️ Error: {err_msg}"

        st.session_state.chat_history.append(("bot", bot_reply))

for role, message in st.session_state.chat_history:
    if role == "user":
        st.chat_message("user").write(message)
    else:
        st.chat_message("assistant").markdown(message.replace("\n", "  \n"))
