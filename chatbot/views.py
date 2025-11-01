from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .utils import upload_to_s3

class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        role = request.data.get("role")
        if not role:
            return Response({"error": "Role is required"}, status=status.HTTP_400_BAD_REQUEST)

        if role.lower() != "admin":
            return Response({"error": "You are not authorized to upload files"}, status=status.HTTP_403_FORBIDDEN)
        if "file" not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)


        file_obj = request.FILES["file"]
        file_data = upload_to_s3(file_obj)
 
        return Response({
            "message": "File uploaded successfully",
            "file_key": file_data["key"],
            "file_url": file_data["url"],
        },  status=status.HTTP_201_CREATED)
    



# --------------------------------------- using celery ------------------------------------
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .utils_upload import upload_to_s3
from .models import UploadRecord
from .tasks import process_s3_file_task
from .serializers import UploadRecordSerializer

class FileUploadViewed(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        role = request.data.get("role")
        if not role or role.lower() != "admin":
            return Response({"error": "Only admin can upload"}, status=status.HTTP_403_FORBIDDEN)

        if "file" not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES["file"]

        try:
            s3_key = upload_to_s3(file_obj)
        except Exception as e:
            return Response({"error": "S3 upload failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        record = UploadRecord.objects.create(
            role=role.lower(),
            original_name=file_obj.name,
            s3_key=s3_key,
            status="pending"
        )

        process_s3_file_task.delay(record.id, s3_key)

        serializer = UploadRecordSerializer(record)
        return Response({
            "message": "File uploaded to S3 and queued for processing",
            "record": serializer.data
        }, status=status.HTTP_201_CREATED)



class UploadStatusView(APIView):
    def get(self, request, record_id):
        try:
            rec = UploadRecord.objects.get(id=record_id)
            serializer = UploadRecordSerializer(rec)
            return Response(serializer.data)
        except UploadRecord.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI


class QueryView(APIView):
    """
    Body: { "query": "your question" }
    """

    def post(self, request):
        query = request.data.get("query")
        if not query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
    
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY
            )
            vectorstore = PineconeVectorStore.from_existing_index(
                index_name=settings.PINECONE_INDEX_NAME,
                embedding=embeddings
            )


            results = vectorstore.similarity_search(query, k=3)
            context = "\n\n".join([r.page_content for r in results])

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are SENSES, a spiritual AI companion. "
                            "Respond with warmth, insight, and clarity."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}",
                    },
                ],
                temperature=0.6,
                max_tokens=800,
            )

            answer = response.choices[0].message.content
            return Response({"query": query, "answer": answer}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# voice to voice 

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import tempfile, base64


class VoiceChatElevenView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if "audio" not in request.FILES:
            return Response({"error": "No audio file provided"}, status=status.HTTP_400_BAD_REQUEST)

        voice_id = request.data.get("voice_id", "pNInz6obpgDQGcFmaJgB")  # Adam as default voice


        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        eleven_client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

        try:

            audio_file = request.FILES["audio"]
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
                for chunk in audio_file.chunks():
                    tmp_audio.write(chunk)
                tmp_audio_path = tmp_audio.name

            with open(tmp_audio_path, "rb") as f:
                transcription = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
            user_text = transcription.text.strip()

       
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY
            )
            vectorstore = PineconeVectorStore.from_existing_index(
                index_name=settings.PINECONE_INDEX_NAME,
                embedding=embeddings
            )
            results = vectorstore.similarity_search(user_text, k=3)
            context = "\n\n".join([r.page_content for r in results])

            
            gpt_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are SENSES, a spiritual AI voice companion."},
                    {"role": "user", "content": f"Context:\n{context}\n\nUser said: {user_text}"}
                ],
                temperature=0.7,
            )
            answer_text = gpt_response.choices[0].message.content


            response_stream = eleven_client.text_to_speech.convert(
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                text=answer_text
            )

            audio_bytes = b"".join(chunk for chunk in response_stream)
            voice_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            return Response({
                "user_text": user_text,
                "answer_text": answer_text,
                "voice_id": voice_id,
                "voice_base64": voice_base64
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


