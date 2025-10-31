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
    



# using celery ------------------------------------
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
        # 1) upload to s3
        try:
            s3_key = upload_to_s3(file_obj)
        except Exception as e:
            return Response({"error": "S3 upload failed", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2) create UploadRecord
        record = UploadRecord.objects.create(
            role=role.lower(),
            original_name=file_obj.name,
            s3_key=s3_key,
            status="pending"
        )

        # 3) trigger celery task asynchronously
        process_s3_file_task.delay(record.id, s3_key)

        serializer = UploadRecordSerializer(record)
        return Response({
            "message": "File uploaded to S3 and queued for processing",
            "record": serializer.data
        }, status=status.HTTP_201_CREATED)


# Optional: check status
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
    POST /api/query/
    Body: { "query": "your question" }
    """

    def post(self, request):
        query = request.data.get("query")
        if not query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1️⃣ Load Pinecone vectorstore
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY
            )
            vectorstore = PineconeVectorStore.from_existing_index(
                index_name=settings.PINECONE_INDEX_NAME,
                embedding=embeddings
            )

            # 2️⃣ Retrieve top-3 most similar chunks
            results = vectorstore.similarity_search(query, k=3)
            context = "\n\n".join([r.page_content for r in results])

            # 3️⃣ Generate AI answer from OpenAI
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
