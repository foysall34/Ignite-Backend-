import os
import tempfile
import boto3
from celery import shared_task
from django.conf import settings

from openai import OpenAI
from pinecone import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .models import UploadRecord
from .extract_utils import extract_text_from_file     
from .pinecone_utils import store_into_pinecone        
from .elevenlabs_utils import update_elevenlabs_agent  

client = OpenAI(api_key=settings.OPENAI_API_KEY)


@shared_task
def process_s3_file_task(record_id, s3_key):
    print(" Starting file processing task...")
    print(f"Record ID: {record_id}")
    print(f" S3 Key: {s3_key}")

    try:
        record = UploadRecord.objects.get(id=record_id)

        print(" Downloading file from S3...")

        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

   
        ext = os.path.splitext(s3_key)[1] or ".pdf"

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            s3.download_fileobj(settings.AWS_STORAGE_BUCKET_NAME, s3_key, tmp)
            local_path = tmp.name

        print(f" Downloaded to: {local_path}")
        record.status = "processing"
        record.save()

        
        print(" Extracting text from file...")
        text = extract_text_from_file(local_path)
        print(f" Extracted {len(text)} characters")

       
        print("Splitting text into chunks...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120
        )
        chunks = splitter.split_text(text)
        print(f" Total Chunks: {len(chunks)}")

      
        print("Creating embeddings for chunks...")

        embeddings = []
        for i, chunk in enumerate(chunks):
            print(f"→ Embedding chunk {i+1}/{len(chunks)}")

            res = client.embeddings.create(
                model="text-embedding-3-small",
                input=chunk
            )

            embeddings.append({
                "text": chunk,
                "embedding": res.data[0].embedding
            })

        print("Embedding completed.")

        print(" Uploading embeddings to Pinecone...")

        if len(embeddings) == 0:
            print(" No embeddings to store. Skipping Pinecone upload.")
        else:
            store_into_pinecone(embeddings)
            print("Pinecone store SUCCESS ")

  
        print(" Updating ElevenLabs Knowledge Base...")

        if len(text.strip()) == 0:
            print(" No text found. Skipping ElevenLabs KB update.")
        else:
            print("Updating ElevenLabs agent with text chunk...=================")
            el_res = update_elevenlabs_agent(text)
            print(" ElevenLabs response:", el_res.status_code)

            if el_res.status_code == 200:
                print(" ElevenLabs KB UPDATE SUCCESS ")
            else:
                print(" ElevenLabs KB UPDATE FAILED")

   
        record.status = "completed"
        record.save()

        print(" Processing completed successfully.")

    except Exception as e:
        print(" ERROR in task:", str(e))
        record.status = "failed"
        record.error_message = str(e)
        record.save()
