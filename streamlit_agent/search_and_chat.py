from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from langchain.tools import StructuredTool
from langchain.pydantic_v1 import BaseModel, Field
import os
import requests
import streamlit as st
from dotenv import load_dotenv
from default_prompt import DEFAULT_PROMPT
from langchain.schema import SystemMessage, HumanMessage


load_dotenv()

azure_ew_api_key = os.getenv("OPENAI_API_KEY")
azure_ew_endpoint = os.getenv("AZURE_ENDPOINT")
azure_search_api = os.getenv("AZURE_SEARCH_API")
azure_search_key = os.getenv("AZURE_SEARCH_KEY")
# azure_search_index = os.getenv("AZURE_SEARCH_INDEX")
# azure_search_index = 'vector-1741772887139'
azure_search_index = 'vector-14-22'
azure_openai_api_version = os.getenv("API_VERSION")

st.set_page_config(
    page_title="EW PBI Access Assistant", page_icon="./streamlit_agent/icons/ew_icon.jpeg"
)

col1, col2 = st.columns([1, 5])  # Adjust proportions

with col1:
    st.image("./streamlit_agent/icons/ew_icon.jpeg", width=80)

with col2:
    st.title("Eurowag PBI Access assistant")


def search_azure_ai(query: str) -> str:
    url = f"{azure_search_api}/indexes/{azure_search_index}/docs"

    headers = {
        "Content-Type": "application/json",
        "api-key": azure_search_key,
    }

    params = {
        "api-version": "2024-07-01",
        "search": query,
        "top": 10,
        "minimumScore": 0.8,
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        results = response.json()
        docs = [doc for doc in results.values() if type(doc) == list][0]
        for i in docs:
            i.pop("text_vector")
        return (
            # "\n".join(docs)
            docs
            if docs
            else "Report not found "
        )
    else:
        return 
        # return "Search failed. Check API key, index name, or Azure configuration."


class SearchQueryInput(BaseModel):
    query: str = Field(description="Query to search in Azure AI Search")


azure_search_tool = StructuredTool.from_function(
    name="azure_ai_search",
    func=search_azure_ai,
    description="Use this tool to search Azure AI Search for relevant documents.",
    args_schema=SearchQueryInput,
)

msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=msgs, return_messages=True, memory_key="chat_history", output_key="output"
)
if len(msgs.messages) == 0 or st.sidebar.button("Reset chat history"):
    msgs.clear()
    msgs.add_ai_message("How can I help you today?")
    st.session_state.steps = {}

avatars = {"human": "user", "ai": "assistant"}
for idx, msg in enumerate(msgs.messages):
    with st.chat_message(avatars[msg.type]):
        # Render intermediate steps if any were saved
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)

prompt = st.chat_input(placeholder="write your message here")
if prompt:
    # prompt = DEFAULT_PROMPT + prompt
    # prompt = st.chat_input(placeholder="write your message here")

    st.chat_message("user").write(prompt)

    llm = AzureChatOpenAI(
        azure_endpoint=azure_ew_endpoint,
        model_name="gpt-4o-mini",
        api_key=azure_ew_api_key,
        streaming=True,
        api_version="2023-05-15",
        azure_deployment="gpt-4o-mini",
        temperature=0.1,
    )

    system_message = SystemMessage(content=DEFAULT_PROMPT)

    # Construct full prompt: Include system message + user input
    messages = [system_message] + [HumanMessage(content=prompt)]
    tools = [azure_search_tool]
    chat_agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools)
    executor = AgentExecutor.from_agent_and_tools(
        agent=chat_agent,
        tools=tools,
        memory=memory,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        cfg = RunnableConfig()
        cfg["callbacks"] = [st_cb]
        response = executor.invoke(prompt, cfg)
        st.write(response["output"])
        st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]