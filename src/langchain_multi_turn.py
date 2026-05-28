from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage,SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4o")

store = {}

def get_session_history(session_id:str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

with_message_history = RunnableWithMessageHistory(llm,get_session_history)

config = {"configurable": {"session_id" :"abc"}}

response = with_message_history.invoke(
    [HumanMessage ]

)
message = [
    SystemMessage("너는 사용자를 도우는 상담사야")

]

while True:
    user_input = input("user: ")
    if user_input == "exit":
        break
    message.append(HumanMessage(user_input))

    ai_response =llm.invoke(message)

    message.append(ai_response)

    print("AI:"+ai_response.content)