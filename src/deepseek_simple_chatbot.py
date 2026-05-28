from pathlib import Path
import logging
import os

from dotenv import load_dotenv
from chromadb.config import Settings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_chatbot():
    load_dotenv()
    logging.getLogger("chromadb.telemetry.product.posthog").disabled = True

    llm = ChatOllama(model="deepseek-r1:14b")

    base_dir = Path(__file__).resolve().parent
    persist_directory = base_dir / "chroma_store"
    chroma_settings = Settings(anonymized_telemetry=False)

    embedding = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    if not persist_directory.exists():
        loader = PyPDFLoader(str(base_dir / "../data/OneNYC_2050_Strategic_Plan.pdf의 사본.pdf"))
        data_nyc = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        all_splits = text_splitter.split_documents(data_nyc)

        loader_seoul = PyPDFLoader(str(base_dir / "../data/2040_seoul_plan.pdf의 사본.pdf"))
        data_seoul = loader_seoul.load()
        seoul_splits = text_splitter.split_documents(data_seoul)

        all_splits.extend(seoul_splits)

        vectorstore = Chroma.from_documents(
            documents=all_splits,
            embedding=embedding,
            persist_directory=str(persist_directory),
            client_settings=chroma_settings,
        )
    else:
        vectorstore = Chroma(
            persist_directory=str(persist_directory),
            embedding_function=embedding,
            client_settings=chroma_settings,
        )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    question_answering_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "사용자의 질문에 아래 context에 기반하여 대답해: \n\n{context}"),
            MessagesPlaceholder(variable_name="message"),
        ]
    )

    document_chain = create_stuff_documents_chain(llm, question_answering_prompt)

    query_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """기존 대화 내용을 참고해서 사용자의 질문을 명확한 한 문장의 질문으로 다시 작성하세요.
대명사(이, 그, 저, 이것, 그것 등)를 쓰지 말고 구체적인 명사를 사용하세요.
답변하지 말고, 다시 작성한 질문만 출력하세요."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{query}"),
        ]
    )

    question_answering_chain = query_prompt | llm | StrOutputParser()

    return retriever, document_chain, question_answering_chain


def get_response(user_input, messages, retriever, document_chain, question_answering_chain):
    augmented_query = question_answering_chain.invoke(
        {"messages": messages, "query": user_input}
    )
    docs = retriever.invoke(augmented_query)

    messages.append(HumanMessage(user_input))

    ai_response = document_chain.invoke(
        {"message": messages, "context": docs}
    )

    messages.append(AIMessage(ai_response))

    return ai_response


if __name__ == "__main__":
    retriever, document_chain, question_answering_chain = build_chatbot()
    messages = []

    while True:
        user_input = input("user: ")
        if user_input == "exit":
            break

        ai_response = get_response(
            user_input,
            messages,
            retriever,
            document_chain,
            question_answering_chain,
        )

        print("AI:" + ai_response)
