import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from tools import tool1_weather, tool2_stock, tool3_general_qa

load_dotenv()

# -----------------------------
# Initialize LLM (replace with active model)
# -----------------------------
llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")  # Update if decommissioned

tools = [tool1_weather, tool2_stock, tool3_general_qa]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder("messages"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

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
        try:
            response = agent_executor.invoke({
                "messages": [HumanMessage(content=user_input)]
            })
            bot_reply = response["output"]
        except Exception as e:
            bot_reply = f"⚠️ Error: {str(e)}"

        st.session_state.chat_history.append(("bot", bot_reply))

for role, message in st.session_state.chat_history:
    if role == "user":
        st.chat_message("user").write(message)
    else:
        st.chat_message("assistant").markdown(message.replace("\n", "  \n"))
