import os
import tempfile
import boto3
from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from PIL import Image
import pytesseract
from moviepy.editor import VideoFileClip

CHUNK_SIZE = 400
CHUNK_OVERLAP = 200

def extract_documents_from_file(file_path, file_key):
    docs = []
    lower = file_key.lower()
    if lower.endswith(".pdf"):
        docs.extend(PyPDFLoader(file_path).load())
    elif lower.endswith(".docx"):
        docs.extend(Docx2txtLoader(file_path).load())
    elif lower.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
        text = pytesseract.image_to_string(Image.open(file_path))
        docs.append(Document(page_content=text, metadata={"source": file_key}))
    elif lower.endswith((".mp3", ".wav", ".m4a")):
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        with open(file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
        docs.append(Document(page_content=transcript.text, metadata={"source": file_key}))
    elif lower.endswith((".mp4", ".mkv", ".avi", ".mov")):
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        video = VideoFileClip(file_path)
        tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        video.audio.write_audiofile(tmp_audio.name, verbose=False, logger=None)
        video.close()
        with open(tmp_audio.name, "rb") as f:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
        docs.append(Document(page_content=transcript.text, metadata={"source": file_key}))
    else:
 
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                docs.append(Document(page_content=f.read(), metadata={"source": file_key}))
        except Exception:
            pass

    return docs

def process_file_from_s3(file_key):
    """Download private file from S3, extract text, split, embed, upload to Pinecone"""
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    s3.download_file(settings.AWS_STORAGE_BUCKET_NAME, file_key, tmp_file.name)
    file_path = tmp_file.name


    docs = extract_documents_from_file(file_path, file_key)
    if not docs:
        return {"success": False, "message": "No documents extracted"}

 
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    if settings.PINECONE_INDEX_NAME not in [i["name"] for i in pc.list_indexes()]:
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=1536,
            metric="cosine",
        )

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY)
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings
    )
    vectorstore.add_documents(chunks)

    return {"success": True, "chunks": len(chunks)}



