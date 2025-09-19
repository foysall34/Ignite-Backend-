

import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

def load_documents(folder_path: str):

    documents = []
    if not os.path.isdir(folder_path):
        print(f"Warning: Directory '{folder_path}' not found.")
        return documents
    for filename in os.listdir(folder_path):
        path = os.path.join(folder_path, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(path)
        elif filename.endswith(".docx"):
            loader = Docx2txtLoader(path)
        else:
            continue
        documents.extend(loader.load())
    return documents

def chatbot(query: str, folder_path: str = "ignite", index_name: str = "scholarships"):

    documents = load_documents(folder_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings_model
    )
    if splits:
        vectorstore.add_documents(documents=splits)
    search_results = vectorstore.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in search_results])
    prompt = f"""
    You are AI Assistant, a highly intelligent and helpful assistant. For this interaction,
    your knowledge base is the extensive document provided by the user.

    Context:
    {context}

    Question: {query}
    Answer:
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000,
        temperature=0.5
    )
    answer = response.choices[0].message.content.replace("\n", " ").strip()
    return {"response": answer}