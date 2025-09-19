!pip install langchain-pinecone pinecone langchain-community pypdf

# ==========================
# Backend-Friendly AI Chatbot (JSON Output)
# ==========================

import os
import json
from google.colab import userdata
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from openai import OpenAI

# ==========================
# API Keys (stored in Colab secrets)
# ==========================
os.environ["OPENAI_API_KEY"] = userdata.get("OPENAI_API_KEY")
os.environ["PINECONE_API_KEY"] = userdata.get("PINECONE_API_KEY")

# ==========================
# Document Loader Function
# ==========================
def load_documents(folder_path: str):
    documents = []
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

# ==========================
# Chatbot Function
# ==========================
def chatbot(query: str, folder_path: str = "ignite", index_name: str = "scholarships"):
    # 1. Load and split documents
    documents = load_documents(folder_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    # 2. Connect to Pinecone vectorstore
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )

    # 3. Add document chunks if not already added
    if splits:
        vectorstore.add_documents(documents=splits)

    # 4. Retrieve relevant chunks
    search_results = vectorstore.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in search_results])

    # 5. Create OpenAI client
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # 6. Generate response
    prompt = f"""
    You are AI Assistant, a highly intelligent and helpful assistant. For this interaction,
    your knowledge base is the extensive document provided by the user, which covers AI, ML, NLP,
    advanced techniques, AI development lifecycle, Generative AI, LLMs, Ethical AI, Explainable AI,
    Edge AI, and Multimodal AI.

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

    answer = response.choices[0].message.content
    # Clean up formatting (remove \n)
    answer = response.choices[0].message.content.replace("\n", " ").strip()
    # Return in JSON format
    return json.dumps({"response": answer}, ensure_ascii=False, indent=2)



# ==========================
# Example (for testing only)
# ==========================
if __name__ == "__main__":
    test_query = "what is the major NLP preprocessing techniques?"
    output = chatbot(test_query)
    print(output)


