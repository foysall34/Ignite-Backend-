from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .utils import upload_to_s3

class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if "file" not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES["file"]
        file_data = upload_to_s3(file_obj)

        return Response({
            "message": "File uploaded successfully",
            "file_key": file_data["key"],
            "file_url": file_data["url"],  
        }, status=status.HTTP_201_CREATED)
