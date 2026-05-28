import streamlit as st

from deepseek_simple_chatbot import build_chatbot, get_response


@st.cache_resource
def load_chatbot():
    return build_chatbot()


st.title("DeepSeek RAG Chatbot")

retriever, document_chain, question_answering_chain = load_chatbot()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    st.session_state.chat = [
        {"role": "assistant", "content": "질문을 입력하세요."}
    ]

for message in st.session_state.chat:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("질문을 입력하세요"):
    st.session_state.chat.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    response = get_response(
        prompt,
        st.session_state.messages,
        retriever,
        document_chain,
        question_answering_chain,
    )

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.chat.append({"role": "assistant", "content": response})
